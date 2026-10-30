PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL CHECK(priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    status TEXT NOT NULL CHECK(status IN ('OPEN','IN_PROGRESS','PENDING','RESOLVED','CLOSED')),
    category TEXT NOT NULL,
    assigned_team TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1 CHECK(version >= 1)
);

CREATE TABLE IF NOT EXISTS ticket_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id),
    note TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_update_proposals (
    proposal_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id),
    proposed_note TEXT NOT NULL,
    proposed_status TEXT,
    reason TEXT NOT NULL,
    ticket_version INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING','APPROVED','REJECTED','STALE','EXPIRED')),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    idempotency_key TEXT,
    correlation_id TEXT,
    approval_request_id TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    decided_at TEXT,
    decision_key TEXT,
    decided_by TEXT,
    decision_result TEXT,
    audit_event_id INTEGER
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    details TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON ticket_update_proposals(status);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_events(occurred_at);
