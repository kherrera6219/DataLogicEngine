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
    "L9-KA-001": (
        {
            "trace": {
                f"layer{number}": {"output": {"status": "completed"}}
                for number in range(1, 9)
            },
            "layers": list(range(1, 9)),
        },
        lambda row: row["trace_complete"] is True,
    ),
    "L9-KA-002": (
        {
            "original_query": "Validate deployment control 42",
            "final_solution": "Validate deployment control 42 with tests",
        },
        lambda row: row["measured"] is True
        and row["numeric_facts_preserved"] is True,
    ),
    "L9-KA-003": (
        {
            "domain_confidences": [
                {"domain": "operations", "confidence": 0.98}
            ],
            "threshold": 0.95,
        },
        lambda row: row["measured"] is True and row["consensus"] is True,
    ),
    "L9-KA-004": (
        {
            "solution": {"overall_confidence": 0.98},
            "trace": {
                f"layer{number}": {"output": "ok"}
                for number in range(1, 9)
            },
        },
        lambda row: row["evaluation_score"] == 1.0,
    ),
    "L9-KA-005": (
        {"readiness": 0.7, "issues": []},
        lambda row: row["trigger_refinement"] is True,
    ),
    "L9-KA-006": (
        {
            "l8_confidence": 0.98,
            "trace_integrity": 1.0,
            "belief_alignment": 1.0,
            "meta_evaluation": 1.0,
        },
        lambda row: row["status"] == "measured"
        and row["measurement_coverage"] > 0,
    ),
    "L9-KA-007": (
        {
            "iteration": 0,
            "max_iterations": 1,
            "dependency_results": {
                "L9-KA-005": {"trigger_refinement": True}
            },
        },
        lambda row: row["continue"] is True and row["remaining"] == 1,
    ),
    "L10-KA-001": (
        {"content": "alpha beta gamma delta"},
        lambda row: row["token_count"] == 4 and row["entropy_score"] > 0,
    ),
    "L10-KA-002": (
        {"content": "I can modify my own instructions"},
        lambda row: row["awareness_detected"] is True,
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
    "L10-KA-004": (
        {"content": "hide evidence to evade compliance"},
        lambda row: row["passed"] is False and bool(row["violations"]),
    ),
    "L10-KA-007": (
        {
            "request_id": "invariant",
            "risk_domain": "legal",
            "confidence": 0.99,
            "consequential_decision": True,
        },
        lambda row: row["escalation_required"] is True
        and row["reviews_dispatched"] == 0,
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
