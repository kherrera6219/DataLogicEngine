from __future__ import annotations

import pytest

from backend.governed_execution.contracts import (
    GovernedStage,
    GovernedStageStatus,
)
from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleCoordinator,
    KnowledgeLifecycleError,
    LifecycleTransitionPublisher,
)
from backend.memory.unified_memory_service import UnifiedMemoryService
from backend.storage.retention import (
    DeleteResult,
    DeletionSubject,
    RetentionDeleteCoordinator,
)
from backend.truth_engine.knowledge_temporal_health import (
    KnowledgeTemporalHealthService,
)
from extensions import db


def test_cp19h_truthlink_and_frost_record_causal_stage_and_ka_lineage():
    publisher = LifecycleTransitionPublisher()
    first = GovernedStage(name="admission", stage_type="policy")
    first_receipt = publisher.publish_stage("trace-1", first)
    first.finish(GovernedStageStatus.COMPLETED)
    publisher.publish_stage("trace-1", first)
    second = GovernedStage(name="layer_1", stage_type="reasoning_layer")
    second_receipt = publisher.publish_stage("trace-1", second)

    assert first_receipt["parent_stage_id"] is None
    assert second_receipt["parent_stage_id"] == first.stage_id
    assert publisher.frost.verify_snapshot(first_receipt["snapshot_id"])
    assert publisher.truth_link.message_queue[-1]["message_type"] == (
        "stage_transition"
    )


def test_cp19h_truthlink_publication_failure_is_visible():
    class FailingBus:
        @staticmethod
        def publish(*args, **kwargs):
            raise RuntimeError("publication_failed")

    publisher = LifecycleTransitionPublisher(truth_link=FailingBus())

    with pytest.raises(KnowledgeLifecycleError):
        publisher.publish_stage(
            "trace-failure",
            GovernedStage(name="admission", stage_type="policy"),
        )


def test_cp19h_validated_memory_commit_has_receipt_and_rolls_back(tmp_path):
    memory = UnifiedMemoryService(
        storage_path=tmp_path / "memory.json",
        auto_load=False,
        strict=True,
    )
    coordinator = KnowledgeLifecycleCoordinator(memory_service=memory)
    proposal = coordinator.stage_validated_memory(
        content="validated knowledge",
        session_id="session-1",
        source_run_id="run-1",
        source_ids=["source-1"],
        owner_user_id=1,
        principal_id="desktop-1",
        tenant_id="tenant-1",
    )

    committed = coordinator.commit_validated_memory(proposal)

    assert committed.applied is True
    assert committed.receipt["validation_state"] == "validated"
    assert len(memory.graph.vertices) == 1
    assert coordinator.rollback_validated_memory(committed) is True
    assert committed.state == "rolled_back"
    assert len(memory.graph.vertices) == 0


def test_cp19h_registry_preserves_experimental_boundaries_and_no_duplicate_ids():
    coordinator = KnowledgeLifecycleCoordinator()
    manifest = coordinator.ka_controller.manifest
    registry_ids = [
        canonical_id
        for operations in coordinator.owners.values()
        for canonical_ids in operations.values()
        for canonical_id in canonical_ids
    ]

    assert len(set(registry_ids)) == 66
    assert set(registry_ids) <= set(manifest.entries)
    assert {
        "KA-029",
        "KA-034",
        "KA-051",
        "KA-054",
        "KA-055",
        "KA-063",
    }.isdisjoint(registry_ids)
    assert all(
        not manifest.entries[canonical_id].admission.production_enabled
        for canonical_id in {
            "KA-029",
            "KA-034",
            "KA-051",
            "KA-054",
            "KA-055",
            "KA-063",
        }
    )


def test_cp19h_deletion_and_recovery_dispatch_owned_maintenance_kas(app):
    class EmptyAdapter:
        @staticmethod
        def delete(subject):
            return DeleteResult(0)

        @staticmethod
        def remnant_count(subject):
            return 0

    stores = (
        "postgresql",
        "neo4j",
        "chroma",
        "redis",
        "minio",
        "local_json",
        "logs",
    )
    with app.app_context():
        coordinator = RetentionDeleteCoordinator(
            session=db.session,
            adapters={name: EmptyAdapter() for name in stores},
            required_stores=stores,
            digest_key="installation-scoped-tombstone-key",
        )
        tombstone = coordinator.run(DeletionSubject("user", "owner-1"))
        assert tombstone.status == "completed"
    assert coordinator.lifecycle_evidence["cache_invalidation"]["executed_ids"] == [
        "KA-080"
    ]
    assert coordinator.lifecycle_evidence["failure_recovery"]["executed_ids"] == [
        "KA-064"
    ]


def _temporal_health_inputs():
    knowledge_id = "knowledge-1"
    return {
        "KA-023": {
            "reference_time": "2026-07-25T00:00:00Z",
            "knowledge_items": [
                {
                    "knowledge_id": knowledge_id,
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
                    "knowledge_id": knowledge_id,
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
                    "knowledge_id": knowledge_id,
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
                    "knowledge_id": knowledge_id,
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
                    "knowledge_id": knowledge_id,
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
                    "concept_id": knowledge_id,
                    "baseline_contradiction_rate": 0.1,
                    "current_contradiction_rate": 0.7,
                    "active_citation_count": 0,
                    "superseding_policy_refs": ["policy-v2"],
                    "paradigm_replacement_refs": ["model-v2"],
                }
            ],
        },
    }


def _assert_temporal_health_owner_path(tmp_path, canonical_id):
    record = KnowledgeTemporalHealthService(
        review_root=tmp_path / "reviews"
    ).record_review(
        ka_inputs=_temporal_health_inputs(),
        idempotency_key=f"temporal-health-{canonical_id}",
        request_id=f"batch-12-{canonical_id}",
        principal_id="owner-1",
    )
    states = record["lifecycle"]["trace_states"][canonical_id]
    assert states[:2] == ["planned", "candidate"]
    assert "selected" in states
    assert "admitted" in states
    assert "executing" in states
    assert "executed" in states
    assert states[-1] == "effect_proposed"
    assert record["authoritative_effect_receipt"]["status"] == "applied"


def test_ka_023_owning_path(tmp_path):
    _assert_temporal_health_owner_path(tmp_path, "KA-023")


def test_ka_052_owning_path(tmp_path):
    _assert_temporal_health_owner_path(tmp_path, "KA-052")


def test_ka_064_owning_path(tmp_path):
    _assert_temporal_health_owner_path(tmp_path, "KA-064")


def test_ka_1082_owning_path(tmp_path):
    _assert_temporal_health_owner_path(tmp_path, "KA-1082")


def test_ka_1083_owning_path(tmp_path):
    _assert_temporal_health_owner_path(tmp_path, "KA-1083")


def test_ka_1093_owning_path(tmp_path):
    _assert_temporal_health_owner_path(tmp_path, "KA-1093")


def test_ka_1105_owning_path(tmp_path):
    _assert_temporal_health_owner_path(tmp_path, "KA-1105")
