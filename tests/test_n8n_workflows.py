from __future__ import annotations

import json
import runpy
from pathlib import Path

WORKFLOW_DIR = Path(__file__).parents[1] / "n8n" / "workflows"
EXPECTED = {
    "01-supportops-main-chat.json",
    "02-ticket-analysis.json",
    "03-knowledge-retrieval.json",
    "04-incident-diagnosis.json",
    "05-approval-request.json",
    "06-ticket-decision.json",
    "07-error-monitoring.json",
}


def load_workflows() -> dict[str, dict]:
    return {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in WORKFLOW_DIR.glob("*.json")
    }


def test_workflow_json_and_graph_integrity() -> None:
    workflows = load_workflows()
    assert set(workflows) == EXPECTED
    for filename, workflow in workflows.items():
        assert workflow["name"].startswith("SupportOps")
        assert workflow["active"] is False
        assert workflow["id"]
        assert workflow["meta"]["supportopsTargetN8n"] == "2.45.7"
        names = {node["name"] for node in workflow["nodes"]}
        ids = [node["id"] for node in workflow["nodes"]]
        assert len(ids) == len(set(ids)), filename
        for source, outputs in workflow["connections"].items():
            assert source in names, filename
            for connection_groups in outputs.values():
                for group in connection_groups:
                    for connection in group:
                        assert connection["node"] in names, filename


def test_required_n8n_nodes_and_mcp_roles() -> None:
    workflows = load_workflows()
    main_types = {node["type"] for node in workflows["01-supportops-main-chat.json"]["nodes"]}
    assert "@n8n/n8n-nodes-langchain.chatTrigger" in main_types
    assert "@n8n/n8n-nodes-langchain.agent" in main_types
    assert "@n8n/n8n-nodes-langchain.lmChatOpenAi" in main_types
    assert sum(node_type.endswith(".mcpClientTool") for node_type in main_types) == 1
    main_nodes = workflows["01-supportops-main-chat.json"]["nodes"]
    assert sum(node["type"].endswith(".mcpClientTool") for node in main_nodes) == 2

    for filename in ("02-ticket-analysis.json", "03-knowledge-retrieval.json"):
        types = {node["type"] for node in workflows[filename]["nodes"]}
        assert "@n8n/n8n-nodes-langchain.mcpClient" in types
        assert "@n8n/n8n-nodes-langchain.agent" not in types

    decision_types = {node["type"] for node in workflows["06-ticket-decision.json"]["nodes"]}
    assert "n8n-nodes-base.httpRequest" in decision_types
    assert not any(node_type.endswith(".mcpClientTool") for node_type in decision_types)


def test_exports_contain_no_credentials_or_secrets() -> None:
    for path in WORKFLOW_DIR.glob("*.json"):
        raw = path.read_text(encoding="utf-8")
        lowered = raw.lower()
        assert '"credentials"' not in lowered
        assert "openai_api_key" not in lowered
        assert "sk-" not in lowered
        assert "supportops_mcp_bearer_token" not in lowered
        assert "supportops_approval_api_token" not in lowered


def test_agent_never_receives_approval_capabilities() -> None:
    main = load_workflows()["01-supportops-main-chat.json"]
    tool_nodes = [node for node in main["nodes"] if node["type"].endswith(".mcpClientTool")]
    exposed = {tool for node in tool_nodes for tool in node["parameters"].get("includeTools", [])}
    assert "prepare_ticket_update" in exposed
    assert not exposed.intersection(
        {"approve_ticket_update", "reject_ticket_update", "execute_sql", "run_shell_command"}
    )


def test_v21_trust_boundaries_and_actual_mcp_output_shape() -> None:
    workflows = load_workflows()
    diagnosis = json.dumps(workflows["04-incident-diagnosis.json"]).lower()
    approval_request = json.dumps(workflows["05-approval-request.json"]).lower()
    decision = json.dumps(workflows["06-ticket-decision.json"]).lower()
    errors = json.dumps(workflows["07-error-monitoring.json"]).lower()

    assert "structuredcontent?.title" in diagnosis
    assert "remote_application_allowed:false" in approval_request
    assert "x-supportops-approver" not in decision
    assert "$json.approver" not in decision
    assert "individual api credential" in decision
    assert "/events/errors" in errors
    assert "safe_message" not in errors


def test_standalone_validator_accepts_all_exports() -> None:
    namespace = runpy.run_path(str(WORKFLOW_DIR.parent / "tests" / "validate_workflows.py"))
    for path in WORKFLOW_DIR.glob("*.json"):
        namespace["validate_workflow"](path)
