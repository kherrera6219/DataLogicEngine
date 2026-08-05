"""CP19-K Batch 20 owning-path proof for evidence/confidence/entropy."""

from __future__ import annotations

import pytest

from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator


def _inputs() -> dict[str, dict]:
    return {
        "KA-002": {"goal": "Assess a bounded release claim"},
        "KA-009": {
            "query": "release evidence",
            "evidence": [
                {
                    "evidence_id": "e-1",
                    "source_type": "documentation",
                    "content": "release evidence",
                }
            ],
        },
        "KA-014": {
            "evidence_score": 0.8,
            "persona_consensus_score": 0.7,
            "truth_score": 0.8,
            "relevance_score": 0.9,
        },
        "KA-026": {
            "findings": [
                {"id": "a", "content": "control is enabled"},
                {"id": "b", "content": "control is not enabled"},
            ]
        },
        "KA-035": {
            "gaps": ["coverage"],
            "priors": {"coverage": 0.5},
            "observations": {"coverage": [0.7, 0.9]},
            "evidence_weights": {"coverage": 0.5},
        },
        "KA-1041": {
            "confidence_vectors": [
                {
                    "concept_id": "control",
                    "domain": "percent",
                    "value": 80,
                    "scale_minimum": 0,
                    "scale_maximum": 100,
                }
            ]
        },
        "KA-1042": {"dependency_graph": [{"upstream": "a", "downstream": "release"}]},
        "KA-1102": {
            "categories": [
                {"category": "supported", "count": 8},
                {"category": "unsupported", "count": 2},
            ]
        },
    }


def _run_owner():
    ids = [
        "KA-002",
        "KA-009",
        "KA-014",
        "KA-026",
        "KA-035",
        "KA-1041",
        "KA-1042",
        "KA-1102",
    ]
    return KnowledgeLifecycleCoordinator().execute_operation_sync(
        owner="truthcore_l6_l8",
        operation="evidence_confidence_entropy",
        requested_ids=ids,
        ka_inputs=_inputs(),
        request_id="batch-20-evidence-confidence",
        run_id="batch-20-run",
        max_effects=8,
        principal_id="owner-1",
        service_capabilities={"governed_execution_service"},
    )


def _assert_owner(canonical_id: str):
    execution = _run_owner()
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


@pytest.mark.parametrize(
    ("canonical_id", "assertion"),
    [
        ("KA-002", lambda row: row["execution_started"] is False),
        ("KA-009", lambda row: row["evidence_state_updated"] is False),
        ("KA-014", lambda row: row["calibrated_confidence"] is None),
        ("KA-026", lambda row: row["corrections_applied"] == 0),
        ("KA-035", lambda row: row["imputations_applied"] is False),
        ("KA-1041", lambda row: row["calibrated_probability"] is False),
        ("KA-1042", lambda row: row["corrections_applied"] == 0),
        ("KA-1102", lambda row: 0 <= row["normalized_entropy"] <= 1),
    ],
)
def test_batch_20_individual_owning_paths(canonical_id, assertion):
    assert assertion(_assert_owner(canonical_id))


def test_ka_002_owning_path():
    assert _assert_owner("KA-002")["candidate_only"] is True


def test_ka_009_owning_path():
    assert _assert_owner("KA-009")["overall_validity"] is True


def test_ka_014_owning_path():
    assert _assert_owner("KA-014")["is_certified"] is False


def test_ka_026_owning_path():
    assert _assert_owner("KA-026")["has_contradictions"] is True


def test_ka_035_owning_path():
    assert _assert_owner("KA-035")["method"]


def test_ka_1041_owning_path():
    assert _assert_owner("KA-1041")["normalized_confidence"]


def test_ka_1042_owning_path():
    assert _assert_owner("KA-1042")["dependencies_consumed"] == ["KA-026"]


def test_ka_1102_owning_path():
    assert _assert_owner("KA-1102")["category_count"] == 2
