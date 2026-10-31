# Testing

The current V2.2 audit ran:

```text
python -m pytest                       38 passed
ruff check .                           All checks passed
python n8n/tests/validate_workflows.py 7 valid workflows
docker compose config --quiet          passed
docker compose runtime                 3/3 healthy
```

The Python E2E test and Docker stack discover both MCP tool lists, retrieve `INC-1042`, find the Outlook procedure, create a PENDING proposal, apply a trusted local decision and verify audit/idempotency. A Docker MCP call was also executed directly against both published endpoints.

No `OPENAI_API_KEY` was present, so live model behavior is **NOT VERIFIED**. The seven workflows were imported into the isolated n8n 2.45.7 instance at `http://localhost:5681`; AI workflow execution, Wait/resume, and remotely enabled approval remain **NOT VERIFIED** in n8n runtime.
