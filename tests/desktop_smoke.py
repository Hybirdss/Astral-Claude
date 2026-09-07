"""Real input/capture test. Run ONLY in an isolated Xvfb display; not collected by pytest.

Drives every desktop_act action against a Tk scratch window through a separate MCP server
process, then checks the state the window saved. Known widget geometry tests execution and
coordinate mapping; it does not measure a model's visual reasoning.
"""

import asyncio
import base64
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

TARGET = r"""
import json, sys, tkinter as tk
from pathlib import Path

root = tk.Tk()
root.geometry("640x520+80+60")
root.title("Astral scratch target")
entry = tk.Entry(root, font=("Arial", 18))
entry.pack(padx=30, pady=(30, 10), fill="x")
scale = tk.Scale(root, from_=0, to=100, orient="horizontal", length=420, showvalue=0)
scale.pack(pady=10)
text = tk.Text(root, height=8, font=("Arial", 12))
text.insert("1.0", "\n".join(f"line {i}" for i in range(1, 301)))
text.pack(padx=30, pady=10, fill="x")


def save():
    state = {"entry": entry.get(), "scale": scale.get(), "text_top": text.yview()[0]}
    Path(sys.argv[2]).write_text(json.dumps(state), encoding="utf-8")


button = tk.Button(root, text="Save scratch state", command=save)
button.pack(pady=15)
root.update()


def center(widget):
    return [widget.winfo_rootx() + widget.winfo_width() // 2,
            widget.winfo_rooty() + widget.winfo_height() // 2]


points = {"entry": center(entry), "text": center(text), "save": center(button)}
for value in (0, 80):
    x, y = scale.coords(value)
    points[f"scale_{value}"] = [scale.winfo_rootx() + x, scale.winfo_rooty() + y]
Path(sys.argv[1]).write_text(json.dumps(points))
root.mainloop()
"""


async def main():
    if os.environ.get("ASTRAL_TEST_DESKTOP") != "1":
        raise SystemExit("Set ASTRAL_TEST_DESKTOP=1 only inside an isolated Xvfb session.")
    with tempfile.TemporaryDirectory(prefix="astral-smoke-") as temporary:
        root = Path(temporary)
        ready, saved = root / "ready.json", root / "saved.json"
        app = subprocess.Popen([sys.executable, "-c", TARGET, str(ready), str(saved)])
        try:
            for _ in range(100):
                if ready.exists():
                    break
                if app.poll() is not None:
                    raise RuntimeError("Scratch GUI failed to launch")
                time.sleep(0.1)
            points = json.loads(ready.read_text())
            env = {**os.environ, "ASTRAL_CLAUDE_LOCK_DIR": str(root / "locks")}
            params = StdioServerParameters(
                command=sys.executable, args=["-m", "astral_claude", "serve"], env=env
            )
            async with (
                stdio_client(params) as (reader, writer),
                ClientSession(reader, writer) as session,
            ):
                await session.initialize()
                status = await session.call_tool("desktop_status", {})
                assert json.loads(status.content[0].text)["session_supported"], status

                async def call(name, arguments):
                    response = await session.call_tool(name, arguments)
                    assert not response.isError, response
                    meta = json.loads(next(b.text for b in response.content if b.type == "text"))
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

                def at(name):
                    x, y = points[name]
                    iw, ih = meta["image_size"]
                    dw, dh = meta["desktop_size"]
                    return {"x": round(x * iw / dw), "y": round(y * ih / dh)}

                await act({"action": "click", **at("entry")})
                await act({"action": "type_text", "text": "Astral desktop works"})
                await act({"action": "key", "keys": ["home"]})
                await act({"action": "key", "keys": ["shift", "end"]})
                await act({"action": "key", "keys": ["delete"]})
                await act({"action": "paste_text", "text": "Astral café 안녕", "duration": 0.5})
                assert meta["image_size"][0] == 800, "act should keep the requested resolution"
                end = at("scale_80")
                await act(
                    {
                        "action": "drag",
                        **at("scale_0"),
                        "end_x": end["x"],
                        "end_y": end["y"],
                        "duration": 0.6,
                    }
                )
                await act({"action": "click", **at("text")})
                await act({"action": "scroll", **at("text"), "amount": -5})
                await act({"action": "wait", "duration": 0.2})
                await act({"action": "move", **at("save")})
                await act({"action": "click", **at("save")})
                for _ in range(50):
                    if saved.exists():
                        break
                    await asyncio.sleep(0.1)
                state = json.loads(saved.read_text(encoding="utf-8"))
                assert state["entry"] == "Astral café 안녕", state
                assert 60 <= state["scale"] <= 100, state
                assert state["text_top"] > 0, state
                # Ending a drag at a corner triggers PyAutoGUI's mouseUp fail-safe.
                # Check the X server's actual button state after the resulting tool error.
                from Xlib import X, display

                consumed_id = meta["observation_id"]
                response = await session.call_tool(
                    "desktop_act",
                    {
                        "observation_id": consumed_id,
                        "action": {
                            "action": "drag",
                            "x": 700,
                            "y": 450,
                            "end_x": 0,
                            "end_y": 0,
                            "duration": 0.3,
                        },
                    },
                )
                assert response.isError, response
                assert "fail-safe" in response.content[0].text.lower(), response
                connection = display.Display()
                try:
                    pointer = connection.screen().root.query_pointer()
                    assert not pointer.mask & X.Button1Mask, "Aborted drag left button pressed"
                finally:
                    connection.close()
                response = await session.call_tool(
                    "desktop_act",
                    {"observation_id": consumed_id, "action": {"action": "wait", "duration": 0.1}},
                )
                assert response.isError and "stale" in response.content[0].text, response
                print(
                    "PASS: real MCP PNGs; click, type_text, key, paste_text, drag, scroll, "
                    "wait, move verified through saved widget state; fail-safe drag releases "
                    "the mouse button and consumes the observation"
                )
        finally:
            app.terminate()
            app.wait(timeout=10)


if __name__ == "__main__":
    asyncio.run(main())
