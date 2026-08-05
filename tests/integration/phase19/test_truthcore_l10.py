"""CP19-K Batch 25 owning-path proof for L10 oversight and release proposals."""

from __future__ import annotations

from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator
from tests.integration.phase19.test_truthcore_l6_l8 import _inputs as _l6_inputs


def _batch_25_inputs() -> dict[str, dict]:
    inputs = _l6_inputs()
    inputs.update(
        {
            "KA-020": {
                "pass_count": 1,
                "max_passes": 3,
                "final_confidence": 0.5,
                "entropy_level": 0.8,
                "gap_count": 1,
            },
            "KA-021": {
                "observations": [
                    {
                        "observation_id": "obs-1",
                        "metric_name": "unresolved_conflict_count",
                        "baseline_value": 0,
                        "observed_value": 2,
                        "tolerance": 0,
                        "corroborating_trace_ids": ["trace-1"],
                    }
                ]
            },
            "KA-1106": {
                "overrides": [
                    {
                        "override_id": "override-1",
                        "decision_ref": "decision-1",
                        "original_outcome": "release",
                        "corrected_outcome": "review",
                        "reason_code": "safety_intervention",
                        "rationale": "The human owner required an additional safety review.",
                        "reviewer_role": "release_owner",
                        "evidence_refs": ["trace-1"],
                    }
                ]
            },
            "KA-1112": {
                "windows": [
                    {
                        "window_id": "window-1",
                        "chaos_plan_count": 0,
                        "unapproved_chaos_count": 0,
                        "human_override_count": 1,
                        "override_without_reason_count": 0,
                        "drift_alert_count": 0,
                        "unresolved_drift_count": 0,
                    }
                ]
            },
            "KA-116": {"content": "repeat repeat repeat repeat"},
        }
    )
    return inputs


def _run_batch_25_owner(canonical_id: str):
    execution = KnowledgeLifecycleCoordinator().execute_operation_sync(
        owner="truthcore_l10",
        operation="oversight_release",
        requested_ids=[canonical_id],
        ka_inputs=_batch_25_inputs(),
        request_id=f"batch-25-{canonical_id}",
        run_id=f"batch-25-run-{canonical_id}",
        max_effects=2,
        principal_id="release-owner",
        service_capabilities={"governed_execution_service"},
    )
    states = [
        event.state.value
        for event in execution.report.traces[canonical_id].events
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
    return execution.results[canonical_id]["output"]


def test_ka_020_owning_path():
    output = _run_batch_25_owner("KA-020")
    assert output["should_loopback"] is True
    assert output["loopback_applied"] is False
    assert output["dependencies_consumed"] == ["KA-014", "KA-1102"]


def test_ka_021_owning_path():
    output = _run_batch_25_owner("KA-021")
    assert output["is_emergent"] is True
    assert output["emergence_established"] is False


def test_ka_1106_owning_path():
    output = _run_batch_25_owner("KA-1106")
    assert len(output["records"][0]["training_signal_sha256"]) == 64
    assert output["training_updates_applied"] == 0


def test_ka_1112_owning_path():
    output = _run_batch_25_owner("KA-1112")
    assert output["audit_passed"] is True
    assert output["governance_actions_applied"] == 0


def test_ka_116_owning_path():
    output = _run_batch_25_owner("KA-116")
    assert output["state"] == "STABLE"
    assert output["reconciliation_triggered"] is False
    assert output["system_decay_established"] is False
