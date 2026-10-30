from __future__ import annotations

import re
from pathlib import Path

from supportops.models.procedure import Procedure

ALLOWED_PROCEDURES = {
    "outlook-send-failure": "outlook-send-failure.md",
    "network-troubleshooting": "network-troubleshooting.md",
    "dns-diagnostics": "dns-diagnostics.md",
    "printer-troubleshooting": "printer-troubleshooting.md",
    "microsoft365-mfa": "microsoft365-mfa.md",
    "ticket-escalation": "ticket-escalation.md",
}

TOKEN = re.compile(r"[a-z0-9]+")


class KnowledgeService:
    def __init__(self, knowledge_dir: Path) -> None:
        self.knowledge_dir = knowledge_dir.resolve()

    def _path_for(self, procedure_id: str) -> Path:
        filename = ALLOWED_PROCEDURES.get(procedure_id)
        if filename is None:
            raise LookupError(f"Procedure {procedure_id!r} is not in the allowlist")
        path = (self.knowledge_dir / filename).resolve()
        if path.parent != self.knowledge_dir:
            raise PermissionError("Knowledge path escaped the allowlisted directory")
        return path

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        query = query.strip()
        if not 2 <= len(query) <= 200:
            raise ValueError("query length must be between 2 and 200")
        if not 1 <= limit <= 10:
            raise ValueError("limit must be between 1 and 10")
        terms = set(TOKEN.findall(query.lower()))
        results: list[dict[str, object]] = []
        for procedure_id, filename in ALLOWED_PROCEDURES.items():
            text = self._path_for(procedure_id).read_text(encoding="utf-8")
            lowered = text.lower()
            title = text.splitlines()[0].removeprefix("# ").strip()
            score = sum(lowered.count(term) for term in terms)
            if score:
                excerpt = self._excerpt(text, terms)
                results.append(
                    {
                        "procedure_id": procedure_id,
                        "title": title,
                        "relevant_excerpt": excerpt,
                        "source_reference": filename,
                        "score": score,
                    }
                )
        return sorted(results, key=lambda item: (-int(item["score"]), str(item["procedure_id"])))[
            :limit
        ]

    def get(self, procedure_id: str) -> Procedure:
        path = self._path_for(procedure_id)
        text = path.read_text(encoding="utf-8")
        sections = self._sections(text)
        title = text.splitlines()[0].removeprefix("# ").strip()
        steps = [
            line.lstrip("0123456789.- ").strip()
            for line in sections.get("Diagnostic Steps", "").splitlines()
            if line.strip().startswith(tuple("0123456789-"))
        ]
        category = sections.get("Category", "General").strip()
        return Procedure(
            procedure_id=procedure_id,
            title=title,
            category=category,
            preconditions=sections.get("Preconditions", "").strip(),
            diagnostic_steps=steps,
            escalation_criteria=sections.get("Escalation Criteria", "").strip(),
            source_reference=path.name,
        )

    def raw(self, procedure_id: str) -> str:
        return self._path_for(procedure_id).read_text(encoding="utf-8")

    @staticmethod
    def _sections(text: str) -> dict[str, str]:
        parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
        return {
            parts[index].strip(): parts[index + 1].strip() for index in range(1, len(parts) - 1, 2)
        }

    @staticmethod
    def _excerpt(text: str, terms: set[str]) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        matching = [line for line in lines if any(term in line.lower() for term in terms)]
        return " ".join(matching[:3])[:500]
