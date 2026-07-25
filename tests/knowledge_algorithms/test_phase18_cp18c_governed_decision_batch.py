from backend.knowledge_algorithms.controller import CanonicalKAController


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_ka_1072_context_optimizer_preserves_required_items_within_budget():
    result = execute(
        "KA-1072",
        {
            "context_elements": [
                {
                    "element_id": "required",
                    "token_count": 100,
                    "relevance": 1,
                    "required": True,
                },
                {
                    "element_id": "high",
                    "token_count": 200,
                    "relevance": 0.9,
                },
                {
                    "element_id": "low",
                    "token_count": 400,
                    "relevance": 0.1,
                },
            ],
            "token_budget": 350,
        },
    )

    assert result.success is True
    assert result.output["selected_element_ids"] == ["required", "high"]
    assert result.output["selected_token_count"] == 300
    assert result.output["selection_method"] == "required_then_utility_density"


def test_ka_1073_intent_clarifier_requires_missing_declared_slot():
    result = execute(
        "KA-1073",
        {
            "utterance": "restore backup",
            "candidate_intents": [
                {
                    "intent_id": "restore",
                    "description": "restore backup",
                    "keywords": ["restore", "backup"],
                    "required_slots": ["backup_id"],
                },
                {
                    "intent_id": "delete",
                    "description": "delete record",
                    "keywords": ["delete"],
                },
            ],
        },
    )

    assert result.success is True
    assert result.output["resolved_intent"] is None
    assert result.output["status"] == "clarification_required"
    assert result.output["clarification_questions"] == [
        {
            "code": "required_slot_missing",
            "slot": "backup_id",
            "prompt": "Provide backup_id.",
        }
    ]


def test_ka_1079_promotion_gate_approves_without_applying_promotion():
    result = execute(
        "KA-1079",
        {
            "knowledge_id": "knowledge-1",
            "validation_status": "validated",
            "confidence": 0.95,
            "evidence_count": 3,
            "citation_count": 2,
            "contradiction_count": 0,
            "provenance_complete": True,
            "risk_class": "medium",
        },
    )

    assert result.success is True
    assert result.output["decision"] == "approve"
    assert result.output["promotion_applied"] is False


def test_ka_1080_simulation_cost_estimator_applies_declared_contingency():
    result = execute(
        "KA-1080",
        {
            "planned_steps": [
                {
                    "step_id": "simulation",
                    "iterations": 10,
                    "estimated_ms_per_iteration": 50,
                    "estimated_tokens_per_iteration": 100,
                    "estimated_peak_memory_mb": 256,
                    "estimated_cost_per_iteration": 0.1,
                }
            ],
            "contingency_ratio": 0.2,
        },
    )

    assert result.success is True
    assert result.output["estimate"]["duration_ms"] == 600
    assert result.output["estimate"]["tokens"] == 1200
    assert result.output["estimate"]["cost_units"] == 1.2
    assert result.output["measurement_status"] == "caller_supplied_estimate"


def test_ka_1081_budget_enforcer_blocks_over_budget_without_execution():
    result = execute(
        "KA-1081",
        {
            "estimated_duration_ms": 2_000,
            "estimated_tokens": 1_000,
            "estimated_cost_units": 0,
            "estimated_peak_memory_mb": 256,
            "recursion_depth": 1,
            "concurrency": 1,
            "maximum_duration_ms": 1_000,
            "maximum_tokens": 2_000,
            "maximum_cost_units": 1,
            "maximum_peak_memory_mb": 512,
            "maximum_recursion_depth": 3,
            "maximum_concurrency": 2,
        },
    )

    assert result.success is True
    assert result.output["allowed"] is False
    assert result.output["violations"][0]["budget"] == "duration"
    assert result.output["execution_started"] is False


def test_ka_1084_consensus_engine_measures_agreement_not_truth():
    result = execute(
        "KA-1084",
        {
            "instance_answers": [
                {"instance_id": "a", "answer": "Approved"},
                {"instance_id": "b", "answer": " approved "},
                {"instance_id": "c", "answer": "Rejected"},
            ],
            "consensus_threshold": 0.66,
        },
    )

    assert result.success is True
    assert result.output["consensus_reached"] is True
    assert result.output["agreement_ratio"] == 0.66666667
    assert result.output["measurement_status"] == "agreement_only"


def test_ka_1085_anomaly_engine_flags_declared_z_score_threshold():
    result = execute(
        "KA-1085",
        {
            "baselines": [
                {
                    "feature": "reasoning_steps",
                    "mean": 10,
                    "standard_deviation": 2,
                    "warning_z": 3,
                }
            ],
            "observations": [
                {
                    "observation_id": "run-1",
                    "features": {"reasoning_steps": 20},
                }
            ],
        },
    )

    assert result.success is True
    assert result.output["anomaly_count"] == 1
    assert result.output["observations"][0]["flags"][0]["z_score"] == 5
    assert result.output["measurement_status"] == "statistical_deviation_only"


def test_ka_1087_explainability_checker_requires_step_evidence_link():
    result = execute(
        "KA-1087",
        {
            "critical_steps": [
                {
                    "step_id": "s1",
                    "description": "Validate source",
                    "required_evidence_refs": ["e1"],
                }
            ],
            "explanation_segments": [
                {
                    "segment_id": "x1",
                    "text": "The source was reviewed.",
                    "covers_step_ids": ["s1"],
                    "evidence_refs": [],
                }
            ],
        },
    )

    assert result.success is True
    assert result.output["coverage_complete"] is False
    assert result.output["step_coverage"][0]["missing_evidence_refs"] == ["e1"]
    assert result.output["explanation_generated"] is False
