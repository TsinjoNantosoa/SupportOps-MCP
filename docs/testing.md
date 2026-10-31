# Testing

Executed successfully in this environment:

```text
uv run pytest                         35 passed
uv run ruff check .                  All checks passed
uv run python n8n/tests/validate_workflows.py
docker compose config --quiet
docker compose build
docker compose up -d
```

The Docker test observed three healthy services, discovered both MCP tool lists, retrieved `INC-1042`, found the Outlook procedure, and confirmed remote approval was disabled. n8n 2.45.7 imported all seven exports. A runtime fixture executed MCP Client nodes against both services and returned `status=PASS`, `ticket_id=INC-1042`, and `source_reference=outlook-send-failure.md`. Isolated stacks and volumes were removed afterward.

No `OPENAI_API_KEY` was present, so live model behavior is **NON VÉRIFIÉ**. The production exports were imported, but only the deterministic MCP runtime fixture was executed end to end. AI workflows, Wait/resume, and remotely enabled approval remain **NON VÉRIFIÉS** in n8n runtime.
