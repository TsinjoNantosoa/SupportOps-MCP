from __future__ import annotations

import hmac
from collections.abc import Callable

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from supportops.config import Settings


class BearerTokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, token: str) -> None:
        super().__init__(app)
        self.token = token

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {self.token}"
        if not hmac.compare_digest(supplied, expected):
            return JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)


def run_server(mcp: MCPServer, settings: Settings, *, host: str, port: int) -> None:
    if settings.mcp_transport == "stdio":
        mcp.run(transport="stdio")
        return
    if settings.mcp_transport != "streamable-http":
        raise ValueError("SUPPORTOPS_MCP_TRANSPORT must be 'stdio' or 'streamable-http'")

    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(settings.allowed_hosts),
        allowed_origins=list(settings.allowed_origins),
    )
    app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        max_request_body_size=settings.max_request_body_size,
        session_idle_timeout=300,
        max_sessions=100,
        transport_security=security,
        host=host,
    )
    if settings.mcp_bearer_token:
        app.add_middleware(BearerTokenMiddleware, token=settings.mcp_bearer_token)
    uvicorn.run(app, host=host, port=port, log_level="info")
