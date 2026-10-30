# Testing

Executed successfully in this environment:

```text
uv run pytest                         28 passed
uv run ruff check .                  All checks passed
uv run python n8n/tests/validate_workflows.py
docker compose config --quiet
docker compose build
docker compose up -d
```

The Docker test observed three healthy services, discovered both MCP tool lists, retrieved `INC-1042`, found one Outlook procedure, and confirmed remote approval was disabled. The isolated test stack and volume were removed afterward.

No `OPENAI_API_KEY` was present, so live model behavior is **NON VÉRIFIÉ**. A temporary n8n 2.45.7 CLI installation timed out, so workflow import and runtime execution are also **NON VÉRIFIÉ**. Static tests validate JSON, graph references, node roles, tool separation, and absence of exported credentials.
