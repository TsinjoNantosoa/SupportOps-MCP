# SupportOps n8n workflows

These seven exports target **n8n 2.45.7**. The node names, versions, and parameters were checked against the official `n8n`, `n8n-nodes-base`, and `@n8n/n8n-nodes-langchain` packages available on 2026-10-30. All files pass JSON and graph-integrity tests. Import into a running n8n instance remains **NON VÉRIFIÉ** in this environment because the temporary `npx n8n@2.45.7` installation timed out.

## Import order

Import every file in `workflows/` from the n8n UI. Configure credentials before activation:

1. An OpenAI credential and a tool-capable model actually available to that credential.
2. Optional MCP bearer credentials if `SUPPORTOPS_MCP_BEARER_TOKEN` is enabled.
3. An HTTP Header Auth credential containing `Authorization: Bearer <approval-token>` for workflows 05 and 06.
4. Header authentication on workflow 06's decision webhook.

The exports contain no credential IDs or secrets. Their Docker-network endpoints are `supportops-ticketing:8001`, `supportops-knowledge:8002`, and `supportops-approval:8010`. Replace them with `localhost` for n8n running directly on the host, or `host.docker.internal` when n8n is in a container and SupportOps runs on the host.

## Safety state

Remote ticket decisions are disabled by default. Workflow 05 can retrieve and present exact proposal fields after an approval API token is configured, but workflow 06 receives HTTP 403 until `SUPPORTOPS_REMOTE_APPROVAL_ENABLED=true` and an allowlisted approver are deliberately configured. The local CLI remains the default trusted decision path.

The `gpt-5-mini` value in the two OpenAI nodes is the official n8n 2.45.7 node default, not a claim that the model is available to your account. Select an accessible tool-capable model before activation.

Run static validation with:

```bash
uv run python n8n/tests/validate_workflows.py
uv run pytest tests/test_n8n_workflows.py
```
