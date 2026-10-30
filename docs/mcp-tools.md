# MCP tool inventory

## supportops-ticketing

- `list_tickets(status?, priority?, limit=20)` returns bounded fictional summaries.
- `get_ticket(ticket_id)` returns the structured ticket, notes, and version.
- `search_tickets(query, limit=20)` performs parameterized lexical SQL search.
- `prepare_ticket_update(ticket_id, proposed_note, reason, proposed_status?, idempotency_key?, correlation_id?)` creates or safely reuses a PENDING proposal. It never modifies a ticket.

## supportops-knowledge

- `search_knowledge(query, limit=5)` returns deterministic ranked matches and source references.
- `get_procedure(procedure_id)` returns one structured allowlisted procedure.
- `supportops://knowledge/{procedure_id}` is a read-only resource template.

No MCP tool approves/rejects proposals, executes SQL or shell commands, or reads caller-supplied paths.
