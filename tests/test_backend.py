"""NativeDesktop behaviour with fake PyAutoGUI/MSS/pyperclip; no real desktop is touched."""

import sys
import types

import pytest

from astral_claude import backend as backend_module
from astral_claude.backend import DesktopUnavailable, NativeDesktop, primary_modifier

MAPPING = {"ctrl": 37, "alt": 64, "shift": 50, "win": 133, "enter": 36, "s": 39, "S": 39, "v": 55}


class FakePyAutoGUI:
    KEYBOARD_KEYS = list(MAPPING) + ["command", "option"]

    def __init__(self, mapping=MAPPING):
        self.calls = []
        self.platformModule = types.SimpleNamespace(keyboardMapping=mapping)

    def __getattr__(self, name):
        if name in {"click", "moveTo", "dragTo", "scroll", "hotkey", "write"}:
            return lambda *args, **kwargs: self.calls.append((name, args, kwargs))
        raise AttributeError(name)


@pytest.fixture
def desktop(monkeypatch):
    native = NativeDesktop.__new__(NativeDesktop)
    native.pg = FakePyAutoGUI()
    native.system = "Linux"
    monkeypatch.setattr(
        backend_module.time, "sleep", lambda s: native.pg.calls.append(("sleep", s))
    )
    return native


def test_pointer_and_text_actions_dispatch_to_pyautogui(desktop):
    desktop.execute({"action": "click", "x": 10, "y": 20, "clicks": 2, "button": "right"})
    desktop.execute({"action": "move", "x": 30, "y": 40})
    desktop.execute(
        {
            "action": "drag",
            "x": 1,
            "y": 2,
            "end_x": 3,
            "end_y": 4,
            "duration": 0.7,
            "button": "left",
        }
    )
    desktop.execute({"action": "scroll", "x": 5, "y": 6, "amount": -3})
    desktop.execute({"action": "type_text", "text": "hi\n"})
    desktop.execute({"action": "wait", "duration": 0.3})
    names = [call[0] for call in desktop.pg.calls]
    assert names == ["click", "moveTo", "moveTo", "dragTo", "moveTo", "scroll", "write", "sleep"]
    assert desktop.pg.calls[0] == (
        "click",
        (10, 20),
        {"clicks": 2, "interval": 0.12, "button": "right"},
    )
    assert desktop.pg.calls[3] == ("dragTo", (3, 4), {"duration": 0.7, "button": "left"})
    assert desktop.pg.calls[5] == ("scroll", (-3,), {})
    assert desktop.pg.calls[-1] == ("sleep", 0.3)


def test_key_names_are_normalized_and_checked_against_the_platform(desktop):
    desktop.execute({"action": "key", "keys": ["Ctrl", "S"]})
    assert desktop.pg.calls == [("hotkey", ("ctrl", "S"), {})]
    with pytest.raises(ValueError, match="'command' is not available on Linux.*'ctrl'"):
        desktop.execute({"action": "key", "keys": ["command", "s"]})
    with pytest.raises(ValueError, match="not available"):
        desktop.execute({"action": "key", "keys": ["option"]})
    assert len(desktop.pg.calls) == 1


def test_key_check_falls_back_to_generic_list_without_platform_mapping(desktop):
    desktop.pg.platformModule = types.SimpleNamespace()
    assert desktop.available_keys() == set(FakePyAutoGUI.KEYBOARD_KEYS)


def test_unmapped_platform_entries_are_not_offered():
    native = NativeDesktop.__new__(NativeDesktop)
    native.system = "Linux"
    native.pg = FakePyAutoGUI({"ctrl": 37, "command": None, "option": 0})
    assert native.available_keys() == {"ctrl"}


def test_paste_replaces_then_restores_text_clipboard(desktop, monkeypatch):
    clipboard = {"value": "previous text", "log": []}
    fake = types.SimpleNamespace(
        PyperclipException=RuntimeError,
        paste=lambda: clipboard["value"],
        copy=lambda text: (clipboard.__setitem__("value", text), clipboard["log"].append(text)),
    )
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    desktop.execute({"action": "paste_text", "text": "café 안녕", "duration": 1.5})
    assert clipboard["log"] == ["café 안녕", "previous text"]
    assert desktop.pg.calls == [("hotkey", ("ctrl", "v"), {}), ("sleep", 1.5)]
    assert clipboard["value"] == "previous text"


def test_paste_uses_command_on_macos(desktop, monkeypatch):
    desktop.system = "Darwin"
    desktop.pg.platformModule.keyboardMapping = {"command": 55, "v": 9}
    fake = types.SimpleNamespace(
        PyperclipException=RuntimeError, paste=lambda: "", copy=lambda t: None
    )
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    desktop.execute({"action": "paste_text", "text": "x", "duration": 0.1})
    assert desktop.pg.calls[0] == ("hotkey", ("command", "v"), {})


def test_missing_clipboard_tool_is_reported_before_any_input(desktop, monkeypatch):
    class Broken(RuntimeError):
        pass

    def paste():
        raise Broken("no xclip")

    fake = types.SimpleNamespace(PyperclipException=Broken, paste=paste, copy=lambda t: None)
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    with pytest.raises(DesktopUnavailable, match="xclip"):
        desktop.execute({"action": "paste_text", "text": "x", "duration": 0.1})
    assert desktop.pg.calls == []


class FakeShot:
    size = (4, 2)
    rgb = bytes(4 * 2 * 3)


class FakeMSS:
    def __init__(self, monitors):
        self.monitors = monitors
        self.grabbed = None

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def grab(self, monitor):
        self.grabbed = monitor
        return FakeShot()


def test_capture_uses_the_display_at_the_input_origin(desktop):
    virtual = {"left": -1920, "top": 0, "width": 3840, "height": 1080}
    secondary = {"left": -1920, "top": 0, "width": 1920, "height": 1080}
    primary = {"left": 0, "top": 0, "width": 1920, "height": 1080}
    desktop.mss = types.SimpleNamespace(mss=FakeMSS([virtual, secondary, primary]))
    image = desktop.capture()
    assert desktop.mss.mss.grabbed is primary
    assert image.size == (4, 2)


def test_capture_without_origin_display_is_rejected(desktop):
    desktop.mss = types.SimpleNamespace(
        mss=FakeMSS([{"left": 0, "top": 0}, {"left": 100, "top": 0}])
    )
    with pytest.raises(DesktopUnavailable, match="primary display"):
        desktop.capture()


def test_linux_session_checks_run_before_desktop_imports(monkeypatch):
    monkeypatch.setattr(backend_module.platform, "system", lambda: "Linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":0")
    with pytest.raises(DesktopUnavailable, match="Wayland"):
        NativeDesktop()
    monkeypatch.delenv("WAYLAND_DISPLAY")
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.delenv("DISPLAY")
    with pytest.raises(DesktopUnavailable, match="No DISPLAY"):
        NativeDesktop()


def test_primary_modifier_per_platform():
    assert primary_modifier("Darwin") == "command"
    assert primary_modifier("Linux") == "ctrl"
    assert primary_modifier("Windows") == "ctrl"


def test_macos_zero_keycode_supports_select_all(desktop):
    desktop.system = "Darwin"
    desktop.pg.platformModule.keyboardMapping = {"a": 0, "command": 55, "missing": None}
    desktop.execute({"action": "key", "keys": ["command", "a"]})
    assert desktop.pg.calls == [("hotkey", ("command", "a"), {})]
    assert "missing" not in desktop.available_keys()


def test_failed_drag_releases_button_without_disabling_failsafe(desktop):
    error = RuntimeError("corner fail-safe")
    desktop.pg.FAILSAFE = True
    desktop.pg.position = lambda: (0, 0)
    releases = []
    desktop.pg.platformModule._mouseUp = lambda *args: releases.append(args)

    def drag(*args, **kwargs):
        raise error

    desktop.pg.dragTo = drag
    with pytest.raises(RuntimeError) as caught:
        desktop.execute(
            {
                "action": "drag",
                "x": 10,
                "y": 20,
                "end_x": 0,
                "end_y": 0,
                "duration": 0.2,
                "button": "left",
            }
        )
    assert caught.value is error
    assert releases == [(0, 0, "left")]
    assert desktop.pg.FAILSAFE is True


def test_failed_hotkey_attempts_all_releases_and_preserves_original_error(desktop):
    error = RuntimeError("key down failed")
    releases = []

    def hotkey(*args):
        raise error

    def release(key):
        releases.append(key)
        if key == "s":
            raise RuntimeError("release failed")

    desktop.pg.hotkey = hotkey
    desktop.pg.platformModule._keyUp = release
    with pytest.raises(RuntimeError) as caught:
        desktop.execute({"action": "key", "keys": ["ctrl", "s"]})
    assert caught.value is error
    assert releases == ["s", "ctrl"]
    assert "release failed" in error.__notes__[0]


def test_paste_preserves_clipboard_changed_during_settle(desktop, monkeypatch):
    clipboard = {"value": "previous"}
    fake = types.SimpleNamespace(
        PyperclipException=RuntimeError,
        paste=lambda: clipboard["value"],
        copy=lambda text: clipboard.__setitem__("value", text),
    )
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    monkeypatch.setattr(backend_module.time, "sleep", lambda _: fake.copy("new user copy"))
    desktop.paste("requested", 0.5)
    assert clipboard["value"] == "new user copy"


def test_paste_failure_restores_clipboard_and_releases_keys(desktop, monkeypatch):
    clipboard = {"value": "previous"}
    fake = types.SimpleNamespace(
        PyperclipException=RuntimeError,
        paste=lambda: clipboard["value"],
        copy=lambda text: clipboard.__setitem__("value", text),
    )
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    releases = []
    desktop.pg.platformModule._keyUp = releases.append

    def hotkey(*args):
        raise RuntimeError("input failed")

    desktop.pg.hotkey = hotkey
    with pytest.raises(RuntimeError, match="input failed"):
        desktop.paste("requested", 0.5)
    assert clipboard["value"] == "previous"
    assert releases == ["v", "ctrl"]


def test_clipboard_restore_failure_does_not_mask_input_failure(desktop, monkeypatch):
    clipboard = {"value": "previous"}

    def copy(text):
        if text == "previous":
            raise RuntimeError("restore failed")
        clipboard["value"] = text

    fake = types.SimpleNamespace(
        PyperclipException=RuntimeError,
        paste=lambda: clipboard["value"],
        copy=copy,
    )
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    desktop.pg.platformModule._keyUp = lambda key: None

    def hotkey(*args):
        raise RuntimeError("input failed")

    desktop.pg.hotkey = hotkey
    with pytest.raises(RuntimeError, match="input failed") as caught:
        desktop.paste("requested", 0.5)
    assert "restore failed" in caught.value.__notes__[0]
