import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ImageContent, TextContent

from astral_claude import server
from astral_claude.core import Controller

from .test_core import FakeDesktop


def test_observe_returns_actual_mcp_image_content(monkeypatch):
    monkeypatch.setattr(server, "controller", Controller(FakeDesktop))
    blocks = asyncio.run(server.mcp.call_tool("desktop_observe", {}))
    assert any(
        isinstance(block, ImageContent) and block.mimeType == "image/png" for block in blocks
    )
    metadata = json.loads(next(b.text for b in blocks if isinstance(b, TextContent)))
    assert metadata["image_size"] == [1600, 900]


def test_stdio_initialization_discovery_status_and_errors():
    async def run():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "astral_claude", "serve"]
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert {t.name for t in listed.tools} == {
                    "desktop_status",
                    "desktop_observe",
                    "desktop_act",
                }
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
