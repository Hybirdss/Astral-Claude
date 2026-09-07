import argparse
import hashlib
import json
import os
import platform
import re
from pathlib import Path

from filelock import FileLock, Timeout

from . import __version__


def lock_directory() -> Path:
    """Per-user lock location; ASTRAL_CLAUDE_LOCK_DIR overrides it for tests and unusual homes."""
    override = os.environ.get("ASTRAL_CLAUDE_LOCK_DIR")
    return Path(override) if override else Path.home() / ".cache" / "astral-claude"


def display_session() -> str:
    """All screens of one X server share input; native backends ignore DISPLAY."""
    if platform.system() != "Linux":
        return "native"
    display = os.environ.get("DISPLAY") or "native"
    return re.sub(r"(:\d+)\.\d+$", r"\1", display)


def main():
    parser = argparse.ArgumentParser(description="Astral-Claude local desktop MCP server")
    parser.add_argument("command", choices=["serve", "doctor"])
    parser.add_argument("--version", action="version", version=f"astral-desktop {__version__}")
    args = parser.parse_args()
    from .server import desktop_status, mcp

    if args.command == "doctor":
        print(json.dumps(desktop_status(), indent=2))
        return
    # One server per user's display, even across plugin installs or working directories.
    session = display_session()
    suffix = hashlib.sha256(session.encode()).hexdigest()[:16]
    lock_dir = lock_directory()
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
