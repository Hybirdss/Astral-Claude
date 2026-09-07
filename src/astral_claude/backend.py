"""Lazy desktop dependencies: importing the package never captures a screen."""

import os
import platform
import time

from PIL import Image


class DesktopUnavailable(RuntimeError):
    pass


class NativeDesktop:
    def __init__(self):
        system = platform.system()
        if system == "Linux":
            if os.environ.get("WAYLAND_DISPLAY") or os.environ.get("XDG_SESSION_TYPE") == "wayland":
                raise DesktopUnavailable(
                    "Native Wayland is not supported by this backend. Use a real X11 session "
                    "or a separate Xvfb desktop; do not point it at XWayland on your live desktop. "
                    "See docs/platforms.md."
                )
            if not os.environ.get("DISPLAY"):
                raise DesktopUnavailable("No DISPLAY. Start an X11 desktop or Xvfb first.")
        if system == "Windows":
            import ctypes

            # Must happen before screenshot/input libraries establish their coordinate space.
            try:
                ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            except (AttributeError, OSError):
                ctypes.windll.user32.SetProcessDPIAware()
        try:
            import mss
            import pyautogui

            self.pg = pyautogui
            self.mss = mss
            self.pg.FAILSAFE = True
            self.pg.PAUSE = 0.12
        except Exception as exc:
            raise DesktopUnavailable(f"Desktop initialization failed: {exc}") from exc

    def size(self):
        return tuple(self.pg.size())

    def capture(self):
        # Capture only the display anchored at the input coordinate origin.
        with self.mss.mss() as screen:
            primary = next(
                (m for m in screen.monitors[1:] if m["left"] == 0 and m["top"] == 0), None
            )
            if primary is None:
                raise DesktopUnavailable("Cannot identify the primary display at (0, 0).")
            shot = screen.grab(primary)
            return Image.frombytes("RGB", shot.size, shot.rgb)

    def execute(self, action):
        kind = action["action"]
        if kind == "click":
            self.pg.click(
                action["x"],
                action["y"],
                clicks=action["clicks"],
                interval=0.12,
                button=action["button"],
            )
        elif kind == "move":
            self.pg.moveTo(action["x"], action["y"], duration=0.2)
        elif kind == "drag":
            self.pg.moveTo(action["x"], action["y"])
            self.pg.dragTo(
                action["end_x"],
                action["end_y"],
                duration=action["duration"],
                button=action["button"],
            )
        elif kind == "scroll":
            self.pg.moveTo(action["x"], action["y"])
            self.pg.scroll(action["amount"])
        elif kind == "key":
            keys = action["keys"]
            if any(key not in self.pg.KEYBOARD_KEYS for key in keys):
                raise ValueError("Unknown key; use PyAutoGUI key names, e.g. ctrl, command, enter.")
            self.pg.hotkey(*keys)
        elif kind == "type_text":
            self.pg.write(action["text"], interval=0.01)
        elif kind == "paste_text":
            import pyperclip

            previous = pyperclip.paste()
            try:
                pyperclip.copy(action["text"])
                self.pg.hotkey("command" if platform.system() == "Darwin" else "ctrl", "v")
                time.sleep(0.4)
            finally:
                pyperclip.copy(previous)
        elif kind == "wait":
            time.sleep(action["duration"])
