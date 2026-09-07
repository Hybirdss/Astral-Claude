import json
import os
import platform
import shutil
from typing import Annotated

from mcp.server.fastmcp import FastMCP, Image
from pydantic import Field

from . import __version__
from .backend import NativeDesktop, primary_modifier
from .core import DEFAULT_DIMENSION, MAX_DIMENSION, MIN_DIMENSION, Action, Controller

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
        "version": __version__,
        "os": system,
        "session": "wayland" if wayland else os.environ.get("XDG_SESSION_TYPE", "unknown"),
        "display_set": bool(os.environ.get("DISPLAY")),
        "backend": "PyAutoGUI + MSS; primary display only",
        "session_supported": system in {"Windows", "Darwin"}
        or (system == "Linux" and not wayland and bool(os.environ.get("DISPLAY"))),
        "primary_modifier": primary_modifier(system),
        "blender_on_path": bool(shutil.which("blender")),
        "permissions_verified": False,
        "next_step": "Observe to verify capture; a harmless authorized click verifies input.",
    }


@mcp.tool()
def desktop_observe(
    max_dimension: Annotated[
        int, Field(strict=True, ge=MIN_DIMENSION, le=MAX_DIMENSION)
    ] = DEFAULT_DIMENSION,
) -> list:
    """Return a primary-display PNG and observation_id. Inspect the image before acting.

    Coordinates for desktop_act are pixels of this returned image, NOT native screen pixels.
    max_dimension accepts 640..2400; use 2400 for small text. Screenshots returned by
    desktop_act keep this max_dimension. Invalidates previous observations.
    """
    return result(controller.observe(max_dimension))


@mcp.tool()
def desktop_act(observation_id: str, action: Action) -> list:
    """Execute ONE action grounded in the latest observation; return a new PNG and ID.

    action.action: click/move/drag/scroll/key/type_text/paste_text/wait.
    Pointer actions require x,y; drag also end_x,end_y (numbers round to whole pixels).
    scroll moves the pointer to x,y first, then sends signed vertical notches (positive up).
    key presses keys together, e.g. ["ctrl","s"]; on macOS use ["command","s"]. Names that the
    current OS cannot press are rejected instead of being silently dropped.
    type_text is ASCII keystrokes; paste_text supports Unicode via the clipboard, waits
    `duration` seconds (default 0.5) for the app to read it, then restores the previous
    text-only clipboard if it still contains the pasted text. New clipboard content is kept.
    Confirm the focused field first.
    IDs expire after 120s and are single-use. A returned screenshot does not prove success:
    inspect it, wait if needed, and verify saved artifacts. This is not a sandbox or focus lock.
    """
    return result(controller.act(observation_id, action))
