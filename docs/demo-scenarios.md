# V2 demonstration scenarios

1. **Ticket analysis:** workflow 02 validates `INC-1042` and calls `get_ticket` with standalone MCP Client. No mutation.
2. **Knowledge retrieval:** workflow 03 searches `Outlook sending issue`, returns allowlisted references, and explicitly handles no match.
3. **Cross-server diagnosis:** workflow 04 calls both MCP servers, then validates a structured facts/hypotheses/checks/sources schema.
4. **Create proposal:** the main agent calls `prepare_ticket_update` with an n8n execution idempotency key. The ticket remains unchanged.
5. **Human approval:** workflow 05 presents exact fields. The trusted CLI, or deliberately enabled workflow 06, applies one atomic update and returns an audit ID.
6. **Human rejection:** the same review path records REJECTED and leaves the ticket unchanged.
7. **Security and reliability:** repeat a creation key, decision key, ordinary double approval, expired proposal, stale version, forged approver, prompt injection fixture, bearer denial, and unavailable MCP server.

The deterministic Python and Docker portions are tested. n8n UI import, OpenAI synthesis, Wait resume, and live end-to-end n8n execution remain **NON VÉRIFIÉ**.
