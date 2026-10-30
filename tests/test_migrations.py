from __future__ import annotations

import sqlite3

from supportops.storage.seed import initialize_database


def test_existing_v1_database_receives_additive_migration(tmp_path) -> None:
    path = tmp_path / "v1.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE tickets (
                ticket_id TEXT PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL,
                priority TEXT NOT NULL,status TEXT NOT NULL,category TEXT NOT NULL,
                assigned_team TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
                version INTEGER NOT NULL
            );
            CREATE TABLE ticket_update_proposals (
                proposal_id TEXT PRIMARY KEY,ticket_id TEXT NOT NULL,proposed_note TEXT NOT NULL,
                proposed_status TEXT,reason TEXT NOT NULL,ticket_version INTEGER NOT NULL,
                status TEXT NOT NULL,session_id TEXT NOT NULL,user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,expires_at TEXT NOT NULL,decided_at TEXT
            );
            """
        )
    db = initialize_database(path)
    with db.connect() as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(ticket_update_proposals)")
        }
        indexes = {
            row["name"] for row in connection.execute("PRAGMA index_list(ticket_update_proposals)")
        }
    assert {"idempotency_key", "correlation_id", "decision_key", "audit_event_id"} <= columns
    assert "idx_proposal_idempotency" in indexes
