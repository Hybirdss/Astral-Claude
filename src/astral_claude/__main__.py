import argparse
import hashlib
import json
import os
from pathlib import Path

from filelock import FileLock, Timeout


def main():
    parser = argparse.ArgumentParser(description="Astral-Claude local desktop MCP server")
    parser.add_argument("command", choices=["serve", "doctor"])
    args = parser.parse_args()
    from .server import desktop_status, mcp

    if args.command == "doctor":
        print(json.dumps(desktop_status(), indent=2))
        return
    # One server per user's display, even across plugin installs or working directories.
    session = os.environ.get("DISPLAY", "native")
    suffix = hashlib.sha256(session.encode()).hexdigest()[:16]
    lock_dir = Path.home() / ".cache" / "astral-claude"
    lock_dir.mkdir(parents=True, exist_ok=True)
    try:
        with FileLock(lock_dir / f"desktop-{suffix}.lock", timeout=0):
            mcp.run(transport="stdio")
    except Timeout:
        parser.exit(
            1, "Another Astral-Claude server owns this display. Close that session first.\n"
        )


if __name__ == "__main__":
    main()
