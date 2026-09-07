"""Real input/capture test. Run ONLY in an isolated Xvfb display; not collected by pytest."""

import asyncio
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image


async def main():
    if os.environ.get("ASTRAL_TEST_DESKTOP") != "1":
        raise SystemExit("Set ASTRAL_TEST_DESKTOP=1 only inside an isolated Xvfb session.")
    with tempfile.TemporaryDirectory(prefix="astral-smoke-") as temporary:
        root = Path(temporary)
        ready, saved = root / "ready.json", root / "saved.txt"
        script = r"""
import json, sys, tkinter as tk
from pathlib import Path
root = tk.Tk()
root.geometry("600x350+100+100")
root.title("Astral scratch target")
entry = tk.Entry(root, font=("Arial", 18))
entry.pack(padx=30, pady=30, fill="x")
def save():
    Path(sys.argv[2]).write_text(entry.get(), encoding="utf-8")
button = tk.Button(root, text="Save scratch text", command=save)
button.pack(pady=20)
root.update()
points = {name: [widget.winfo_rootx()+widget.winfo_width()//2,
                  widget.winfo_rooty()+widget.winfo_height()//2]
          for name, widget in [("entry", entry), ("save", button)]}
Path(sys.argv[1]).write_text(json.dumps(points))
root.mainloop()
"""
        app = subprocess.Popen([sys.executable, "-c", script, str(ready), str(saved)])
        try:
            for _ in range(100):
                if ready.exists():
                    break
                if app.poll() is not None:
                    raise RuntimeError("Scratch GUI failed to launch")
                time.sleep(0.1)
            points = json.loads(ready.read_text())
            params = StdioServerParameters(
                command=sys.executable, args=["-m", "astral_claude", "serve"], env=dict(os.environ)
            )
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()

                    async def call(name, arguments):
                        import base64

                        response = await session.call_tool(name, arguments)
                        assert not response.isError, response
                        meta = json.loads(
                            next(b.text for b in response.content if b.type == "text")
                        )
                        encoded = next(b.data for b in response.content if b.type == "image")
                        frame = Image.open(io.BytesIO(base64.b64decode(encoded)))
                        assert frame.size == tuple(meta["image_size"])
                        # Non-antialiased Tk on Xvfb may legitimately use only a few colors.
                        assert len(frame.getcolors(maxcolors=1_000_000)) > 2
                        return meta

                    meta = await call("desktop_observe", {"max_dimension": 800})

                    async def act(action):
                        nonlocal meta
                        meta = await call(
                            "desktop_act",
                            {"observation_id": meta["observation_id"], "action": action},
                        )

                    def coordinates(name):
                        x, y = points[name]
                        iw, ih = meta["image_size"]
                        dw, dh = meta["desktop_size"]
                        return {"x": round(x * iw / dw), "y": round(y * ih / dh)}

                    await act({"action": "click", **coordinates("entry")})
                    await act({"action": "type_text", "text": "Astral desktop works"})
                    await act({"action": "click", **coordinates("save")})
                    for _ in range(50):
                        if saved.exists():
                            break
                        await asyncio.sleep(0.1)
                    assert saved.read_text() == "Astral desktop works"
                    print(
                        "PASS: real MCP PNG, scaled click, text entry, button click, saved content"
                    )
        finally:
            app.terminate()
            app.wait(timeout=10)


if __name__ == "__main__":
    asyncio.run(main())
