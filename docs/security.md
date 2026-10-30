# Security summary

MCP tools use least privilege, typed validation, parameterized SQL, allowlisted files, bounded results, and structured errors. HTTP uses loopback defaults, SDK DNS-rebinding protection, explicit Hosts/Origins, body/session limits, and optional bearer authentication. Tool results remain untrusted model context.

Proposal and decision retries are idempotent only when their exact keys and payload/outcome match. Ticket version predicates, `BEGIN IMMEDIATE`, single-use states, and same-transaction audit prevent duplicate or stale application. The LLM receives no approval capability.

Remote approval is disabled by default. The optional isolated-demo API does not replace enterprise identity. Local subprocesses are not OS sandboxes, bearer tokens require secret management and TLS outside loopback, SQLite is single-host storage, and n8n execution data must be configured to avoid retaining sensitive prompts.
