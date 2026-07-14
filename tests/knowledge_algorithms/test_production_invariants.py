"""Semantic invariants for every production-enabled Knowledge Algorithm."""

from time import perf_counter

from backend.knowledge_algorithms.ka_master_controller import KAMasterController
from backend.knowledge_algorithms.production_catalog import load_production_catalog


FIXTURES = {
    "KA-001": ({"query": "Research encryption controls"}, lambda row: bool(row["tasks"])),
    "KA-004": ({"query": "  Assess control  "}, lambda row: row["is_valid"] is True),
    "KA-009": (
        {
            "query": "encryption control",
            "evidence": [
                {"source": "manual", "source_type": "document", "content": "encryption control"}
            ],
        },
        lambda row: row["overall_validity"] is True,
    ),
    "KA-024": (
        {"confidence": 0.9, "risk_score": 0.1},
        lambda row: row["status"] == "APPROVED",
    ),
    "KA-061": (
        {"query": "<script>alert('x')</script>"},
        lambda row: row["blocked"] is True and row["veto"] is True,
    ),
    "KA-074": (
        {"records": [{"id": 1}, "invalid"]},
        lambda row: row["validation_summary"]["invalid"] == 2
        and len(row["quarantined"]) == 2,
    ),
    "KA-113": (
        {"query": "Compare ambiguous regulatory encryption trade-offs"},
        lambda row: 0.0 <= row["complexity_score"] <= 1.0,
    ),
    "KA-117": (
        {"snapshot": {"nodes": [{"id": "a", "confidence": 1.0}], "edges": [{"source": "a", "target": "missing"}]}},
        lambda row: row["is_valid"] is False,
    ),
    "L10-KA-003": (
        {"content": "Email admin@example.com"},
        lambda row: row["redactions_found"] == 1 and "[REDACTED_EMAIL]" in row["redacted_content"],
    ),
    "L10-KA-005": (
        {"violations": [{"severity": "major"}]},
        lambda row: row["decision"] == "ESCALATE" and row["requires_human_signoff"] is True,
    ),
    "L10-KA-006": (
        {"confidence": 0.98},
        lambda row: row["decayed_confidence"] == 0.9604,
    ),
}


def _output(result):
    return result.get("output", result)


def test_every_production_enabled_ka_has_repeatable_semantic_invariant():
    controller = KAMasterController({})
    enabled = {
        ka_id: entry
        for ka_id, entry in load_production_catalog().items()
        if entry.production_enabled
    }

    assert set(FIXTURES) == set(enabled)
    for ka_id, (payload, invariant) in FIXTURES.items():
        started = perf_counter()
        first = controller.execute_algorithm(ka_id, dict(payload))
        second = controller.execute_algorithm(ka_id, dict(payload))
        duration_ms = (perf_counter() - started) * 1000
        assert _output(first) == _output(second), ka_id
        assert invariant(_output(first)), ka_id
        assert duration_ms <= enabled[ka_id].performance_budget_ms, ka_id
