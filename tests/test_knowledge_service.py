from __future__ import annotations

import pytest

from supportops.services.knowledge_service import KnowledgeService


def test_search_get_and_limit(knowledge_dir) -> None:
    service = KnowledgeService(knowledge_dir)
    results = service.search("network DNS connectivity", limit=1)
    assert len(results) == 1
    assert results[0]["source_reference"].endswith(".md")
    procedure = service.get("dns-diagnostics")
    assert procedure.diagnostic_steps
    assert procedure.source_reference == "dns-diagnostics.md"


def test_missing_and_path_traversal_refused(knowledge_dir) -> None:
    service = KnowledgeService(knowledge_dir)
    with pytest.raises(LookupError):
        service.get("missing")
    with pytest.raises(LookupError):
        service.get("../../etc/passwd")


def test_hostile_instruction_is_returned_only_as_source_data(knowledge_dir) -> None:
    service = KnowledgeService(knowledge_dir)
    text = service.raw("ticket-escalation")
    assert "embedded instruction" in text
    assert "untrusted test data" in text
