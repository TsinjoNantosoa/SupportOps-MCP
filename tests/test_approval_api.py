from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from supportops.services.ticket_service import TicketService, UpdateRequest
from supportops.storage.seed import initialize_database


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def approval_api(tmp_path: Path, *, enabled: bool) -> Iterator[tuple[str, TicketService]]:
    db_path = tmp_path / "approval.db"
    tickets = TicketService(initialize_database(db_path, reset=True))
    port = free_port()
    env = os.environ.copy()
    env.update(
        {
            "SUPPORTOPS_DB_PATH": str(db_path),
            "SUPPORTOPS_APPROVAL_HOST": "127.0.0.1",
            "SUPPORTOPS_APPROVAL_PORT": str(port),
            "SUPPORTOPS_APPROVAL_API_TOKEN": "approval-test-token",
            "SUPPORTOPS_REMOTE_APPROVAL_ENABLED": str(enabled).lower(),
            "SUPPORTOPS_AUTHORIZED_APPROVERS": "alice",
        }
    )
    process = subprocess.Popen(
        [sys.executable, "-m", "supportops.approval_api"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=0.5):
                    break
            except OSError:
                if process.poll() is not None:
                    raise RuntimeError("Approval API exited during startup") from None
                time.sleep(0.1)
        else:
            raise TimeoutError("Approval API did not start")
        yield f"http://127.0.0.1:{port}", tickets
    finally:
        process.terminate()
        process.wait(timeout=10)


def proposal(tickets: TicketService):
    return tickets.prepare_update(
        UpdateRequest(
            ticket_id="INC-1042",
            proposed_note="Remote approval API test note.",
            reason="Verify safe API behavior",
        ),
        session_id="n8n-session",
        user_id="n8n-host",
    )


def request_json(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, object] | None = None,
    approver: str | None = None,
) -> dict[str, object]:
    headers = {"Authorization": "Bearer approval-test-token"}
    if approver:
        headers["X-SupportOps-Approver"] = approver
    data = json.dumps(body).encode() if body else None
    if data:
        headers["Content-Type"] = "application/json"
    with urlopen(Request(url, data=data, headers=headers, method=method), timeout=5) as response:
        return json.loads(response.read())


def test_remote_decisions_are_disabled_by_default(tmp_path) -> None:
    with approval_api(tmp_path, enabled=False) as (base_url, tickets):
        pending = proposal(tickets)
        read = request_json(f"{base_url}/proposals/{pending.proposal_id}")
        assert read["status"] == "PENDING"
        with pytest.raises(HTTPError) as denied:
            request_json(
                f"{base_url}/proposals/{pending.proposal_id}/decision",
                method="POST",
                body={
                    "decision": "APPROVE",
                    "session_id": "n8n-session",
                    "decision_key": "exec-disabled",
                },
                approver="alice",
            )
        assert denied.value.code == 403
        assert tickets.get_ticket("INC-1042").notes == []


def test_authorized_remote_decision_and_retry_are_idempotent(tmp_path) -> None:
    with approval_api(tmp_path, enabled=True) as (base_url, tickets):
        pending = proposal(tickets)
        url = f"{base_url}/proposals/{pending.proposal_id}/decision"
        body = {
            "decision": "APPROVE",
            "session_id": "n8n-session",
            "decision_key": "n8n-execution-42",
        }
        with pytest.raises(HTTPError) as forged:
            request_json(url, method="POST", body=body, approver="mallory")
        assert forged.value.code == 403

        first = request_json(url, method="POST", body=body, approver="alice")
        replay = request_json(url, method="POST", body=body, approver="alice")
        assert first["audit_event_id"] == replay["audit_event_id"]
        assert replay["idempotent_replay"] is True
        assert len(tickets.get_ticket("INC-1042").notes) == 1
