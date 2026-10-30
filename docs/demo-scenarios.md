# Reproducible demo scenarios

1. Ticket analysis: ask `Analyze ticket INC-1042.` Expect `get_ticket`, observed facts, source `INC-1042`, and no mutation.
2. Knowledge retrieval: ask `What is the procedure for an Outlook sending issue?` Expect lexical search/retrieval and source `outlook-send-failure.md`.
3. Cross-server reasoning: ask `Analyze INC-1042 and recommend troubleshooting steps using the knowledge base.` Expect calls to both servers and separated facts/hypotheses.
4. Human approval: ask the agent to prepare a note, inspect `supportops proposals`, then run `supportops approve <id>` and confirm. Expect one note/version change and an audit event.
5. Rejection: prepare another proposal, run `supportops reject <id>`, and confirm. Expect no ticket change and a rejection audit event.

Run approval on an already handled ID to verify single use. The escalation procedure contains an explicit fictional hostile-instruction warning; tests ensure it is returned as untrusted source data and never becomes an approval path.

