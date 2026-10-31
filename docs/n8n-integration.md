# n8n integration

The exports target n8n 2.45.7. `MCP Client Tool` 1.4 connects both servers to the AI Agent. Standalone `MCP Client` 1.1 performs deterministic ticket and knowledge calls. The main workflow uses Chat Trigger 1.5, AI Agent 3.1, OpenAI Chat Model 1.3, and Simple Memory 1.4.

Import the seven files in `n8n/workflows`. Configure an OpenAI credential and select a model actually listed for that credential. The bundled model value is an n8n node default only. If MCP bearer authentication is enabled, change both MCP node types from `None` to `Bearer Auth` and select the matching credential.

Workflow 05 retrieves exact proposal data from the trusted API and pauses at a Wait webhook. Workflow 06 accepts a separately authenticated human-decision webhook and calls the approval API. Remote decisions are disabled in Python by default; use the CLI unless the isolated-demo controls are intentionally enabled.

Static validation passed and all seven exports were imported into n8n 2.45.7. A runtime fixture called both MCP services from n8n and retrieved `INC-1042` plus the Outlook procedure. OpenAI output, browser Wait/resume, credential selection through the UI, and every production workflow path remain **NON VÉRIFIÉ**.
