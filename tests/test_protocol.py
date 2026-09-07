import asyncio
import json
import subprocess
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ImageContent, TextContent

from astral_claude import __version__, server
from astral_claude.core import Controller

from .test_core import FakeDesktop


def server_env(tmp_path):
    # The SDK's default environment omits DISPLAY, so the lock namespace is "native".
    # An isolated lock directory keeps tests independent of a real server on this machine.
    return {**get_default_environment(), "ASTRAL_CLAUDE_LOCK_DIR": str(tmp_path)}


def test_observe_returns_actual_mcp_image_content(monkeypatch):
    monkeypatch.setattr(server, "controller", Controller(FakeDesktop))
    blocks = asyncio.run(server.mcp.call_tool("desktop_observe", {}))
    assert any(
        isinstance(block, ImageContent) and block.mimeType == "image/png" for block in blocks
    )
    metadata = json.loads(next(b.text for b in blocks if isinstance(b, TextContent)))
    assert metadata["image_size"] == [1600, 900]


def test_act_accepts_numeric_coordinates_through_the_tool_layer(monkeypatch):
    monkeypatch.setattr(server, "controller", Controller(FakeDesktop))

    async def run():
        blocks = await server.mcp.call_tool("desktop_observe", {"max_dimension": 800})
        observation = json.loads(blocks[0].text)["observation_id"]
        blocks = await server.mcp.call_tool(
            "desktop_act",
            {"observation_id": observation, "action": {"action": "click", "x": 400.0, "y": 225.0}},
        )
        return json.loads(blocks[0].text)

    metadata = asyncio.run(run())
    assert metadata["image_size"] == [800, 450]
    assert server.controller.backend.actions[0]["x"] == 960


def test_status_reports_version_and_shortcut_modifier():
    status = server.desktop_status()
    assert status["version"] == __version__
    assert status["primary_modifier"] in {"ctrl", "command"}
    assert status["permissions_verified"] is False


def test_stdio_initialization_discovery_status_and_errors(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "astral_claude", "serve"], env=server_env(tmp_path)
        )
        async with (
            stdio_client(params) as (reader, writer),
            ClientSession(reader, writer) as session,
        ):
            await session.initialize()
            listed = await session.list_tools()
            assert {t.name for t in listed.tools} == {
                "desktop_status",
                "desktop_observe",
                "desktop_act",
            }
            act = next(t for t in listed.tools if t.name == "desktop_act")
            assert "scroll" in act.description
            response = await session.call_tool("desktop_status", {})
            assert not response.isError
            data = json.loads(response.content[0].text)
            assert data["permissions_verified"] is False
            response = await session.call_tool(
                "desktop_act",
                {"observation_id": "made-up", "action": {"action": "key", "keys": ["enter"]}},
            )
            assert response.isError
            assert "stale" in response.content[0].text

    asyncio.run(run())


@pytest.mark.parametrize("displays", [(None, None), (":98.0", ":98")])
def test_second_server_for_the_same_display_exits(tmp_path, displays):
    async def run():
        first_env = server_env(tmp_path)
        second_env = server_env(tmp_path)
        if displays[0] is not None:
            first_env["DISPLAY"], second_env["DISPLAY"] = displays
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "astral_claude", "serve"], env=first_env
        )
        async with (
            stdio_client(params) as (reader, writer),
            ClientSession(reader, writer) as session,
        ):
            await session.initialize()
            second = subprocess.run(
                [sys.executable, "-m", "astral_claude", "serve"],
                env=second_env,
                input=b"",
                capture_output=True,
                timeout=60,
            )
            assert second.returncode == 1
            assert b"owns this display" in second.stderr
            assert len(list(tmp_path.glob("desktop-*.lock"))) == 1

    asyncio.run(run())


@pytest.mark.parametrize("dimension", [True, "800", 800.5, 639, 2401])
def test_tool_rejects_invalid_dimensions_without_loading_backend(monkeypatch, dimension):
    controller = Controller(FakeDesktop)
    monkeypatch.setattr(server, "controller", controller)
    with pytest.raises(ToolError, match="max_dimension"):
        asyncio.run(server.mcp.call_tool("desktop_observe", {"max_dimension": dimension}))
    assert controller.backend is None
