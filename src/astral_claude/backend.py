"""Lazy desktop dependencies: importing the package never captures a screen."""

import os
import platform
import time
from contextlib import contextmanager

from PIL import Image


class DesktopUnavailable(RuntimeError):
    pass


def primary_modifier(system=None):
    """The modifier that ordinary app shortcuts use on this OS: command on macOS, ctrl elsewhere."""
    return "command" if (system or platform.system()) == "Darwin" else "ctrl"


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
        self.system = system

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

    def available_keys(self):
        """Key names that this OS backend can actually press.

        PyAutoGUI's KEYBOARD_KEYS is a cross-platform list; the platform module's mapping is
        what keyDown consults, and it silently ignores names it lacks (e.g. 'command' on X11).
        """
        mapping = getattr(getattr(self.pg, "platformModule", None), "keyboardMapping", None)
        if not isinstance(mapping, dict):
            return set(self.pg.KEYBOARD_KEYS)
        # macOS uses hardware keycode 0 for A; X11 uses 0 for an unmapped key.
        return {
            name
            for name, code in mapping.items()
            if code is not None and (code != 0 or self.system == "Darwin")
        }

    @contextmanager
    def release_on_error(self, *, keys=(), button=None):
        """Release attempted input after failure, including a corner fail-safe abort."""
        try:
            yield
        except BaseException as exc:
            # Public keyUp/mouseUp also run the fail-safe and cannot release at a corner.
            # Only cleanup uses the platform primitives; FAILSAFE stays enabled.
            for key in reversed(keys):
                try:
                    self.pg.platformModule._keyUp(key)
                except Exception as cleanup_error:
                    exc.add_note(f"Could not release key {key!r}: {cleanup_error}")
            if button is not None:
                try:
                    x, y = self.pg.position()
                    self.pg.platformModule._mouseUp(x, y, button)
                except Exception as cleanup_error:
                    exc.add_note(f"Could not release mouse button {button!r}: {cleanup_error}")
            raise

    def hotkey(self, keys):
        keys = self.normalize_keys(keys)
        with self.release_on_error(keys=keys):
            self.pg.hotkey(*keys)

    def normalize_keys(self, keys):
        available = self.available_keys()
        normalized = []
        for key in keys:
            name = key.lower() if len(key) > 1 else key
            if name not in available:
                raise ValueError(
                    f"Key {key!r} is not available on {self.system}; the primary shortcut "
                    f"modifier here is {primary_modifier(self.system)!r}. Use PyAutoGUI key "
                    "names such as ctrl, alt, shift, win, command, option, enter, esc, tab."
                )
            normalized.append(name)
        return normalized

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
            with self.release_on_error(button=action["button"]):
                self.pg.dragTo(
                    action["end_x"],
                    action["end_y"],
                    duration=action["duration"],
                    button=action["button"],
                )
        elif kind == "scroll":
            # The pointer moves first so the wheel event reaches the widget under x, y.
            self.pg.moveTo(action["x"], action["y"])
            self.pg.scroll(action["amount"])
        elif kind == "key":
            self.hotkey(action["keys"])
        elif kind == "type_text":
            self.pg.write(action["text"], interval=0.01)
        elif kind == "paste_text":
            self.paste(action["text"], action["duration"])
        elif kind == "wait":
            time.sleep(action["duration"])
        else:
            raise ValueError(f"Unknown desktop action: {kind!r}")

    def paste(self, text, settle_seconds):
        import pyperclip

        keys = self.normalize_keys([primary_modifier(self.system), "v"])
        try:
            previous = pyperclip.paste()
        except pyperclip.PyperclipException as exc:
            raise DesktopUnavailable(
                f"Clipboard unavailable for paste_text: {exc}. On X11 install xclip or xsel."
            ) from exc
        try:
            pyperclip.copy(text)
            self.hotkey(keys)
            # Give the focused app time to read the clipboard before it is restored.
            time.sleep(settle_seconds)
        except BaseException as exc:
            try:
                if pyperclip.paste() == text:
                    pyperclip.copy(previous)
            except Exception as cleanup_error:
                exc.add_note(f"Could not restore clipboard: {cleanup_error}")
            raise
        else:
            # Preserve text copied by the user or the application while paste settled.
            if pyperclip.paste() == text:
                pyperclip.copy(previous)
