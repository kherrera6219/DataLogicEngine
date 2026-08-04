"""Batch 12 TruthMemory/TruthLink/FROST temporal-health owner proofs."""

from __future__ import annotations

import json

import pytest

from backend.truth_engine.knowledge_temporal_health import (
    BATCH_12_IDS,
    KnowledgeTemporalHealthCoordinator,
    KnowledgeTemporalHealthError,
    KnowledgeTemporalHealthService,
)


def _inputs() -> dict[str, dict]:
    return {
        "KA-023": {
            "reference_time": "2026-07-25T00:00:00Z",
            "knowledge_items": [
                {
                    "knowledge_id": "knowledge-1",
                    "current_confidence": 0.9,
                    "observed_at": "2026-01-01T00:00:00Z",
                    "domain": "general",
                    "category": "knowledge",
                }
            ],
        },
        "KA-052": {
            "reference_date": "2026-07-25",
            "records": [
                {
                    "knowledge_id": "knowledge-1",
                    "last_validated_on": "2026-01-01",
                    "current_version": 10,
                    "protected": False,
                }
            ],
        },
        "KA-064": {
            "failure_events": [
                {
                    "occurrence_id": f"event-{index}",
                    "failure_code": "revalidation_failed",
                    "component": "truthmemory",
                }
                for index in range(3)
            ],
            "minimum_occurrences": 3,
        },
        "KA-1082": {
            "series": [
                {
                    "knowledge_id": "knowledge-1",
                    "observations": [
                        {"observed_at": "2026-01-01T00:00:00Z", "confidence": 0.9},
                        {"observed_at": "2026-07-01T00:00:00Z", "confidence": 0.6},
                    ],
                }
            ],
            "degradation_threshold": 0.1,
        },
        "KA-1083": {
            "reference_date": "2026-07-25",
            "candidates": [
                {
                    "knowledge_id": "knowledge-1",
                    "last_validated_on": "2026-01-01",
                    "risk_class": "high",
                    "confidence": 0.6,
                }
            ],
        },
        "KA-1093": {
            "reference_date": "2026-07-25",
            "records": [
                {
                    "knowledge_id": "knowledge-1",
                    "current_trust": 0.8,
                    "last_used_on": "2026-01-01",
                    "risk_class": "high",
                    "active_evidence_count": 0,
                }
            ],
        },
        "KA-1105": {
            "concepts": [
                {
                    "concept_id": "knowledge-1",
                    "baseline_contradiction_rate": 0.1,
                    "current_contradiction_rate": 0.7,
                    "active_citation_count": 0,
                    "superseding_policy_refs": ["policy-v2"],
                    "paradigm_replacement_refs": ["model-v2"],
                }
            ],
        },
    }


def _submit(service: KnowledgeTemporalHealthService, **overrides):
    payload = {
        "ka_inputs": _inputs(),
        "idempotency_key": "temporal-health-review-1",
        "request_id": "batch-12-temporal-health",
        "principal_id": "owner-1",
    }
    payload.update(overrides)
    return service.record_review(**payload)


def test_temporal_health_owner_records_only_content_free_review(tmp_path):
    service = KnowledgeTemporalHealthService(review_root=tmp_path / "reviews")

    first = _submit(service)
    second = _submit(service)

    assert first == second
    assert set(first["algorithm_summaries"]) == set(BATCH_12_IDS)
    assert first["lifecycle"]["execution_order"] == [
        ["KA-023", "KA-064", "KA-1082", "KA-1093"],
        ["KA-1083"],
        ["KA-052", "KA-1105"],
    ]
    assert first["knowledge_updates_applied"] is False
    assert first["confidence_updates_applied"] is False
    assert first["trust_updates_applied"] is False
    assert first["versions_created"] == 0
    assert first["retirements_applied"] == 0
    assert first["jobs_scheduled"] == 0
    assert first["alerts_dispatched"] == 0
    assert first["provider_calls_applied"] == 0
    assert first["external_egress_applied"] is False
    receipt = first["authoritative_effect_receipt"]
    assert receipt["operation"] == "record_knowledge_temporal_health_review"
    assert receipt["status"] == "applied"


def _assert_owning_path(tmp_path, canonical_id):
    service = KnowledgeTemporalHealthService(review_root=tmp_path / "reviews")

    record = _submit(service)

    states = record["lifecycle"]["trace_states"][canonical_id]
    assert states[:2] == ["planned", "candidate"]
    assert "selected" in states
    assert "executed" in states
    assert states[-1] == "effect_proposed"


def test_ka_023_owning_path(tmp_path):
    _assert_owning_path(tmp_path, "KA-023")


def test_ka_052_owning_path(tmp_path):
    _assert_owning_path(tmp_path, "KA-052")


def test_ka_064_owning_path(tmp_path):
    _assert_owning_path(tmp_path, "KA-064")


def test_ka_1082_owning_path(tmp_path):
    _assert_owning_path(tmp_path, "KA-1082")


def test_ka_1083_owning_path(tmp_path):
    _assert_owning_path(tmp_path, "KA-1083")


def test_ka_1093_owning_path(tmp_path):
    _assert_owning_path(tmp_path, "KA-1093")


def test_ka_1105_owning_path(tmp_path):
    _assert_owning_path(tmp_path, "KA-1105")


def test_temporal_health_rejects_idempotency_reuse(tmp_path):
    service = KnowledgeTemporalHealthService(review_root=tmp_path / "reviews")
    original = _submit(service)
    target = service.review_root / f"{original['review_id']}.json"
    original_bytes = target.read_bytes()
    changed = _inputs()
    changed["KA-023"]["minimum_confidence"] = 0.2

    with pytest.raises(
        KnowledgeTemporalHealthError,
        match="different review",
    ):
        _submit(service, ka_inputs=changed)

    assert target.read_bytes() == original_bytes


def test_temporal_health_rejects_tampered_receipt(tmp_path):
    service = KnowledgeTemporalHealthService(review_root=tmp_path / "reviews")
    original = _submit(service)
    target = service.review_root / f"{original['review_id']}.json"
    tampered = json.loads(target.read_text(encoding="utf-8"))
    tampered["knowledge_updates_applied"] = True
    target.write_text(json.dumps(tampered), encoding="utf-8")

    with pytest.raises(
        KnowledgeTemporalHealthError,
        match="failed integrity validation",
    ):
        _submit(service)


def test_temporal_health_rejects_tampered_ka_claim_before_write(tmp_path):
    class TamperedCoordinator(KnowledgeTemporalHealthCoordinator):
        def execute_operation_sync(self, **kwargs):
            execution = super().execute_operation_sync(**kwargs)
            execution.results["KA-052"]["output"]["retirements_applied"] = 1
            return execution

    service = KnowledgeTemporalHealthService(
        review_root=tmp_path / "reviews",
        coordinator=TamperedCoordinator(),
    )

    with pytest.raises(
        KnowledgeTemporalHealthError,
        match="unsupported effect",
    ):
        _submit(service)

    assert not service.review_root.exists()
