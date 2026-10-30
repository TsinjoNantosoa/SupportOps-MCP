from __future__ import annotations

import os
import sys

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from supportops.agent.instructions import COPILOT_INSTRUCTIONS
from supportops.config import Settings


def _server_env(settings: Settings) -> dict[str, str]:
    return {
        "SUPPORTOPS_DB_PATH": str(settings.db_path),
        "SUPPORTOPS_SESSION_ID": settings.session_id,
        "SUPPORTOPS_USER": settings.user_id,
    }


async def run_copilot(prompt: str) -> str:
    settings = Settings.load()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for 'supportops chat'")
    common = {"command": sys.executable, "env": _server_env(settings)}
    async with (
        MCPServerStdio(
            name="supportops-ticketing",
            params={**common, "args": ["-m", "supportops.servers.ticketing_server"]},
            cache_tools_list=True,
            client_session_timeout_seconds=30,
        ) as ticketing,
        MCPServerStdio(
            name="supportops-knowledge",
            params={**common, "args": ["-m", "supportops.servers.knowledge_server"]},
            cache_tools_list=True,
            client_session_timeout_seconds=30,
        ) as knowledge,
    ):
        agent = Agent(
            name="SupportOps AI Copilot",
            instructions=COPILOT_INSTRUCTIONS,
            model=settings.model,
            mcp_servers=[ticketing, knowledge],
        )
        result = await Runner.run(agent, prompt, max_turns=12)
        return str(result.final_output)
