# SupportOps MCP V2.2 — portfolio summary

SupportOps is a local, fictional IT-helpdesk copilot demonstrating how n8n can orchestrate an OpenAI agent with two Python MCP servers. Ticketing and knowledge retrieval stay deterministic; Python remains the authority for validation, SQLite transactions, human approval and audit.

The portfolio story is deliberately honest: MCP ticket/procedure retrieval, proposal creation, local approval, idempotency, version checks, expiry and audit are tested. OpenAI live execution, browser Wait/resume and remote approval are documented as **not verified** until a real n8n credential and identity flow are configured.

Stack: Python, MCP, Streamable HTTP, n8n, OpenAI-compatible tool calling, SQLite, Docker Compose, pytest and Ruff.

The system is not connected to real customers, Microsoft 365, Windows, networks or production ticketing. Its value is the safety boundary: the model can recommend and prepare, but a trusted human controller alone can apply a change.
