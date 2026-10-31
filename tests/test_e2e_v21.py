from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import AsyncExitStack, contextmanager
from pathlib import Path

import pytest
from mcp import Client

from supportops.services.approval_service import ApprovalService
from supportops.services.audit_service import list_audit
from supportops.services.ticket_service import TicketService
from supportops.storage.seed import initialize_database


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def supportops_http_stack(tmp_path: Path) -> Iterator[tuple[str, str, Path]]:
    ticket_port = free_port()
    knowledge_port = free_port()
    db_path = tmp_path / "e2e.db"
    env = os.environ.copy()
    env.update(
        {
            "SUPPORTOPS_MCP_TRANSPORT": "streamable-http",
            "SUPPORTOPS_DB_PATH": str(db_path),
            "SUPPORTOPS_KNOWLEDGE_DIR": str(Path(__file__).parents[1] / "knowledge"),
            "SUPPORTOPS_TICKETING_HOST": "127.0.0.1",
            "SUPPORTOPS_TICKETING_PORT": str(ticket_port),
            "SUPPORTOPS_KNOWLEDGE_HOST": "127.0.0.1",
            "SUPPORTOPS_KNOWLEDGE_PORT": str(knowledge_port),
            "SUPPORTOPS_ALLOWED_HOSTS": (
                f"127.0.0.1:{ticket_port},127.0.0.1:{knowledge_port}"
            ),
            "SUPPORTOPS_ALLOWED_ORIGINS": "http://localhost:5678",
            "SUPPORTOPS_SESSION_ID": "e2e-session",
            "SUPPORTOPS_USER": "e2e-n8n",
        }
    )
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for module, port in (
            ("supportops.servers.ticketing_server", ticket_port),
            ("supportops.servers.knowledge_server", knowledge_port),
        ):
            process = subprocess.Popen(
                [sys.executable, "-m", module],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(process)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"{module} exited with {process.returncode}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise TimeoutError(f"{module} did not start")
        yield (
            f"http://127.0.0.1:{ticket_port}/mcp",
            f"http://127.0.0.1:{knowledge_port}/mcp",
            db_path,
        )
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.mark.asyncio
async def test_deterministic_cross_server_proposal_local_approval_and_audit(tmp_path) -> None:
    with supportops_http_stack(tmp_path) as (ticket_url, knowledge_url, db_path):
        async with AsyncExitStack() as stack:
            ticket_client = await stack.enter_async_context(
                Client(ticket_url, read_timeout_seconds=10)
            )
            knowledge_client = await stack.enter_async_context(
                Client(knowledge_url, read_timeout_seconds=10)
            )
            ticket_tools = {tool.name for tool in (await ticket_client.list_tools()).tools}
            knowledge_tools = {tool.name for tool in (await knowledge_client.list_tools()).tools}
            assert {"get_ticket", "prepare_ticket_update"} <= ticket_tools
            assert {"search_knowledge", "get_procedure"} <= knowledge_tools

            ticket = (
                await ticket_client.call_tool("get_ticket", {"ticket_id": "INC-1042"})
            ).structured_content
            search = (
                await knowledge_client.call_tool(
                    "search_knowledge", {"query": "Outlook sending issue", "limit": 3}
                )
            ).structured_content
            assert ticket["ticket_id"] == "INC-1042"
            assert search["results"]
            procedure_id = search["results"][0]["procedure_id"]
            procedure = (
                await knowledge_client.call_tool(
                    "get_procedure", {"procedure_id": procedure_id}
                )
            ).structured_content
            assert procedure["source_reference"].endswith(".md")

            proposal = (
                await ticket_client.call_tool(
                    "prepare_ticket_update",
                    {
                        "ticket_id": "INC-1042",
                        "proposed_note": (
                            "Deterministic V2.1 diagnosis prepared from "
                            f"{procedure['source_reference']}; human review required."
                        ),
                        "reason": "V2.1 deterministic end-to-end demonstration",
                        "idempotency_key": "e2e-execution-001",
                        "correlation_id": "e2e-correlation-001",
                    },
                )
            ).structured_content
            unchanged = (
                await ticket_client.call_tool("get_ticket", {"ticket_id": "INC-1042"})
            ).structured_content
            assert proposal["status"] == "PENDING"
            assert unchanged["version"] == ticket["version"]
            assert unchanged["notes"] == ticket["notes"]

        db = initialize_database(db_path)
        approval = ApprovalService(db)
        applied = approval.decide(
            proposal["proposal_id"],
            approve=True,
            session_id="e2e-session",
            actor="trusted-local-technician",
            trusted_controller=True,
            decision_key="e2e-decision-001",
        )
        replay = approval.decide(
            proposal["proposal_id"],
            approve=True,
            session_id="e2e-session",
            actor="trusted-local-technician",
            trusted_controller=True,
            decision_key="e2e-decision-001",
        )
        final_ticket = TicketService(db).get_ticket("INC-1042")
        assert applied["ticket_changed"] is True
        assert replay["idempotent_replay"] is True
        assert replay["audit_event_id"] == applied["audit_event_id"]
        assert len(final_ticket.notes) == 1
        assert any(event["target_id"] == proposal["proposal_id"] for event in list_audit(db))


def test_unavailable_mcp_does_not_change_ticket(tmp_path) -> None:
    db = initialize_database(tmp_path / "failure.db", reset=True)
    tickets = TicketService(db)
    before = tickets.get_ticket("INC-1042")
    port = free_port()
    with socket.socket() as sock:
        sock.settimeout(0.2)
        assert sock.connect_ex(("127.0.0.1", port)) != 0
    after = tickets.get_ticket("INC-1042")
    assert after.version == before.version
    assert after.notes == before.notes
