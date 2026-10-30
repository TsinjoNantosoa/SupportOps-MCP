# Architecture

The CLI is the MCP host and security boundary. In demo mode it uses MCP Python SDK v2 `Client` with `StdioServerParameters`; in chat mode OpenAI Agents SDK uses two `MCPServerStdio` connections. Both launch independent Python processes and close them through async context managers.

The ticketing adapter delegates to a deterministic SQLite service. The knowledge adapter delegates to an allowlisted Markdown parser. Neither server calls the other. The agent may create a pending proposal, while only the CLI-held `ApprovalService` can commit it.

Tools are model-driven typed calls. Resources are host-driven reads by URI. Prompts are reusable user-selected templates; none are required here because trusted agent instructions are defined in the host.

