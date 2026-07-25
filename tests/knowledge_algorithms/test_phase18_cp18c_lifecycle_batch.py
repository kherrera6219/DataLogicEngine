import json

from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = (
    "KA-1071",
    "KA-1074",
    "KA-1075",
    "KA-1076",
    "KA-1077",
    "KA-1078",
    "KA-1082",
    "KA-1083",
    "KA-1086",
    "KA-1088",
)


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_05_has_one_unique_implementation_owner_per_capability():
    definitions = [
        CanonicalKAController().get_definition(ka_id) for ka_id in BATCH_IDS
    ]
    modules = [
        definition.implementation.entrypoint.module
        for definition in definitions
        if definition.implementation.entrypoint is not None
    ]

    assert len(modules) == len(BATCH_IDS)
    assert len(modules) == len(set(modules))
    assert all(not definition.aliases["unscoped"] for definition in definitions)


def test_ka_1071_provenance_tracker_validates_source_to_claim_reachability():
    result = execute(
        "KA-1071",
        {
            "knowledge_id": "knowledge-1",
            "nodes": [
                {
                    "node_id": "source",
                    "node_type": "source",
                    "source_ref": "report.pdf",
                },
                {
                    "node_id": "evidence",
                    "node_type": "evidence",
                    "source_ref": "report.pdf#page=2",
                    "parent_node_ids": ["source"],
                },
                {
                    "node_id": "claim",
                    "node_type": "claim",
                    "source_ref": "claim:1",
                    "parent_node_ids": ["evidence"],
                },
            ],
        },
    )

    assert result.success is True
    assert result.output["provenance_complete"] is True
    assert result.output["topological_node_order"] == [
        "source",
        "evidence",
        "claim",
    ]
    assert result.output["ungrounded_claim_node_ids"] == []
    assert result.output["provenance_persisted"] is False


def test_ka_1074_privacy_preserver_never_returns_non_public_source_values():
    result = execute(
        "KA-1074",
        {
            "fields": [
                {
                    "field_id": "name",
                    "value": "Ada Lovelace",
                    "classification": "personal",
                },
                {
                    "field_id": "secret",
                    "value": "do-not-return-this",
                    "classification": "secret",
                    "strategy": "drop",
                },
                {
                    "field_id": "status",
                    "value": "active",
                    "classification": "public",
                },
            ]
        },
    )

    assert result.success is True
    assert result.output["protected_fields"] == {
        "name": "[REDACTED:PERSONAL]",
        "status": "active",
    }
    assert result.output["dropped_field_ids"] == ["secret"]
    assert "do-not-return-this" not in json.dumps(result.output)
    assert result.output["non_public_value_exposed"] is False


def test_ka_1075_bias_mitigation_reweights_without_changing_labels():
    result = execute(
        "KA-1075",
        {
            "records": [
                {"record_id": "a1", "group": "a", "observed_label": "yes"},
                {"record_id": "a2", "group": "a", "observed_label": "no"},
                {"record_id": "b1", "group": "b", "observed_label": "yes"},
            ]
        },
    )

    assert result.success is True
    assert result.output["group_multipliers"] == {"a": 0.75, "b": 1.5}
    assert [
        row["observed_label"] for row in result.output["weighted_records"]
    ] == ["yes", "no", "yes"]
    assert result.output["labels_changed"] is False
    assert result.output["mutation_applied"] is False


def test_ka_1076_graph_pruner_preserves_referenced_low_value_nodes():
    result = execute(
        "KA-1076",
        {
            "nodes": [
                {
                    "node_id": "candidate",
                    "importance": 0.1,
                    "confidence": 0.2,
                    "age_days": 500,
                    "reuse_count": 0,
                },
                {
                    "node_id": "referenced",
                    "importance": 0.1,
                    "confidence": 0.2,
                    "age_days": 500,
                    "reuse_count": 0,
                },
                {
                    "node_id": "active",
                    "importance": 0.9,
                    "confidence": 0.9,
                    "age_days": 1,
                    "reuse_count": 10,
                },
            ],
            "edges": [
                {"source_node_id": "active", "target_node_id": "referenced"}
            ],
        },
    )

    assert result.success is True
    assert result.output["archive_candidates"] == [
        {
            "node_id": "candidate",
            "action": "archive_candidate",
            "reason": "low_value_stale_unreferenced",
        }
    ]
    assert result.output["retained_low_value_nodes"] == [
        {"node_id": "referenced", "reason": "referenced_by_other_nodes"}
    ]
    assert result.output["nodes_deleted"] == 0


def test_ka_1077_importance_scorer_ranks_declared_signals():
    result = execute(
        "KA-1077",
        {
            "candidates": [
                {
                    "knowledge_id": "high",
                    "relevance": 1,
                    "confidence": 1,
                    "freshness": 1,
                    "reuse_count": 100,
                    "dependent_count": 20,
                },
                {
                    "knowledge_id": "low",
                    "relevance": 0,
                    "confidence": 0,
                    "freshness": 0,
                    "reuse_count": 0,
                    "dependent_count": 0,
                },
            ]
        },
    )

    assert result.success is True
    assert [row["knowledge_id"] for row in result.output["ranked_knowledge"]] == [
        "high",
        "low",
    ]
    assert result.output["ranked_knowledge"][0]["importance_score"] == 1


def test_ka_1078_memory_tier_classifier_separates_validated_and_disputed():
    result = execute(
        "KA-1078",
        {
            "candidates": [
                {
                    "knowledge_id": "approved",
                    "validation_status": "validated",
                    "importance": 0.9,
                    "confidence": 0.9,
                    "age_days": 5,
                    "reuse_count": 4,
                },
                {
                    "knowledge_id": "disputed",
                    "validation_status": "disputed",
                    "importance": 0.9,
                    "confidence": 0.9,
                    "age_days": 5,
                    "reuse_count": 4,
                },
            ]
        },
    )

    assert result.success is True
    assert result.output["classifications"] == [
        {
            "knowledge_id": "approved",
            "recommended_tier": "long_term",
            "reason": "validated_high_value",
        },
        {
            "knowledge_id": "disputed",
            "recommended_tier": "quarantine",
            "reason": "disputed",
        },
    ]
    assert result.output["tier_changes_applied"] is False


def test_ka_1082_confidence_drift_monitor_flags_declared_degradation():
    result = execute(
        "KA-1082",
        {
            "series": [
                {
                    "knowledge_id": "knowledge-1",
                    "observations": [
                        {
                            "observed_at": "2026-01-01T00:00:00Z",
                            "confidence": 0.9,
                        },
                        {
                            "observed_at": "2026-02-01T00:00:00Z",
                            "confidence": 0.7,
                        },
                    ],
                }
            ],
            "degradation_threshold": 0.1,
        },
    )

    assert result.success is True
    assert result.output["measurements"][0]["net_change"] == -0.2
    assert result.output["measurements"][0]["maximum_drawdown"] == 0.2
    assert result.output["measurements"][0]["degradation_detected"] is True
    assert result.output["measurement_status"] == "observational"


def test_ka_1083_revalidation_scheduler_makes_drift_immediately_due():
    result = execute(
        "KA-1083",
        {
            "reference_date": "2026-07-25",
            "candidates": [
                {
                    "knowledge_id": "knowledge-1",
                    "last_validated_on": "2026-07-20",
                    "risk_class": "low",
                    "confidence": 0.9,
                    "drift_detected": True,
                }
            ],
        },
    )

    assert result.success is True
    assert result.output["schedule"][0]["due_on"] == "2026-07-20"
    assert result.output["schedule"][0]["overdue"] is True
    assert result.output["jobs_scheduled"] == 0
    assert result.output["effect_service_required"] is True


def test_ka_1086_usage_analytics_aggregates_only_supplied_events():
    result = execute(
        "KA-1086",
        {
            "events": [
                {
                    "event_id": "event-1",
                    "knowledge_id": "knowledge-1",
                    "session_id": "session-1",
                    "occurred_at": "2026-07-25T00:00:00Z",
                    "action": "retrieved",
                    "successful": True,
                },
                {
                    "event_id": "event-2",
                    "knowledge_id": "knowledge-1",
                    "session_id": "session-2",
                    "occurred_at": "2026-07-25T01:00:00Z",
                    "action": "cited",
                    "successful": False,
                },
            ]
        },
    )

    assert result.success is True
    analytics = result.output["analytics"][0]
    assert analytics["event_count"] == 2
    assert analytics["success_ratio"] == 0.5
    assert analytics["unique_session_count"] == 2
    assert result.output["telemetry_collected"] is False


def test_ka_1088_lifecycle_manager_proposes_only_valid_next_transitions():
    result = execute(
        "KA-1088",
        {
            "records": [
                {
                    "knowledge_id": "candidate",
                    "current_state": "candidate",
                    "validation_passed": True,
                    "confidence": 0.9,
                },
                {
                    "knowledge_id": "disputed",
                    "current_state": "disputed",
                    "confidence": 0.5,
                },
            ]
        },
    )

    assert result.success is True
    assert [
        row["proposed_state"] for row in result.output["transition_plans"]
    ] == ["validated", "quarantined"]
    assert result.output["transitions_applied"] == 0
    assert result.output["effect_service_required"] is True
