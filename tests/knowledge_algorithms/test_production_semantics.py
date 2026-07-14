from pathlib import Path

from backend.knowledge_algorithms.ka_09_evidence_validation import run as run_ka009
from backend.knowledge_algorithms.production_catalog import load_production_catalog


def test_empty_evidence_is_insufficient_not_successful_validation():
    result = run_ka009({"evidence": [], "query": "What supports this claim?"})

    assert result["success"] is False
    assert result["status"] == "insufficient_evidence"


def test_production_enabled_algorithms_contain_no_unseeded_random_calls():
    catalog = load_production_catalog()
    for entry in catalog.values():
        if not entry.production_enabled:
            continue
        source = Path(*entry.implementation.rsplit(".", 1)[0].split(".")).with_suffix(".py")
        text = source.read_text(encoding="utf-8")
        assert "random." not in text, entry.ka_id
