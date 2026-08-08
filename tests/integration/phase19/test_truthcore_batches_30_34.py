"""CP19-K Batches 30-34 owner-path qualification proofs."""

from __future__ import annotations

from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator
from tests.integration.phase19.test_truthcore_l1_l5 import _batch_13_inputs
from tests.integration.phase19.test_truthcore_l6_l8 import _inputs as _l6_inputs
from tests.knowledge_algorithms.test_phase19_per_ka_semantics import (
    _batch_30_34_payloads,
)


def _owner_inputs() -> dict[str, dict]:
    inputs = _batch_30_34_payloads()
    inputs.update(_batch_13_inputs())
    inputs.update(_l6_inputs())
    inputs["KA-005"] = {"query": "Prepare a bounded technical release review"}
    inputs["KA-004"] = {"query": "Prepare a bounded technical release review"}
    inputs["KA-1080"] = {
        "planned_steps": [
            {
                "step_id": "refine",
                "iterations": 1,
                "estimated_ms_per_iteration": 10,
                "estimated_tokens_per_iteration": 100,
                "estimated_peak_memory_mb": 64,
                "estimated_cost_per_iteration": 0,
            }
        ],
        "contingency_ratio": 0,
    }
    inputs["KA-1081"] = {
        "estimated_duration_ms": 10,
        "estimated_tokens": 100,
        "estimated_cost_units": 0,
        "estimated_peak_memory_mb": 64,
        "recursion_depth": 1,
        "concurrency": 1,
        "maximum_duration_ms": 1_000,
        "maximum_tokens": 1_000,
        "maximum_cost_units": 1,
        "maximum_peak_memory_mb": 512,
        "maximum_recursion_depth": 3,
        "maximum_concurrency": 2,
    }
    inputs["L10-KA-007"] = {"request_id": "r1", "confidence": 0.98}
    return inputs


_OWNER_OPERATION = {
    **{
        canonical_id: ("truthcore_l6_l8", "planning_control")
        for canonical_id in ["KA-006", "KA-007", "KA-060"]
    },
    **{
        canonical_id: ("truthcore_l6_l8", "advanced_reasoning")
        for canonical_id in [
            "KA-066",
            "KA-067",
            "KA-1036",
            "KA-1044",
            "KA-1047",
            "KA-1085",
        ]
    },
    **{
        canonical_id: ("truthcore_l9", "synthesis_explainability")
        for canonical_id in ["KA-008", "KA-019", "KA-056", "KA-1038", "KA-1087"]
    },
    **{
        f"L9-KA-{number:03d}": ("truthcore_l9", "exact_loop_suite")
        for number in range(1, 8)
    },
    **{
        f"L10-KA-{number:03d}": ("truthcore_l10", "exact_release_suite")
        for number in range(1, 8)
    },
}


def _assert_owner_path(canonical_id: str) -> dict:
    owner, operation = _OWNER_OPERATION[canonical_id]
    execution = KnowledgeLifecycleCoordinator(workflow_phase="cp19k").execute_operation_sync(
        owner=owner,
        operation=operation,
        requested_ids=[canonical_id],
        ka_inputs=_owner_inputs(),
        request_id=f"batch-30-34-{canonical_id}",
        run_id=f"batch-30-34-run-{canonical_id}",
        max_effects=8,
        principal_id="truthcore-owner",
        service_capabilities={"governed_execution_service"},
    )
    trace = execution.report.traces[canonical_id]
    states = [
        event.state.value
        for event in trace.events
        if event.state.value not in {"dependency", "effect_proposed"}
    ]
    assert states == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    result = execution.results[canonical_id]
    assert result["effects"] == []
    return result["output"]


def test_ka_006_owning_path():
    assert _assert_owner_path("KA-006")["execution_started"] is False


def test_ka_007_owning_path():
    assert _assert_owner_path("KA-007")["recursion_applied"] is False


def test_ka_060_owning_path():
    assert _assert_owner_path("KA-060")["execution_started"] is False


def test_ka_066_owning_path():
    assert _assert_owner_path("KA-066")["causal_graph_fragment"]


def test_ka_067_owning_path():
    assert _assert_owner_path("KA-067")["transfer_applied"] is False


def test_ka_1036_owning_path():
    assert _assert_owner_path("KA-1036")["pareto_front"] == ["a"]


def test_ka_1044_owning_path():
    assert _assert_owner_path("KA-1044")["knowledge_persisted"] is False


def test_ka_1047_owning_path():
    assert _assert_owner_path("KA-1047")["execution_started"] is False


def test_ka_1085_owning_path():
    assert _assert_owner_path("KA-1085")["anomaly_count"] == 1


def test_ka_008_owning_path():
    assert _assert_owner_path("KA-008")["assessment_complete"] is True


def test_ka_019_owning_path():
    assert _assert_owner_path("KA-019")["knowledge_persisted"] is False


def test_ka_056_owning_path():
    assert _assert_owner_path("KA-056")["provider_called"] is False


def test_ka_1038_owning_path():
    assert _assert_owner_path("KA-1038")["extraction_performed"] is False


def test_ka_1087_owning_path():
    assert _assert_owner_path("KA-1087")["coverage_complete"] is True


def test_l9_ka_001_owning_path():
    assert _assert_owner_path("L9-KA-001")["trace_complete"] is True


def test_l9_ka_002_owning_path():
    assert _assert_owner_path("L9-KA-002")["drift_detected"] is False


def test_l9_ka_003_owning_path():
    assert _assert_owner_path("L9-KA-003")["consensus"] is True


def test_l9_ka_004_owning_path():
    assert _assert_owner_path("L9-KA-004")["evaluation_score"] == 1.0


def test_l9_ka_005_owning_path():
    assert _assert_owner_path("L9-KA-005")["trigger_refinement"] is True


def test_l9_ka_006_owning_path():
    assert _assert_owner_path("L9-KA-006")["status"] == "measured"


def test_l9_ka_007_owning_path():
    assert _assert_owner_path("L9-KA-007")["continue"] is True


def test_l10_ka_001_owning_path():
    assert _assert_owner_path("L10-KA-001")["success"] is True


def test_l10_ka_002_owning_path():
    assert _assert_owner_path("L10-KA-002")["awareness_detected"] is False


def test_l10_ka_003_owning_path():
    assert _assert_owner_path("L10-KA-003")["sensitive_values_returned"] is False


def test_l10_ka_004_owning_path():
    assert _assert_owner_path("L10-KA-004")["passed"] is True


def test_l10_ka_005_owning_path():
    assert _assert_owner_path("L10-KA-005")["release_authorized"] is True


def test_l10_ka_006_owning_path():
    assert _assert_owner_path("L10-KA-006")["passed"] is True


def test_l10_ka_007_owning_path():
    assert _assert_owner_path("L10-KA-007")["reviews_dispatched"] == 0
