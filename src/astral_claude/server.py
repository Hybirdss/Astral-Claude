import json
import os
import platform
import shutil

from mcp.server.fastmcp import FastMCP, Image

from .backend import NativeDesktop
from .core import Action, Controller

mcp = FastMCP("Astral-Claude")
controller = Controller(NativeDesktop)


def result(obs):
    return [json.dumps(obs.metadata()), Image(data=obs.png, format="png")]


@mcp.tool()
def desktop_status() -> dict:
    """Report OS/session prerequisites without taking a screenshot or moving the mouse."""
    system = platform.system()
    wayland = (
        bool(os.environ.get("WAYLAND_DISPLAY")) or os.environ.get("XDG_SESSION_TYPE") == "wayland"
    )
    return {
        "os": system,
        "session": "wayland" if wayland else os.environ.get("XDG_SESSION_TYPE", "unknown"),
        "display_set": bool(os.environ.get("DISPLAY")),
        "backend": "PyAutoGUI + MSS; primary display only",
        "session_supported": system in {"Windows", "Darwin"}
        or (system == "Linux" and not wayland and bool(os.environ.get("DISPLAY"))),
        "blender_on_path": bool(shutil.which("blender")),
        "permissions_verified": False,
        "next_step": "Observe to verify capture; a harmless authorized click verifies input.",
    }


@mcp.tool()
def desktop_observe(max_dimension: int = 1600) -> list:
    """Return a primary-display PNG and observation_id. Inspect the image before acting.

    Coordinates for desktop_act are pixels of this returned image, NOT native screen pixels.
    max_dimension accepts 640..2400; use 2400 for small text. Invalidates previous observations.
    """
    return result(controller.observe(max_dimension))


@mcp.tool()
def desktop_act(observation_id: str, action: Action) -> list:
    """Execute ONE action grounded in the latest observation; return a new PNG and ID.

    action.action: click/move/drag/scroll/key/type_text/paste_text/wait.
    Pointer actions require x,y; drag also end_x,end_y. Scroll amount is signed vertical
    notches (positive up). key uses keys=["ctrl","s"] or ["command","s"] on macOS.
    type_text is ASCII; paste_text supports Unicode but temporarily replaces the clipboard
    and restores text only (rich clipboard formats are lost). Confirm focused field first.
    IDs expire after 120s and are single-use. A returned screenshot does not prove success:
    inspect it, wait if needed, and verify saved artifacts. This is not a sandbox or focus lock.
    """
    return result(controller.act(observation_id, action))
