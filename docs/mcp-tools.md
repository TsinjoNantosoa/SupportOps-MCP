# MCP inventory

## supportops-ticketing

- `list_tickets(status?, priority?, limit=20)`: bounded summary listing.
- `get_ticket(ticket_id)`: full structured ticket or model-readable tool error.
- `search_tickets(query, limit=20)`: parameterized title/description search.
- `prepare_ticket_update(ticket_id, proposed_note, reason, proposed_status?)`: validates transition and persists a session-bound, expiring pending proposal without changing the ticket.

## supportops-knowledge

- `search_knowledge(query, limit=5)`: deterministic lexical ranking with source references.
- `get_procedure(procedure_id)`: structured allowlisted procedure.
- Resource template `supportops://knowledge/{procedure_id}`: read-only Markdown.

No tool executes shell commands, accepts SQL, reads arbitrary paths, or approves proposals.

