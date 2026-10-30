from __future__ import annotations

import hashlib
import json

from supportops.storage.database import Database

PROPOSAL_COLUMNS = {
    "idempotency_key": "TEXT",
    "correlation_id": "TEXT",
    "approval_request_id": "TEXT",
    "decision_key": "TEXT",
    "decided_by": "TEXT",
    "decision_result": "TEXT",
    "audit_event_id": "INTEGER",
}


def migrate_database(db: Database) -> None:
    """Apply additive SQLite migrations without discarding existing demo data."""
    with db.transaction(immediate=True) as connection:
        existing = {
            row["name"] for row in connection.execute("PRAGMA table_info(ticket_update_proposals)")
        }
        for name, column_type in PROPOSAL_COLUMNS.items():
            if name not in existing:
                connection.execute(
                    f"ALTER TABLE ticket_update_proposals ADD COLUMN {name} {column_type}"
                )
        connection.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_proposal_idempotency
            ON ticket_update_proposals(session_id, idempotency_key)
            WHERE idempotency_key IS NOT NULL"""
        )
        connection.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_proposal_decision_key
            ON ticket_update_proposals(decision_key)
            WHERE decision_key IS NOT NULL"""
        )
        _redact_legacy_audit_notes(connection)


def _redact_legacy_audit_notes(connection) -> None:
    """Remove note bodies written by the V1 audit format while preserving evidence."""
    tables = {
        row["name"]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    if "audit_events" not in tables:
        return
    for row in connection.execute("SELECT event_id,details FROM audit_events").fetchall():
        try:
            details = json.loads(row["details"])
        except (TypeError, json.JSONDecodeError):
            continue
        note = details.pop("note", None)
        if not isinstance(note, str):
            continue
        details["note_sha256"] = hashlib.sha256(note.encode("utf-8")).hexdigest()
        details["note_length"] = len(note)
        connection.execute(
            "UPDATE audit_events SET details=? WHERE event_id=?",
            (json.dumps(details, sort_keys=True), row["event_id"]),
        )
