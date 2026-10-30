from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    workflow_dir = Path(__file__).parents[1] / "workflows"
    files = sorted(workflow_dir.glob("*.json"))
    if len(files) != 7:
        raise SystemExit(f"Expected 7 workflow exports, found {len(files)}")
    for path in files:
        workflow = json.loads(path.read_text(encoding="utf-8"))
        names = {node["name"] for node in workflow["nodes"]}
        for source, outputs in workflow["connections"].items():
            if source not in names:
                raise SystemExit(f"{path.name}: unknown source node {source}")
            for groups in outputs.values():
                for group in groups:
                    for connection in group:
                        if connection["node"] not in names:
                            raise SystemExit(
                                f"{path.name}: unknown target node {connection['node']}"
                            )
        print(f"valid: {path.name}")


if __name__ == "__main__":
    main()
