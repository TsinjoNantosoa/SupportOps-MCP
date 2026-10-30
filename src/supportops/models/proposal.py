from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from supportops.models.ticket import TicketStatus


class ProposalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    STALE = "STALE"
    EXPIRED = "EXPIRED"


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposal_id: str
    ticket_id: str
    proposed_note: str
    proposed_status: TicketStatus | None
    reason: str
    ticket_version: int
    status: ProposalStatus
    session_id: str
    user_id: str
    idempotency_key: str | None = None
    correlation_id: str | None = None
    approval_request_id: str | None = None
    created_at: datetime
    expires_at: datetime
    decided_at: datetime | None = None
    decision_key: str | None = None
    decided_by: str | None = None
    decision_result: str | None = None
    audit_event_id: int | None = None
