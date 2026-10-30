from __future__ import annotations

import pytest
from pydantic import ValidationError

from supportops.models.ticket import Priority, TicketStatus
from supportops.services.ticket_service import TicketService, UpdateRequest


def test_list_filter_search_and_missing(tickets: TicketService) -> None:
    assert len(tickets.list_tickets(limit=100)) == 8
    assert all(row["status"] == "OPEN" for row in tickets.list_tickets(TicketStatus.OPEN))
    assert all(row["priority"] == "HIGH" for row in tickets.list_tickets(priority=Priority.HIGH))
    assert tickets.search_tickets("Outlook")[0]["ticket_id"] == "INC-1042"
    with pytest.raises(LookupError):
        tickets.get_ticket("INC-9999")


def test_validation_and_sql_wildcards_are_literal(tickets: TicketService) -> None:
    with pytest.raises(ValueError):
        tickets.list_tickets(limit=101)
    with pytest.raises(ValueError):
        tickets.search_tickets("x")
    assert tickets.search_tickets("%%") == []
    with pytest.raises(ValidationError):
        UpdateRequest(ticket_id="../../db", proposed_note="valid note", reason="test")


def test_prepare_does_not_change_ticket(tickets: TicketService) -> None:
    before = tickets.get_ticket("INC-1042")
    proposal = tickets.prepare_update(
        UpdateRequest(
            ticket_id="INC-1042",
            proposed_note="Collected reproducible diagnostic evidence.",
            proposed_status=TicketStatus.IN_PROGRESS,
            reason="Technician review",
        ),
        session_id="s1",
        user_id="operator",
    )
    after = tickets.get_ticket("INC-1042")
    assert proposal.status == "PENDING"
    assert before.status == after.status
    assert before.notes == after.notes == []
    assert before.version == after.version
