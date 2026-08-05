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

    assert len(set(registry_ids)) == 80
    assert set(registry_ids) <= set(manifest.entries)
    assert {
        "KA-051",
        "KA-054",
        "KA-055",
        "KA-063",
    } <= set(registry_ids)
    assert all(
        manifest.entries[canonical_id].admission.production_enabled
        for canonical_id in (
            "KA-051",
            "KA-054",
            "KA-055",
            "KA-063",
        )
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


def _batch_17_inputs():
    snapshot = {"nodes": [{"id": "knowledge-1", "digest": "abc"}], "edges": []}
    return {
        "KA-004": {"query": "validated knowledge release"},
        "KA-005": {"query": "validated knowledge release"},
        "KA-018": {
            "source_id": "source-1",
            "source_type": "local_document",
            "content_sha256": "a" * 64,
            "provenance_checks": [
                {
                    "check_id": "hash-bound",
                    "status": "passed",
                    "authority_ref": "local-receipt",
                }
            ],
        },
        "KA-022": {
            "recommendation": "release validated knowledge",
            "impact_scores": {"governed_risk": 0.0},
        },
        "KA-024": {"confidence": 0.95, "risk_score": 0.0},
        "KA-062": {
            "source_id": "source-1",
            "signature_verified": True,
            "authority_verified": True,
            "independently_corrobated": True,
        },
        "KA-065": {"snapshot": snapshot, "baseline": snapshot},
        "KA-1071": {
            "knowledge_id": "knowledge-1",
            "nodes": [
                {"node_id": "source", "node_type": "source", "source_ref": "source-1"},
                {
                    "node_id": "claim",
                    "node_type": "claim",
                    "source_ref": "knowledge-1",
                    "parent_node_ids": ["source"],
                },
            ],
        },
        "KA-1074": {
            "fields": [
                {
                    "field_id": "status",
                    "value": "approved",
                    "classification": "public",
                }
            ]
        },
        "KA-1094": {
            "candidates": [
                {
                    "knowledge_id": "knowledge-1",
                    "validation_status": "validated",
                    "confidence": 0.95,
                    "contradiction_count": 0,
                }
            ]
        },
        "KA-1109": {
            "candidates": [
                {
                    "knowledge_id": "knowledge-1",
                    "declared_sensitivity": "public",
                    "consent_verified": True,
                }
            ]
        },
        "KA-1107": {
            "planned_steps": [
                {
                    "step_id": "release",
                    "capability_id": "KA-1079",
                    "layer": "L10",
                    "query_class": "knowledge_release",
                }
            ],
            "allowed_capability_ids": ["KA-1079"],
            "allowed_layers": ["L10"],
            "allowed_query_classes": ["knowledge_release"],
        },
        "KA-117": {"snapshot": snapshot},
    }


def _run_batch_17_owner(canonical_id: str):
    operation = "maintenance" if canonical_id == "KA-062" else "release"
    execution = KnowledgeLifecycleCoordinator().execute_operation_sync(
        owner="truthmemory_truthlink_frost",
        operation=operation,
        requested_ids=[canonical_id],
        ka_inputs=_batch_17_inputs(),
        request_id=f"batch-17-{canonical_id}",
        run_id=f"batch-17-run-{canonical_id}",
        max_effects=4,
        principal_id="owner-1",
        service_capabilities={"knowledge_lifecycle_service"},
    )
    states = [
        event.state.value
        for event in execution.report.traces[canonical_id].events
        if event.state.value != "effect_proposed"
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


def test_ka_062_owning_path():
    output = _run_batch_17_owner("KA-062")
    assert output["dependency_consumed"] == "KA-018"
    assert output["source_trust_established"] is False


def test_ka_065_owning_path():
    output = _run_batch_17_owner("KA-065")
    assert output["status"] == "regression_free"
    assert output["knowledge_updated"] is False


def test_ka_1071_owning_path():
    output = _run_batch_17_owner("KA-1071")
    assert output["provenance_complete"] is True
    assert output["provenance_persisted"] is False


def test_ka_1094_owning_path():
    output = _run_batch_17_owner("KA-1094")
    assert output["decisions"][0]["decision"] == "retain"
    assert output["records_moved"] == 0


def test_ka_1109_owning_path():
    output = _run_batch_17_owner("KA-1109")
    assert output["decisions"][0]["containment_class"] == "public"
    assert output["persistence_actions_applied"] == 0


def test_ka_117_owning_path():
    output = _run_batch_17_owner("KA-117")
    assert output["is_valid"] is True
    assert output["quarantine_applied"] is False


def _batch_23_inputs():
    from tests.integration.phase19.test_retrieval_graph_memory import (
        _batch_22_inputs,
    )

    inputs = _batch_22_inputs()
    inputs.update(
        {
            "KA-009": {
                "query": "validated knowledge release",
                "evidence": [
                    {
                        "evidence_id": "evidence-1",
                        "source_type": "documentation",
                        "content": "validated knowledge release",
                    }
                ],
            },
            "KA-051": {
                "traces": [
                    {
                        "trace_id": "trace-1",
                        "pattern_id": "bounded-release-review",
                        "measured_score": 0.95,
                    }
                ]
            },
            "KA-053": {"graph_segments": [{"nodes": [{"id": "a"}, {"id": "b"}]}]},
            "KA-054": {
                "multilingual_sources": [
                    {
                        "source_id": "en-source",
                        "language": "en",
                        "nodes": [{"id": "en-control", "concept_id": "control"}],
                    },
                    {
                        "source_id": "es-source",
                        "language": "es",
                        "nodes": [{"id": "es-control", "concept_id": "control"}],
                    },
                ]
            },
            "KA-055": {
                "modal_evidence": [
                    {
                        "evidence_id": "text-1",
                        "topic_id": "control",
                        "modality": "text",
                        "verdict": "supported",
                        "measured_score": 0.9,
                    },
                    {
                        "evidence_id": "image-1",
                        "topic_id": "control",
                        "modality": "image",
                        "verdict": "uncertain",
                        "measured_score": 0.6,
                    },
                ]
            },
            "KA-063": {
                "outcome_metrics": {
                    "measured_accuracy": 0.75,
                    "p95_latency_ms": 1_200,
                },
                "feedback": [{"feedback_id": "f-1", "label": "reviewed"}],
            },
        }
    )
    return inputs


def _run_batch_23_owner(canonical_id: str):
    from backend.governed_execution.knowledge_content_evolution import (
        KnowledgeLifecycleService,
    )

    review = KnowledgeLifecycleService().review_content_evolution_sync(
        requested_ids=[canonical_id],
        ka_inputs=_batch_23_inputs(),
        request_id=f"batch-23-{canonical_id}",
        run_id=f"batch-23-run-{canonical_id}",
        principal_id="owner-1",
        release_authorized=False,
    )
    assert review.ok
    receipt = review.receipts[canonical_id]
    assert receipt["service"] == "KnowledgeLifecycleService"
    assert receipt["status"] == "release_not_authorized"
    assert receipt["applied"] is False
    assert receipt["rollback_status"] == "not_required_no_mutation"
    states = [
        event.state.value
        for event in review.execution.report.traces[canonical_id].events
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
    return review.execution.results[canonical_id]["output"]


def test_ka_051_owning_path():
    output = _run_batch_23_owner("KA-051")
    assert output["candidate_count"] == 1
    assert output["knowledge_changes_applied"] is False


def test_ka_053_owning_path():
    output = _run_batch_23_owner("KA-053")
    assert output["proposal_count"] == 1
    assert output["compression_applied"] is False


def test_ka_054_owning_path():
    output = _run_batch_23_owner("KA-054")
    assert output["alignment_count"] == 1
    assert output["translation_performed"] is False
    assert output["fusion_applied"] is False


def test_ka_055_owning_path():
    output = _run_batch_23_owner("KA-055")
    assert output["disagreement_topic_ids"] == ["control"]
    assert output["source_content_returned"] is False
    assert output["fusion_applied"] is False


def test_ka_063_owning_path():
    output = _run_batch_23_owner("KA-063")
    assert len(output["suggestions"]) == 2
    assert output["profile_update_applied"] is False
    assert output["model_training_started"] is False
