# Security review

Trust boundaries are enforced in code: MCP input is untrusted; tool output is untrusted agent context; approval is a host-only operation. SQLite statements are parameterized. File access uses an identifier-to-filename allowlist plus resolved parent verification. Proposal identity comes from the host process environment, not a model argument.

Approval uses `BEGIN IMMEDIATE`, validates `PENDING`, session, expiry, and captured ticket version, updates the ticket with a version predicate, marks the proposal exactly once, and writes the audit event in the same transaction. The agent has no approval tool.

Local stdio reduces network exposure but is not a process sandbox. Local environment identity is demonstration-only. A remote design needs authenticated Streamable HTTP, TLS, token audience validation, origin and host checks, per-tool authorization, rate limiting, dependency/schema integrity monitoring, and centralized redacted audit logs.

