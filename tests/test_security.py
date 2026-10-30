from __future__ import annotations

from supportops.services.approval_service import ApprovalService


def test_llm_cannot_self_approve(db, tickets) -> None:
    from supportops.services.ticket_service import UpdateRequest

    proposal = tickets.prepare_update(
        UpdateRequest(ticket_id="INC-1042", proposed_note="Proposed only.", reason="Security test"),
        session_id="s1",
        user_id="local",
    )
    try:
        ApprovalService(db).decide(
            proposal.proposal_id,
            approve=True,
            session_id="s1",
            actor="model-output",
            trusted_controller=False,
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("Untrusted approval unexpectedly succeeded")
    assert tickets.get_ticket("INC-1042").notes == []
