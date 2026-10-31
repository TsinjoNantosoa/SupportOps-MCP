from __future__ import annotations

import json
from pathlib import Path
from typing import Any

WORKFLOW_DIR = Path(__file__).parents[1] / "workflows"
EXPECTED_FILES = {
    "01-supportops-main-chat.json",
    "02-ticket-analysis.json",
    "03-knowledge-retrieval.json",
    "04-incident-diagnosis.json",
    "05-approval-request.json",
    "06-ticket-decision.json",
    "07-error-monitoring.json",
}
SUPPORTED_NODE_VERSIONS = {
    "@n8n/n8n-nodes-langchain.agent": {3.1},
    "@n8n/n8n-nodes-langchain.chatTrigger": {1.5},
    "@n8n/n8n-nodes-langchain.lmChatOpenAi": {1.3},
    "@n8n/n8n-nodes-langchain.mcpClient": {1.1},
    "@n8n/n8n-nodes-langchain.mcpClientTool": {1.4},
    "@n8n/n8n-nodes-langchain.memoryBufferWindow": {1.4},
    "@n8n/n8n-nodes-langchain.outputParserStructured": {1.3},
    "n8n-nodes-base.code": {2},
    "n8n-nodes-base.errorTrigger": {1},
    "n8n-nodes-base.executeWorkflowTrigger": {1.1},
    "n8n-nodes-base.httpRequest": {4.4},
    "n8n-nodes-base.if": {2.3},
    "n8n-nodes-base.respondToWebhook": {1.5},
    "n8n-nodes-base.wait": {1.1},
    "n8n-nodes-base.webhook": {2.1},
}


def _fail(path: Path, message: str) -> None:
    raise ValueError(f"{path.name}: {message}")


def _all_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _all_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _all_strings(nested)


def validate_workflow(path: Path) -> None:
    workflow = json.loads(path.read_text(encoding="utf-8"))
    if workflow.get("active") is not False:
        _fail(path, "exports must be inactive")
    if workflow.get("meta", {}).get("supportopsTargetN8n") != "2.45.7":
        _fail(path, "target n8n version must be 2.45.7")
    if not workflow.get("id") or not workflow.get("versionId"):
        _fail(path, "stable workflow id and versionId are required")

    nodes = workflow.get("nodes", [])
    names = [node.get("name") for node in nodes]
    ids = [node.get("id") for node in nodes]
    if len(names) != len(set(names)) or len(ids) != len(set(ids)):
        _fail(path, "node names and ids must be unique")

    for node in nodes:
        node_type = node.get("type")
        version = node.get("typeVersion")
        if version not in SUPPORTED_NODE_VERSIONS.get(node_type, set()):
            _fail(path, f"unsupported node type/version {node_type}@{version}")
        params = node.get("parameters", {})
        if node_type.endswith((".mcpClient", ".mcpClientTool")):
            if params.get("serverTransport") != "httpStreamable":
                _fail(path, f"{node['name']} must use Streamable HTTP")
            endpoint = params.get("endpointUrl", "")
            if endpoint not in {
                "http://supportops-ticketing:8001/mcp",
                "http://supportops-knowledge:8002/mcp",
            }:
                _fail(path, f"{node['name']} uses an unexpected MCP endpoint")
            timeout = params.get("options", {}).get("timeout")
            if not isinstance(timeout, int) or not 1 <= timeout <= 60_000:
                _fail(path, f"{node['name']} needs a bounded timeout")

    name_set = set(names)
    for source, outputs in workflow.get("connections", {}).items():
        if source not in name_set:
            _fail(path, f"unknown source node {source}")
        for groups in outputs.values():
            for group in groups:
                for connection in group:
                    if connection.get("node") not in name_set:
                        _fail(path, f"unknown target node {connection.get('node')}")

    raw = path.read_text(encoding="utf-8").lower()
    forbidden = (
        '"credentials"',
        "openai_api_key",
        "sk-",
        "supportops_mcp_bearer_token",
        "supportops_approval_api_token",
        "x-supportops-approver",
        "$json.approver",
    )
    for marker in forbidden:
        if marker in raw:
            _fail(path, f"forbidden credential or trust marker: {marker}")
    if any("REPLACE_" in value for value in _all_strings(workflow)):
        _fail(path, "unresolved placeholder")

    if path.name == "04-incident-diagnosis.json" and "structuredcontent?.title" not in raw:
        _fail(path, "diagnosis must parse the actual MCP structuredContent output")
    if path.name == "05-approval-request.json" and "remote_application_allowed:false" not in raw:
        _fail(path, "Wait review must not authorize remote application")
    if path.name == "06-ticket-decision.json":
        webhook = next(node for node in nodes if node["type"] == "n8n-nodes-base.webhook")
        if webhook["parameters"].get("authentication") != "headerAuth":
            _fail(path, "decision webhook must require authentication")
        if "individual api credential" not in raw:
            _fail(path, "decision identity must be derived from an individual credential")
    if path.name == "07-error-monitoring.json" and (
        "/events/errors" not in raw or "safe_message" in raw
    ):
        _fail(path, "errors must be persisted without raw messages")


def main() -> None:
    files = sorted(WORKFLOW_DIR.glob("*.json"))
    if {path.name for path in files} != EXPECTED_FILES:
        raise SystemExit("Workflow file set does not match the V2.2 contract")
    try:
        for path in files:
            validate_workflow(path)
            print(f"valid: {path.name}")
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
