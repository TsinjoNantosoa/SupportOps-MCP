from __future__ import annotations

import os
import sys

import pytest
from mcp import Client, StdioServerParameters

from supportops.servers import knowledge_server, ticketing_server
from supportops.services.ticket_service import TicketService


@pytest.mark.asyncio
async def test_ticketing_protocol_discovery_call_and_error(db, monkeypatch) -> None:
    monkeypatch.setattr(ticketing_server, "service", TicketService(db))
    async with Client(ticketing_server.mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        assert names == {"list_tickets", "get_ticket", "search_tickets", "prepare_ticket_update"}
        get_schema = next(tool.input_schema for tool in tools.tools if tool.name == "get_ticket")
        assert "ticket_id" in get_schema["required"]
        result = await client.call_tool("get_ticket", {"ticket_id": "INC-1042"})
        assert result.structured_content["ticket_id"] == "INC-1042"
        missing = await client.call_tool("get_ticket", {"ticket_id": "INC-9999"})
        assert missing.is_error is True


@pytest.mark.asyncio
async def test_knowledge_protocol_tools_and_resource() -> None:
    async with Client(knowledge_server.mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools.tools} == {"search_knowledge", "get_procedure"}
        templates = await client.list_resource_templates()
        assert any(
            "procedure_id" in str(item.uri_template) for item in templates.resource_templates
        )
        result = await client.read_resource("supportops://knowledge/dns-diagnostics")
        assert "# DNS Diagnostics" in result.contents[0].text


@pytest.mark.asyncio
async def test_real_stdio_subprocess(tmp_path) -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "supportops.servers.ticketing_server"],
        env={
            "SUPPORTOPS_DB_PATH": str(tmp_path / "stdio.db"),
            "SUPPORTOPS_SESSION_ID": "stdio-test",
            "SUPPORTOPS_USER": "pytest",
            "PYTHONPATH": os.pathsep.join(
                [str(ticketing_server.settings.root / "src"), os.getenv("PYTHONPATH", "")]
            ),
        },
    )
    async with Client(params, read_timeout_seconds=30) as client:
        tools = await client.list_tools()
        assert "get_ticket" in {tool.name for tool in tools.tools}
        result = await client.call_tool("get_ticket", {"ticket_id": "INC-1042"})
        assert result.structured_content["status"] == "OPEN"
