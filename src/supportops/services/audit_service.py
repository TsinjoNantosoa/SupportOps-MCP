from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from supportops.storage.database import Database


def record_audit(
    connection: sqlite3.Connection,
    *,
    actor: str,
    action: str,
    target_type: str,
    target_id: str,
    outcome: str,
    details: dict[str, object],
) -> None:
    connection.execute(
        """INSERT INTO audit_events
        (occurred_at,actor,action,target_type,target_id,outcome,details)
        VALUES (?,?,?,?,?,?,?)""",
        (
            datetime.now(UTC).isoformat(),
            actor,
            action,
            target_type,
            target_id,
            outcome,
            json.dumps(details, sort_keys=True),
        ),
    )


def list_audit(db: Database, limit: int = 100) -> list[dict[str, object]]:
    limit = max(1, min(limit, 500))
    with db.connect() as connection:
        rows = connection.execute(
            "SELECT * FROM audit_events ORDER BY event_id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]
