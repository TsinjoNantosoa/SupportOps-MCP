from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from supportops.models.ticket import TicketStatus
from supportops.services.approval_service import ApprovalError, ApprovalService
from supportops.services.ticket_service import UpdateRequest


def make_proposal(tickets, session: str = "s1"):
    return tickets.prepare_update(
        UpdateRequest(
            ticket_id="INC-1042",
            proposed_note="Exact diagnostic note for approval testing.",
            proposed_status=TicketStatus.IN_PROGRESS,
            reason="Test approval controls",
        ),
        session_id=session,
        user_id="operator",
    )


def test_valid_approval_is_single_use_and_audited(db, tickets) -> None:
    proposal = make_proposal(tickets)
    approval = ApprovalService(db)
    result = approval.decide(
        proposal.proposal_id,
        approve=True,
        session_id="s1",
        actor="operator",
        trusted_controller=True,
    )
    assert result["ticket_changed"] is True
    ticket = tickets.get_ticket("INC-1042")
    assert ticket.status == TicketStatus.IN_PROGRESS
    assert ticket.version == 2
    assert len(ticket.notes) == 1
    with pytest.raises(ApprovalError, match="already processed"):
        approval.decide(
            proposal.proposal_id,
            approve=True,
            session_id="s1",
            actor="operator",
            trusted_controller=True,
        )
    with db.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0] >= 2


def test_rejection_never_changes_ticket_and_is_single_use(db, tickets) -> None:
    proposal = make_proposal(tickets)
    before = tickets.get_ticket("INC-1042")
    approval = ApprovalService(db)
    result = approval.decide(
        proposal.proposal_id,
        approve=False,
        session_id="s1",
        actor="operator",
        trusted_controller=True,
    )
    assert result["ticket_changed"] is False
    assert tickets.get_ticket("INC-1042").version == before.version
    with pytest.raises(ApprovalError):
        approval.decide(
            proposal.proposal_id,
            approve=False,
            session_id="s1",
            actor="operator",
            trusted_controller=True,
        )


def test_session_expiry_stale_and_untrusted_controller(db, tickets) -> None:
    approval = ApprovalService(db)
    cross_session = make_proposal(tickets, "owner")
    with pytest.raises(PermissionError, match="another session"):
        approval.decide(
            cross_session.proposal_id,
            approve=True,
            session_id="intruder",
            actor="agent",
            trusted_controller=True,
        )
    with db.connect() as connection:
        denial = connection.execute(
            "SELECT outcome FROM audit_events ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    assert denial["outcome"] == "SESSION_MISMATCH"
    with pytest.raises(PermissionError, match="trusted CLI"):
        approval.decide(
            cross_session.proposal_id,
            approve=True,
            session_id="owner",
            actor="LLM",
            trusted_controller=False,
        )

    expired = make_proposal(tickets, "owner")
    with db.transaction(immediate=True) as connection:
        connection.execute(
            "UPDATE ticket_update_proposals SET expires_at=? WHERE proposal_id=?",
            ((datetime.now(UTC) - timedelta(seconds=1)).isoformat(), expired.proposal_id),
        )
    with pytest.raises(ApprovalError, match="expired"):
        approval.decide(
            expired.proposal_id,
            approve=True,
            session_id="owner",
            actor="operator",
            trusted_controller=True,
        )
    assert tickets.get_proposal(expired.proposal_id).status == "EXPIRED"

    stale = make_proposal(tickets, "owner")
    with db.transaction(immediate=True) as connection:
        connection.execute("UPDATE tickets SET version=version+1 WHERE ticket_id='INC-1042'")
    with pytest.raises(ApprovalError, match="stale"):
        approval.decide(
            stale.proposal_id,
            approve=True,
            session_id="owner",
            actor="operator",
            trusted_controller=True,
        )
    assert tickets.get_proposal(stale.proposal_id).status == "STALE"
