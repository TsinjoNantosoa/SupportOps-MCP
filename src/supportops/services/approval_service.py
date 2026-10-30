from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from supportops.services.audit_service import record_audit
from supportops.storage.database import Database


class ApprovalError(RuntimeError):
    pass


class ApprovalService:
    """Trusted host-side controller. This service is never exposed as an MCP tool."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def decide(
        self,
        proposal_id: str,
        *,
        approve: bool,
        session_id: str,
        actor: str,
        trusted_controller: bool,
        decision_key: str | None = None,
    ) -> dict[str, object]:
        if not trusted_controller:
            raise PermissionError("Only the trusted CLI controller may decide proposals")
        now = datetime.now(UTC)
        decision_key = self._validate_decision_key(decision_key)
        deferred_error: Exception | None = None
        result: dict[str, object] | None = None
        with self.db.transaction(immediate=True) as connection:
            proposal = connection.execute(
                "SELECT * FROM ticket_update_proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if proposal is None:
                raise LookupError(f"Proposal {proposal_id} was not found")
            if proposal["status"] != "PENDING":
                expected = "APPROVED" if approve else "REJECTED"
                if (
                    decision_key
                    and proposal["decision_key"] == decision_key
                    and proposal["status"] == expected
                ):
                    return {
                        "proposal_id": proposal_id,
                        "status": expected,
                        "ticket_changed": expected == "APPROVED",
                        "idempotent_replay": True,
                        "audit_event_id": proposal["audit_event_id"],
                    }
                raise ApprovalError(f"Proposal already processed with status {proposal['status']}")
            if proposal["session_id"] != session_id:
                self._audit_denial(connection, actor, proposal_id, "SESSION_MISMATCH")
                deferred_error = PermissionError("Proposal belongs to another session")
            elif datetime.fromisoformat(proposal["expires_at"]) <= now:
                connection.execute(
                    "UPDATE ticket_update_proposals SET status='EXPIRED', decided_at=?, "
                    "decided_by=?, decision_result='EXPIRED' "
                    "WHERE proposal_id=? AND status='PENDING'",
                    (now.isoformat(), actor, proposal_id),
                )
                self._audit_denial(connection, actor, proposal_id, "EXPIRED")
                deferred_error = ApprovalError("Proposal has expired")
            elif not approve:
                audit_event_id = record_audit(
                    connection,
                    actor=actor,
                    action="PROPOSAL_REJECTED",
                    target_type="ticket_update_proposal",
                    target_id=proposal_id,
                    outcome="REJECTED",
                    details={"ticket_id": proposal["ticket_id"]},
                )
                changed = connection.execute(
                    """UPDATE ticket_update_proposals
                    SET status='REJECTED',decided_at=?,decision_key=?,decided_by=?,
                        decision_result='REJECTED',audit_event_id=?
                    WHERE proposal_id=? AND status='PENDING'""",
                    (now.isoformat(), decision_key, actor, audit_event_id, proposal_id),
                ).rowcount
                if changed != 1:
                    raise ApprovalError("Proposal could not be rejected atomically")
                result = {
                    "proposal_id": proposal_id,
                    "status": "REJECTED",
                    "ticket_changed": False,
                    "idempotent_replay": False,
                    "audit_event_id": audit_event_id,
                }
            else:
                ticket = connection.execute(
                    "SELECT version FROM tickets WHERE ticket_id = ?", (proposal["ticket_id"],)
                ).fetchone()
                if ticket is None or ticket["version"] != proposal["ticket_version"]:
                    connection.execute(
                        "UPDATE ticket_update_proposals SET status='STALE', decided_at=?, "
                        "decided_by=?, decision_result='STALE' "
                        "WHERE proposal_id=? AND status='PENDING'",
                        (now.isoformat(), actor, proposal_id),
                    )
                    self._audit_denial(connection, actor, proposal_id, "STALE_VERSION")
                    deferred_error = ApprovalError(
                        "Ticket changed after proposal creation; proposal is stale"
                    )
                else:
                    audit_event_id = self._apply(
                        connection, proposal, proposal_id, actor, now, decision_key
                    )
                    result = {
                        "proposal_id": proposal_id,
                        "status": "APPROVED",
                        "ticket_changed": True,
                        "idempotent_replay": False,
                        "audit_event_id": audit_event_id,
                    }
        if deferred_error:
            raise deferred_error
        if result is None:
            raise ApprovalError("Proposal decision produced no result")
        return result

    @staticmethod
    def _apply(
        connection,
        proposal,
        proposal_id: str,
        actor: str,
        now: datetime,
        decision_key: str | None,
    ) -> int:
        connection.execute(
            """INSERT INTO ticket_notes(ticket_id,note,created_at,created_by)
            VALUES (?,?,?,?)""",
            (proposal["ticket_id"], proposal["proposed_note"], now.isoformat(), actor),
        )
        if proposal["proposed_status"]:
            updated = connection.execute(
                """UPDATE tickets SET status=?,updated_at=?,version=version+1
                WHERE ticket_id=? AND version=?""",
                (
                    proposal["proposed_status"],
                    now.isoformat(),
                    proposal["ticket_id"],
                    proposal["ticket_version"],
                ),
            ).rowcount
        else:
            updated = connection.execute(
                """UPDATE tickets SET updated_at=?,version=version+1
                WHERE ticket_id=? AND version=?""",
                (now.isoformat(), proposal["ticket_id"], proposal["ticket_version"]),
            ).rowcount
        if updated != 1:
            raise ApprovalError("Atomic ticket update failed")
        audit_event_id = record_audit(
            connection,
            actor=actor,
            action="PROPOSAL_APPROVED",
            target_type="ticket_update_proposal",
            target_id=proposal_id,
            outcome="APPLIED",
            details={
                "ticket_id": proposal["ticket_id"],
                "note_sha256": hashlib.sha256(
                    proposal["proposed_note"].encode("utf-8")
                ).hexdigest(),
                "note_length": len(proposal["proposed_note"]),
                "status": proposal["proposed_status"],
            },
        )
        decided = connection.execute(
            """UPDATE ticket_update_proposals
            SET status='APPROVED',decided_at=?,decision_key=?,decided_by=?,
                decision_result='APPLIED',audit_event_id=?
            WHERE proposal_id=? AND status='PENDING'""",
            (now.isoformat(), decision_key, actor, audit_event_id, proposal_id),
        ).rowcount
        if decided != 1:
            raise ApprovalError("Proposal could not be approved atomically")
        return audit_event_id

    @staticmethod
    def _validate_decision_key(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not 1 <= len(value) <= 200 or any(char.isspace() for char in value):
            raise ValueError("decision_key must be 1-200 non-whitespace characters")
        return value

    @staticmethod
    def _audit_denial(connection, actor: str, proposal_id: str, outcome: str) -> None:
        record_audit(
            connection,
            actor=actor,
            action="PROPOSAL_DECISION_DENIED",
            target_type="ticket_update_proposal",
            target_id=proposal_id,
            outcome=outcome,
            details={},
        )
