"""Display ownership identities, without importing desktop libraries."""

import pytest

from astral_claude import __main__ as cli


@pytest.mark.parametrize(
    ("display", "expected"),
    [
        (":0", ":0"),
        (":0.0", ":0"),
        (":0.1", ":0"),
        (":1", ":1"),
        ("localhost:10.0", "localhost:10"),
        ("remote:0.0", "remote:0"),
    ],
)
def test_x11_screens_share_the_server_lock(monkeypatch, display, expected):
    monkeypatch.setattr(cli.platform, "system", lambda: "Linux")
    monkeypatch.setenv("DISPLAY", display)
    assert cli.display_session() == expected


@pytest.mark.parametrize("system", ["Windows", "Darwin"])
def test_native_lock_is_independent_of_display_environment(monkeypatch, system):
    monkeypatch.setattr(cli.platform, "system", lambda: system)
    monkeypatch.setenv("DISPLAY", ":99")
    assert cli.display_session() == "native"
