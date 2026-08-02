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


def _assert_bounded_result(canonical_id: str, result) -> None:
    definition = load_manifest().entries[canonical_id]

    assert result.success
    assert result.canonical_id == canonical_id
    assert result.manifest_version == load_manifest().manifest_version
    assert result.trace_id
    assert result.duration_ms <= definition.contract.performance_budget_ms
    assert result.effects == []
    assert definition.contract.limitations


def _assert_pure_bounded_result(canonical_id: str, result) -> None:
    _assert_bounded_result(canonical_id, result)
    assert load_manifest().entries[canonical_id].integration.effect_port is None


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


def test_ka_032_semantic_contract():
    completed = _execute(
        "KA-032",
        {
            "pipeline": [
                {"ka_id": "KA-042"},
                {"ka_id": "KA-070", "depends_on": ["step_1"]},
            ],
            "simulation_state": {},
            "exit_criteria": {"min_completed": 2, "max_failures": 0},
        },
    )
    blocked = _execute(
        "KA-032",
        {
            "pipeline": [
                {"ka_id": "KA-070", "depends_on": ["missing_step"]},
            ],
            "simulation_state": {},
            "exit_criteria": {"min_completed": 1, "max_failures": 0},
        },
    )

    _assert_bounded_result("KA-032", completed)
    assert blocked.success is False
    assert blocked.duration_ms <= load_manifest().entries[
        "KA-032"
    ].contract.performance_budget_ms
    assert blocked.effects == []
    assert completed.output["final_status"] == "COMPLETED"
    assert completed.output["checkpoints_captured"] == 2
    assert blocked.state.value == "failed"
    assert blocked.error.code == "KA_EXECUTION_FAILED"
    assert blocked.output == {}


def test_ka_037_semantic_contract():
    normal = _execute(
        "KA-037",
        {
            "priority": "normal",
            "task_type": "orchestration",
            "complexity": "medium",
            "input_size": 400,
            "expected_steps": 4,
        },
    )
    repeated = _execute(
        "KA-037",
        {
            "priority": "normal",
            "task_type": "orchestration",
            "complexity": "medium",
            "input_size": 400,
            "expected_steps": 4,
        },
    )

    _assert_pure_bounded_result("KA-037", normal)
    assert normal.output == repeated.output
    assert 500 <= normal.output["token_budget"] <= 12_000
    assert normal.output["timeout_ms"] <= 30_000
    assert normal.output["execution_queue"] in {"interactive", "priority", "batch"}


def test_ka_042_semantic_contract():
    projected = _execute(
        "KA-042",
        {
            "scenario": "raise capacity",
            "baseline": {"capacity": 10, "latency": 100},
            "change": {"capacity": 20},
            "relationships": {"capacity": {"latency": -2}},
        },
    )

    _assert_pure_bounded_result("KA-042", projected)
    assert projected.output["projected_state"] == {
        "capacity": 20,
        "latency": 80.0,
    }
    assert projected.output["divergence_score"] == 1.0
    assert projected.output["risk_level"] == "high"


def test_ka_070_semantic_contract():
    simulated = _execute(
        "KA-070",
        {
            "hypotheticals": [],
            "graph": {"capacity": {"latency": 0.5}},
            "dependency_results": {
                "KA-042": {
                    "success": True,
                    "divergence_score": 0.5,
                    "impacts": [
                        {
                            "field": "capacity",
                            "after": 20,
                            "changed": True,
                        }
                    ],
                }
            },
        },
    )

    _assert_bounded_result("KA-070", simulated)
    assert simulated.output["local_projection_consumed"] is True
    assert simulated.output["simulated_outcomes"][0]["changed_node"] == "capacity"
    assert simulated.output["aggregate_divergence"] == 0.5


def test_ka_1080_semantic_contract():
    estimated = _execute(
        "KA-1080",
        {
            "planned_steps": [
                {
                    "step_id": "contextualize",
                    "iterations": 2,
                    "estimated_ms_per_iteration": 50,
                    "estimated_tokens_per_iteration": 100,
                    "estimated_peak_memory_mb": 256,
                    "estimated_cost_per_iteration": 0.01,
                }
            ],
            "contingency_ratio": 0.25,
        },
    )

    _assert_pure_bounded_result("KA-1080", estimated)
    assert estimated.output["estimate"] == {
        "duration_ms": 125.0,
        "tokens": 250,
        "cost_units": 0.025,
        "peak_memory_mb": 256.0,
        "step_count": 1,
        "contingency_ratio": 0.25,
    }
    assert estimated.output["measurement_status"] == "caller_supplied_estimate"


def test_ka_1081_semantic_contract():
    blocked = _execute(
        "KA-1081",
        {
            "estimated_duration_ms": 1,
            "estimated_tokens": 1,
            "estimated_cost_units": 0,
            "estimated_peak_memory_mb": 1,
            "recursion_depth": 0,
            "concurrency": 1,
            "maximum_duration_ms": 1_000,
            "maximum_tokens": 1_000,
            "maximum_cost_units": 1,
            "maximum_peak_memory_mb": 512,
            "maximum_recursion_depth": 0,
            "maximum_concurrency": 1,
            "dependency_results": {
                "KA-1080": {
                    "estimate": {
                        "duration_ms": 500,
                        "tokens": 2_000,
                        "cost_units": 0,
                        "peak_memory_mb": 256,
                    }
                }
            },
        },
    )

    _assert_pure_bounded_result("KA-1081", blocked)
    assert blocked.output["allowed"] is False
    assert blocked.output["estimate_source"] == "KA-1080_dependency"
    assert blocked.output["violations"] == [
        {"budget": "tokens", "estimated": 2_000, "maximum": 1_000}
    ]


def test_ka_1091_semantic_contract():
    planned = _execute(
        "KA-1091",
        {
            "outcomes": [
                {
                    "scenario_id": "scenario-1",
                    "outcome_id": "outcome-1",
                    "status": "completed",
                    "significance": 0.9,
                    "summary": "Bounded simulation completed.",
                    "artifact_refs": [],
                }
            ],
            "minimum_significance": 0.7,
        },
    )

    _assert_bounded_result("KA-1091", planned)
    assert planned.output["archive_count"] == 1
    assert planned.output["artifacts_written"] == 0
    assert planned.output["effect_service_required"] is True
    assert len(planned.output["archive_plans"][0]["content_sha256"]) == 64


def test_ka_137_semantic_contract():
    discovered = _execute(
        "KA-137",
        {
            "documents": [
                {
                    "document_id": "mcp-arguments",
                    "text": "api_key=abcdefghijklmnop and 123-45-6789",
                }
            ],
            "detect_types": ["api_key", "ssn"],
        },
    )

    _assert_pure_bounded_result("KA-137", discovered)
    assert [
        finding["data_type"] for finding in discovered.output["findings"]
    ] == ["api_key", "ssn"]
    assert discovered.output["matched_values_returned"] is False
    assert "abcdefghijklmnop" not in str(discovered.output)
    assert "123-45-6789" not in str(discovered.output)


def test_ka_177_semantic_contract():
    allowed = _execute(
        "KA-177",
        {
            "attributes": {"consent_approved": True},
            "rules": [
                {
                    "rule_id": "allow-approved",
                    "attribute": "consent_approved",
                    "operator": "equals",
                    "expected": True,
                    "effect": "allow",
                }
            ],
            "default_effect": "deny",
        },
    )
    denied = _execute(
        "KA-177",
        {
            "attributes": {"consent_approved": False},
            "rules": [
                {
                    "rule_id": "deny-missing",
                    "attribute": "consent_approved",
                    "operator": "equals",
                    "expected": False,
                    "effect": "deny",
                }
            ],
            "default_effect": "deny",
        },
    )

    _assert_bounded_result("KA-177", allowed)
    _assert_bounded_result("KA-177", denied)
    assert allowed.output["decision"] == "allow"
    assert denied.output["decision"] == "deny"
    assert allowed.output["effect_applied"] is False
    assert denied.output["deny_overrides"] is True


def test_ka_179_semantic_contract():
    allowed = _execute(
        "KA-179",
        {
            "subject_id": "owner-1",
            "roles": ["mcp_executor"],
            "attributes": {"connector": "local"},
            "action": "execute",
            "resource_type": "mcp_tool",
            "rules": [
                {
                    "rule_id": "mcp-executor",
                    "actions": ["execute"],
                    "resource_types": ["mcp_tool"],
                    "required_roles": ["mcp_executor"],
                    "required_attributes": {"connector": "local"},
                    "effect": "allow",
                }
            ],
        },
    )
    denied = _execute(
        "KA-179",
        {
            "subject_id": "owner-1",
            "roles": [],
            "attributes": {"connector": "local"},
            "action": "execute",
            "resource_type": "mcp_tool",
            "rules": [
                {
                    "rule_id": "mcp-executor",
                    "actions": ["execute"],
                    "resource_types": ["mcp_tool"],
                    "required_roles": ["mcp_executor"],
                    "required_attributes": {"connector": "local"},
                    "effect": "allow",
                }
            ],
        },
    )

    _assert_bounded_result("KA-179", allowed)
    _assert_bounded_result("KA-179", denied)
    assert allowed.output["decision"] == "allow"
    assert denied.output["decision"] == "deny"
    assert denied.output["default_deny"] is True
    assert allowed.output["access_applied"] is False
