"""Individually named semantic proofs for the active CP19-K KA batches."""

from __future__ import annotations

from backend.knowledge_algorithms.contracts import (
    KAExecutionContext,
    KAExecutionMode,
    KAExecutionRequest,
)
from backend.knowledge_algorithms.controller import CanonicalKAController
from backend.knowledge_algorithms.manifest import load_manifest


def _execute(canonical_id: str, payload: dict):
    controller = CanonicalKAController()
    return controller.execute(
        KAExecutionRequest(
            ka_id=canonical_id,
            input=payload,
            context=KAExecutionContext(
                request_id=f"cp19k-semantic-{canonical_id.lower()}",
                run_id=f"cp19k-semantic-run-{canonical_id.lower()}",
                workflow="cp19_k_semantic_qualification",
                layer="L1",
            ),
            mode=KAExecutionMode.PRODUCTION,
        )
    )


def _assert_pure_bounded_result(canonical_id: str, result) -> None:
    definition = load_manifest().entries[canonical_id]

    assert result.success
    assert result.canonical_id == canonical_id
    assert result.manifest_version == load_manifest().manifest_version
    assert result.trace_id
    assert result.duration_ms <= definition.contract.performance_budget_ms
    assert result.effects == []
    assert definition.integration.effect_port is None
    assert definition.contract.limitations


def test_ka_001_semantic_contract():
    first = _execute(
        "KA-001",
        {"query": "Research production release readiness evidence"},
    )
    second = _execute(
        "KA-001",
        {"query": "Research production release readiness evidence"},
    )

    _assert_pure_bounded_result("KA-001", first)
    assert first.output == second.output
    assert first.output["strategy"] == "research"
    assert [task["id"] for task in first.output["tasks"]] == [
        "t1",
        "t2",
        "t3",
        "t4",
        "t5",
    ]
    assert first.output["graph"] == {
        "t1": [],
        "t2": ["t1"],
        "t3": ["t2"],
        "t4": ["t3"],
        "t5": ["t4"],
    }


def test_ka_004_semantic_contract():
    normalized = _execute(
        "KA-004",
        {"query": "  <b>Assess the control boundary</b>  "},
    )
    rejected = _execute(
        "KA-004",
        {"query": "DROP TABLE production_records"},
    )

    _assert_pure_bounded_result("KA-004", normalized)
    _assert_pure_bounded_result("KA-004", rejected)
    assert normalized.output["is_valid"] is True
    assert normalized.output["normalized_query"] == "Assess the control boundary"
    assert rejected.output["is_valid"] is False
    assert "blacklisted pattern" in rejected.output["reason"]


def test_ka_005_semantic_contract():
    technical = _execute(
        "KA-005",
        {"query": "Debug the API database error"},
    )
    repeated = _execute(
        "KA-005",
        {"query": "Debug the API database error"},
    )

    _assert_pure_bounded_result("KA-005", technical)
    assert technical.output == repeated.output
    assert technical.output["category"] == "TECHNICAL"
    assert technical.output["suggested_tier"] == "moderate"
    assert technical.output["metadata"]["sdk_response"] == {}


def test_ka_061_semantic_contract():
    safe = _execute("KA-061", {"query": "Assess the control boundary"})
    blocked = _execute("KA-061", {"query": "DROP DATABASE production"})

    _assert_pure_bounded_result("KA-061", safe)
    _assert_pure_bounded_result("KA-061", blocked)
    assert safe.output["blocked"] is False
    assert safe.output["sanitized_query"] == "Assess the control boundary"
    assert blocked.output["blocked"] is True
    assert blocked.output["veto"] is True
    assert blocked.output["sanitized_query"] == "[FILTERED]"
    assert blocked.output["threats"]


def test_ka_113_semantic_contract():
    payload = {
        "query": "<b>short input</b>",
        "dependency_results": {
            "KA-004": {
                "is_valid": True,
                "normalized_query": (
                    "Compare maybe whether an SQL API encryption architecture "
                    "might be preferable versus another design, but explain "
                    "the ambiguous trade-off under uncertain constraints."
                ),
            },
            "KA-005": {"suggested_tier": "moderate"},
        },
    }
    routed = _execute("KA-113", payload)
    repeated = _execute("KA-113", payload)

    _assert_pure_bounded_result("KA-113", routed)
    assert routed.output == repeated.output
    assert routed.output["complexity_tier"] == "high"
    assert routed.output["target_pipeline"] == "deep_recursive_pipeline"
    assert routed.output["dependency_routing"] == {
        "normalized_query_consumed": True,
        "classification_tier": "moderate",
    }
