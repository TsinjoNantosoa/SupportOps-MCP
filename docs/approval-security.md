# Approval and idempotency security

Proposal preparation captures exact fields, session, host identity, ticket version, expiry, optional correlation ID, and optional idempotency key. Reusing the same session/key with the same payload returns the original proposal. Reusing it for changed fields is rejected.

Approval occurs under `BEGIN IMMEDIATE`. The controller checks PENDING state, session, expiry, ticket version, and authorization before inserting the note and incrementing the ticket version. The proposal state and audit event are written in the same transaction. A repeated decision without a matching decision key is rejected. A retry with the same decision key/outcome returns the original audit ID without applying another note.

The approval API uses a service bearer token for proposal reads and error persistence. Remote decisions require a separate individual bearer credential mapped to an identity by the server plus an explicit enable flag. Request JSON and `X-SupportOps-Approver` cannot establish identity. Remote decisions remain disabled by default, and the trusted CLI is the recommended MVP path.
