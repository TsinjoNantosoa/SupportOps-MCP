from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPError


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def http_server(
    module: str,
    tmp_path: Path,
    port: int,
    *,
    token: str | None = None,
    max_body_size: int = 1_048_576,
) -> Iterator[str]:
    env = os.environ.copy()
    env.update(
        {
            "SUPPORTOPS_MCP_TRANSPORT": "streamable-http",
            "SUPPORTOPS_DB_PATH": str(tmp_path / "http.db"),
            "SUPPORTOPS_TICKETING_HOST": "127.0.0.1",
            "SUPPORTOPS_TICKETING_PORT": str(port),
            "SUPPORTOPS_KNOWLEDGE_HOST": "127.0.0.1",
            "SUPPORTOPS_KNOWLEDGE_PORT": str(port),
            "SUPPORTOPS_ALLOWED_HOSTS": f"127.0.0.1:{port},localhost:{port}",
            "SUPPORTOPS_ALLOWED_ORIGINS": "http://localhost:5678",
            "SUPPORTOPS_MCP_BEARER_TOKEN": token or "",
            "SUPPORTOPS_MAX_REQUEST_BODY_SIZE": str(max_body_size),
        }
    )
    process = subprocess.Popen(
        [sys.executable, "-m", module],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"MCP server exited with code {process.returncode}")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise TimeoutError("MCP HTTP server did not start")
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("module", "expected_tool"),
    [
        ("supportops.servers.ticketing_server", "get_ticket"),
        ("supportops.servers.knowledge_server", "get_procedure"),
    ],
)
async def test_streamable_http_discovery(module, expected_tool, tmp_path) -> None:
    port = free_port()
    with http_server(module, tmp_path, port) as url:
        async with Client(url, read_timeout_seconds=10) as client:
            tools = await client.list_tools()
            assert expected_tool in {tool.name for tool in tools.tools}


@pytest.mark.asyncio
async def test_streamable_http_bearer_authentication(tmp_path) -> None:
    port = free_port()
    with http_server(
        "supportops.servers.ticketing_server", tmp_path, port, token="test-secret"
    ) as url:
        request = Request(url, data=b"{}", method="POST")
        with pytest.raises(HTTPError) as denied:
            urlopen(request, timeout=3)
        assert denied.value.code == 401

        wrong = Request(
            url,
            data=b"{}",
            method="POST",
            headers={"Authorization": "Bearer wrong-secret"},
        )
        with pytest.raises(HTTPError) as invalid:
            urlopen(wrong, timeout=3)
        assert invalid.value.code == 401

        async with httpx2.AsyncClient(headers={"Authorization": "Bearer test-secret"}) as http:
            transport = streamable_http_client(url, http_client=http)
            async with Client(transport, read_timeout_seconds=10) as client:
                result = await client.call_tool("get_ticket", {"ticket_id": "INC-1042"})
                assert result.structured_content["ticket_id"] == "INC-1042"


def test_streamable_http_rejects_host_origin_and_oversized_body(tmp_path) -> None:
    port = free_port()
    with http_server(
        "supportops.servers.ticketing_server",
        tmp_path,
        port,
        token="test-secret",
        max_body_size=128,
    ) as url:
        base_headers = {
            "Authorization": "Bearer test-secret",
            "Content-Type": "application/json",
        }
        bad_host = Request(
            url,
            data=b"{}",
            method="POST",
            headers={**base_headers, "Host": "attacker.invalid"},
        )
        with pytest.raises(HTTPError) as host_denied:
            urlopen(bad_host, timeout=3)
        assert host_denied.value.code in {400, 403, 421}

        bad_origin = Request(
            url,
            data=b"{}",
            method="POST",
            headers={**base_headers, "Origin": "https://attacker.invalid"},
        )
        with pytest.raises(HTTPError) as origin_denied:
            urlopen(bad_origin, timeout=3)
        assert origin_denied.value.code in {400, 403, 421}

        oversized = Request(url, data=b"x" * 256, method="POST", headers=base_headers)
        with pytest.raises(HTTPError) as too_large:
            urlopen(oversized, timeout=3)
        assert too_large.value.code == 413


@pytest.mark.asyncio
async def test_unknown_knowledge_resource_over_http_is_structured_error(tmp_path) -> None:
    port = free_port()
    with http_server("supportops.servers.knowledge_server", tmp_path, port) as url:
        async with Client(url, read_timeout_seconds=10) as client:
            with pytest.raises(MCPError):
                await client.read_resource("supportops://knowledge/not-allowlisted")
