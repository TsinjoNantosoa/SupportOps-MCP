# SupportOps n8n workflows

These seven exports target **n8n 2.45.7**. Node names, versions, parameters, and the actual MCP Client `structuredContent` output were checked against the packaged implementations on 2026-10-30. All seven files were imported and listed in an isolated n8n 2.45.7 database. The runtime fixture under `tests/runtime/` then called both MCP servers successfully from n8n.

## Import order

Import every file in `workflows/` from the n8n UI. Configure credentials before activation:

1. An OpenAI credential and a tool-capable model actually available to that credential.
2. Optional MCP bearer credentials if `SUPPORTOPS_MCP_BEARER_TOKEN` is enabled.
3. A service HTTP Header Auth credential containing `Authorization: Bearer <SUPPORTOPS_APPROVAL_API_TOKEN>` for workflows 05 and 07.
4. A distinct individual credential containing `Authorization: Bearer <individual-token>` for workflow 06; the API maps it to the approver identity.
5. Header authentication on workflow 06's decision webhook.

The exports contain no credential IDs or secrets. Their Docker-network endpoints are `supportops-ticketing:8001`, `supportops-knowledge:8002`, and `supportops-approval:8010`. Replace them with `localhost` for n8n running directly on the host, or `host.docker.internal` when n8n is in a container and SupportOps runs on the host.

## Safety state

Remote ticket decisions are disabled by default. A Wait response in workflow 05 records review intent only and is never authorization. Workflow 06 rejects an `approver` supplied in JSON; identity comes from `SUPPORTOPS_APPROVER_TOKENS_JSON` and its individual credential. Keep the local CLI as the trusted path until this flow has been validated and remote approval explicitly authorized.

The `gpt-5-mini` value in the two OpenAI nodes is the official n8n 2.45.7 node default, not a claim that the model is available to your account. Select an accessible tool-capable model before activation.

Run static validation with:

```bash
uv run python n8n/tests/validate_workflows.py
uv run pytest tests/test_n8n_workflows.py
```
