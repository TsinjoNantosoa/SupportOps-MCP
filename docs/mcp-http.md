# MCP Streamable HTTP

Set `SUPPORTOPS_MCP_TRANSPORT=streamable-http`, then start each normal server entrypoint. Ticketing defaults to `127.0.0.1:8001/mcp`; Knowledge defaults to `127.0.0.1:8002/mcp`. Stdio remains the default when the variable is absent.

The implementation uses MCP Python SDK 2.3.0 `streamable_http_app()` with stateless JSON responses, a 1 MiB default body limit, five-minute idle timeout, 100-session cap, DNS-rebinding protection, and explicit Host/Origin allowlists. `SUPPORTOPS_MCP_BEARER_TOKEN` adds constant-time bearer verification.

Local unauthenticated mode must stay bound to loopback. For another container, bind `0.0.0.0`, place services on a private Docker network, include only required service hostnames, and enable bearer authentication. For any external network, add TLS, verifiable identity, scoped authorization, rate limits, and monitoring; a shared token is not sufficient for sensitive human approval.
