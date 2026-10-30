# V2 repository audit

Audit date: 2026-10-30. Baseline: commit `961bad2`.

## Verified baseline

- `uv` environment resolves MCP 2.3.0 and OpenAI Agents SDK 0.24.0.
- Original regression suite: 14/14 passing; Ruff passing.
- Both MCP servers discover and invoke tools in memory and via a real stdio subprocess.
- Ticket retrieval, lexical knowledge search, resource reads, proposal creation, approval, rejection, expiry, stale-version detection, single-use decisions, transactions, and audit were exercised.
- Procedure identifiers are allowlisted and SQL queries are parameterized.

## Confirmed defects and limitations

- No Streamable HTTP transport or n8n exports existed.
- Session and user identity came from local environment values.
- The CLI recreated the Python agent for each message and did not retain SDK conversation state.
- Proposal creation had no business idempotency key.
- Remote approval was unavailable; the CLI was the only trusted controller.
- The knowledge path was fixed to the repository layout.
- The prior default model string was not guaranteed to be available.
- Agent tests checked policy/configuration but made no live OpenAI call.
- SQLite cannot be shared safely across separate hosts.

## Security risks considered

MCP output is prompt-injection capable. Local stdio does not sandbox a process. Unauthenticated HTTP must remain localhost/private-network only. A shared bearer token is service authentication, not strong individual approver identity. n8n retries can duplicate effects unless business idempotency is enforced below the workflow layer.

## V2 decisions

- Preserve stdio and add configurable Streamable HTTP with SDK Host/Origin validation, body/session limits, and optional bearer middleware.
- Add additive SQLite migrations rather than resetting existing data.
- Scope proposal idempotency to session plus key; reject key reuse with a changed payload.
- Permit a decision replay only when the same decision key and outcome are repeated; ordinary double decisions remain conflicts.
- Keep remote approval disabled by default. Add a bearer-protected API for proposal review and an opt-in isolated-demo decision path; retain CLI approval as the safe default.
- Target n8n 2.45.7 and validate exports statically. Mark runtime import and OpenAI execution NON VÉRIFIÉ.

## Post-change verification

- 28 pytest tests pass, including both HTTP servers, bearer denial, additive migration, audit redaction, idempotence, approval API authorization, n8n graph checks, stdio, and original regression coverage.
- Docker Compose built three images. All three services became healthy. Host clients discovered both MCP servers and called real tools.
- The attempted temporary n8n CLI installation timed out after six minutes; no workflow import or execution is claimed.
