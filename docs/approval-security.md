# Approval and idempotency security

Proposal preparation captures exact fields, session, host identity, ticket version, expiry, optional correlation ID, and optional idempotency key. Reusing the same session/key with the same payload returns the original proposal. Reusing it for changed fields is rejected.

Approval occurs under `BEGIN IMMEDIATE`. The controller checks PENDING state, session, expiry, ticket version, and authorization before inserting the note and incrementing the ticket version. The proposal state and audit event are written in the same transaction. A repeated decision without a matching decision key is rejected. A retry with the same decision key/outcome returns the original audit ID without applying another note.

The approval API always requires a bearer token for proposal reads. Remote decisions additionally require an explicit enable flag and an allowlisted approver header. They are disabled by default because a shared service credential plus header is not enterprise-grade individual identity. The trusted CLI is the recommended MVP path.
