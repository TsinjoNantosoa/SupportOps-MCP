from __future__ import annotations

import os
import sys
from typing import Any

from mcp import Client, StdioServerParameters

from supportops.config import Settings


def server_parameters(module: str, settings: Settings) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", module],
        env={
            "SUPPORTOPS_DB_PATH": str(settings.db_path),
            "SUPPORTOPS_SESSION_ID": settings.session_id,
            "SUPPORTOPS_USER": settings.user_id,
            "PYTHONPATH": os.pathsep.join(
                filter(None, [str(settings.root / "src"), os.getenv("PYTHONPATH", "")])
            ),
        },
    )


async def run_demo() -> dict[str, Any]:
    settings = Settings.load()
    ticket_params = server_parameters("supportops.servers.ticketing_server", settings)
    knowledge_params = server_parameters("supportops.servers.knowledge_server", settings)
    async with Client(ticket_params, read_timeout_seconds=30) as tickets:
        ticket_tools = [tool.name for tool in (await tickets.list_tools()).tools]
        ticket = await tickets.call_tool("get_ticket", {"ticket_id": "INC-1042"})
        proposal = await tickets.call_tool(
            "prepare_ticket_update",
            {
                "ticket_id": "INC-1042",
                "proposed_note": (
                    "Demo diagnostic evidence collected; no external change performed."
                ),
                "reason": "Demonstrate pending human approval workflow",
            },
        )
    async with Client(knowledge_params, read_timeout_seconds=30) as knowledge:
        knowledge_tools = [tool.name for tool in (await knowledge.list_tools()).tools]
        search = await knowledge.call_tool("search_knowledge", {"query": "Outlook send email"})
        resource = await knowledge.read_resource("supportops://knowledge/outlook-send-failure")
    return {
        "ticketing_tools": ticket_tools,
        "knowledge_tools": knowledge_tools,
        "ticket": ticket.structured_content,
        "knowledge_search": search.structured_content,
        "proposal": proposal.structured_content,
        "resource_read": bool(resource.contents),
    }
