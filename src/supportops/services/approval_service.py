from __future__ import annotations

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
    ) -> dict[str, object]:
        if not trusted_controller:
            raise PermissionError("Only the trusted CLI controller may decide proposals")
        now = datetime.now(UTC)
        deferred_error: Exception | None = None
        result: dict[str, object] | None = None
        with self.db.transaction(immediate=True) as connection:
            proposal = connection.execute(
                "SELECT * FROM ticket_update_proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
            if proposal is None:
                raise LookupError(f"Proposal {proposal_id} was not found")
            if proposal["status"] != "PENDING":
                raise ApprovalError(f"Proposal already processed with status {proposal['status']}")
            if proposal["session_id"] != session_id:
                self._audit_denial(connection, actor, proposal_id, "SESSION_MISMATCH")
                deferred_error = PermissionError("Proposal belongs to another session")
            elif datetime.fromisoformat(proposal["expires_at"]) <= now:
                connection.execute(
                    "UPDATE ticket_update_proposals SET status='EXPIRED', decided_at=? "
                    "WHERE proposal_id=? AND status='PENDING'",
                    (now.isoformat(), proposal_id),
                )
                self._audit_denial(connection, actor, proposal_id, "EXPIRED")
                deferred_error = ApprovalError("Proposal has expired")
            elif not approve:
                changed = connection.execute(
                    "UPDATE ticket_update_proposals SET status='REJECTED', decided_at=? "
                    "WHERE proposal_id=? AND status='PENDING'",
                    (now.isoformat(), proposal_id),
                ).rowcount
                if changed != 1:
                    raise ApprovalError("Proposal could not be rejected atomically")
                record_audit(
                    connection,
                    actor=actor,
                    action="PROPOSAL_REJECTED",
                    target_type="ticket_update_proposal",
                    target_id=proposal_id,
                    outcome="REJECTED",
                    details={"ticket_id": proposal["ticket_id"]},
                )
                result = {
                    "proposal_id": proposal_id,
                    "status": "REJECTED",
                    "ticket_changed": False,
                }
            else:
                ticket = connection.execute(
                    "SELECT version FROM tickets WHERE ticket_id = ?", (proposal["ticket_id"],)
                ).fetchone()
                if ticket is None or ticket["version"] != proposal["ticket_version"]:
                    connection.execute(
                        "UPDATE ticket_update_proposals SET status='STALE', decided_at=? "
                        "WHERE proposal_id=? AND status='PENDING'",
                        (now.isoformat(), proposal_id),
                    )
                    self._audit_denial(connection, actor, proposal_id, "STALE_VERSION")
                    deferred_error = ApprovalError(
                        "Ticket changed after proposal creation; proposal is stale"
                    )
                else:
                    self._apply(connection, proposal, proposal_id, actor, now)
                    result = {
                        "proposal_id": proposal_id,
                        "status": "APPROVED",
                        "ticket_changed": True,
                    }
        if deferred_error:
            raise deferred_error
        if result is None:
            raise ApprovalError("Proposal decision produced no result")
        return result

    @staticmethod
    def _apply(connection, proposal, proposal_id: str, actor: str, now: datetime) -> None:
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
        decided = connection.execute(
            "UPDATE ticket_update_proposals SET status='APPROVED',decided_at=? "
            "WHERE proposal_id=? AND status='PENDING'",
            (now.isoformat(), proposal_id),
        ).rowcount
        if decided != 1:
            raise ApprovalError("Proposal could not be approved atomically")
        record_audit(
            connection,
            actor=actor,
            action="PROPOSAL_APPROVED",
            target_type="ticket_update_proposal",
            target_id=proposal_id,
            outcome="APPLIED",
            details={
                "ticket_id": proposal["ticket_id"],
                "note": proposal["proposed_note"],
                "status": proposal["proposed_status"],
            },
        )

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
