from __future__ import annotations

import inspect

from supportops.agent.instructions import COPILOT_INSTRUCTIONS
from supportops.servers import knowledge_server, ticketing_server


def test_agent_policy_and_capability_separation() -> None:
    lowered = COPILOT_INSTRUCTIONS.lower()
    assert "untrusted" in lowered
    assert "never claim" in lowered
    assert "sources" in lowered
    ticket_source = inspect.getsource(ticketing_server)
    assert "approve" not in {
        line.split("def ", 1)[1].split("(", 1)[0]
        for line in ticket_source.splitlines()
        if line.startswith("def ")
    }
    assert "ApprovalService" not in ticket_source
    assert "prepare_ticket_update" in ticket_source
    assert "search_knowledge" in inspect.getsource(knowledge_server)
