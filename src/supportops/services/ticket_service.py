from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

from supportops.models.proposal import Proposal
from supportops.models.ticket import Priority, Ticket, TicketStatus
from supportops.services.audit_service import record_audit
from supportops.storage.database import Database

TICKET_ID = re.compile(r"^INC-\d{4,}$")
ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.RESOLVED},
    TicketStatus.IN_PROGRESS: {TicketStatus.PENDING, TicketStatus.RESOLVED, TicketStatus.OPEN},
    TicketStatus.PENDING: {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.OPEN},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.OPEN},
    TicketStatus.CLOSED: {TicketStatus.OPEN},
}


class UpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    ticket_id: str = Field(pattern=r"^INC-\d{4,}$")
    proposed_note: str = Field(min_length=3, max_length=2000)
    proposed_status: TicketStatus | None = None
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("proposed_note", "reason")
    @classmethod
    def no_control_characters(cls, value: str) -> str:
        if any(ord(char) < 32 and char not in "\n\t" for char in value):
            raise ValueError("control characters are not allowed")
        return value


class TicketService:
    def __init__(self, db: Database) -> None:
        self.db = db

    @staticmethod
    def _validate_ticket_id(ticket_id: str) -> None:
        if not TICKET_ID.fullmatch(ticket_id):
            raise ValueError("ticket_id must match INC-<digits>")

    def list_tickets(
        self, status: TicketStatus | None = None, priority: Priority | None = None, limit: int = 20
    ) -> list[dict[str, object]]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        clauses: list[str] = []
        params: list[object] = []
        if status:
            clauses.append("status = ?")
            params.append(status.value)
        if priority:
            clauses.append("priority = ?")
            params.append(priority.value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT ticket_id,title,priority,status,created_at,"
            "substr(description,1,160) AS summary FROM tickets"
            + where
            + " ORDER BY ticket_id LIMIT ?"
        )
        params.append(limit)
        with self.db.connect() as connection:
            return [dict(row) for row in connection.execute(sql, params).fetchall()]

    def get_ticket(self, ticket_id: str) -> Ticket:
        self._validate_ticket_id(ticket_id)
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
            if row is None:
                raise LookupError(f"Ticket {ticket_id} was not found")
            notes = [
                item[0]
                for item in connection.execute(
                    "SELECT note FROM ticket_notes WHERE ticket_id = ? ORDER BY id", (ticket_id,)
                ).fetchall()
            ]
        return Ticket(**dict(row), notes=notes)

    def search_tickets(self, query: str, limit: int = 20) -> list[dict[str, object]]:
        query = query.strip()
        if not 2 <= len(query) <= 200:
            raise ValueError("query length must be between 2 and 200")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        with self.db.connect() as connection:
            rows = connection.execute(
                """SELECT ticket_id,title,priority,status,category,
                substr(description,1,200) AS summary FROM tickets
                WHERE title LIKE ? ESCAPE '\\' COLLATE NOCASE
                   OR description LIKE ? ESCAPE '\\' COLLATE NOCASE
                ORDER BY ticket_id LIMIT ?""",
                (pattern, pattern, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def prepare_update(
        self, request: UpdateRequest, *, session_id: str, user_id: str, ttl_minutes: int = 30
    ) -> Proposal:
        ticket = self.get_ticket(request.ticket_id)
        if (
            request.proposed_status
            and request.proposed_status not in ALLOWED_TRANSITIONS[ticket.status]
        ):
            raise ValueError(
                f"status transition {ticket.status} -> {request.proposed_status} is not allowed"
            )
        now = datetime.now(UTC)
        proposal_id = f"PROP-{uuid.uuid4().hex[:12].upper()}"
        values = (
            proposal_id,
            ticket.ticket_id,
            request.proposed_note,
            request.proposed_status.value if request.proposed_status else None,
            request.reason,
            ticket.version,
            "PENDING",
            session_id,
            user_id,
            now.isoformat(),
            (now + timedelta(minutes=ttl_minutes)).isoformat(),
        )
        with self.db.transaction(immediate=True) as connection:
            connection.execute(
                """INSERT INTO ticket_update_proposals
                (proposal_id,ticket_id,proposed_note,proposed_status,reason,ticket_version,
                 status,session_id,user_id,created_at,expires_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                values,
            )
            record_audit(
                connection,
                actor=user_id,
                action="PROPOSAL_CREATED",
                target_type="ticket_update_proposal",
                target_id=proposal_id,
                outcome="PENDING",
                details={"ticket_id": ticket.ticket_id, "session_id": session_id},
            )
        return self.get_proposal(proposal_id)

    def get_proposal(self, proposal_id: str) -> Proposal:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM ticket_update_proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
        if row is None:
            raise LookupError(f"Proposal {proposal_id} was not found")
        return Proposal(**dict(row))

    def list_proposals(self, status: str | None = None) -> list[dict[str, object]]:
        with self.db.connect() as connection:
            if status:
                rows = connection.execute(
                    "SELECT * FROM ticket_update_proposals "
                    "WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM ticket_update_proposals ORDER BY created_at DESC"
                ).fetchall()
        return [dict(row) for row in rows]
