from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from supportops.storage.database import Database

SEED_TICKETS = [
    (
        "INC-1042",
        "Outlook cannot send emails",
        "A fictional user cannot send messages from Outlook Desktop; messages remain in Outbox.",
        "MEDIUM",
        "OPEN",
        "Microsoft 365",
        "Messaging Support",
    ),
    (
        "INC-1043",
        "No internet connectivity",
        "A demo workstation reports connected but cannot reach approved internal "
        "or public test endpoints.",
        "HIGH",
        "OPEN",
        "Network",
        "Network Support",
    ),
    (
        "INC-1044",
        "Network printer unavailable",
        "The fictional Finance-floor printer is shown offline to several demo workstations.",
        "MEDIUM",
        "IN_PROGRESS",
        "Printer",
        "Workplace Support",
    ),
    (
        "INC-1045",
        "Microsoft 365 MFA issue",
        "A fictional user cannot complete MFA after replacing a demonstration phone.",
        "HIGH",
        "OPEN",
        "Identity",
        "Identity Support",
    ),
    (
        "INC-1046",
        "DNS resolution failure",
        "Names do not resolve on one demo workstation while direct test IP connectivity succeeds.",
        "HIGH",
        "OPEN",
        "Network",
        "Network Support",
    ),
    (
        "INC-1047",
        "Windows profile loading error",
        "Windows signs a fictional user into a temporary profile in the lab environment.",
        "MEDIUM",
        "PENDING",
        "Windows",
        "Workplace Support",
    ),
    (
        "INC-1048",
        "Shared folder access denied",
        "A fictional user receives access denied for a demonstration shared folder.",
        "MEDIUM",
        "OPEN",
        "Permissions",
        "Access Support",
    ),
    (
        "INC-1049",
        "Application performance degradation",
        "A demonstration line-of-business application is slow during local test runs.",
        "LOW",
        "IN_PROGRESS",
        "Software",
        "Application Support",
    ),
]


def initialize_database(path: Path, *, reset: bool = False) -> Database:
    db = Database(path)
    if reset and path.exists():
        path.unlink()
    schema_path = Path(__file__).with_name("schema.sql")
    db.initialize(schema_path)
    now = datetime(2026, 1, 15, 9, 0, tzinfo=UTC)
    with db.transaction(immediate=True) as connection:
        count = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if count == 0:
            for index, ticket in enumerate(SEED_TICKETS):
                timestamp = (now + timedelta(minutes=index)).isoformat()
                connection.execute(
                    """INSERT INTO tickets
                    (ticket_id,title,description,priority,status,category,assigned_team,
                     created_at,updated_at,version) VALUES (?,?,?,?,?,?,?,?,?,1)""",
                    (*ticket, timestamp, timestamp),
                )
    return db
