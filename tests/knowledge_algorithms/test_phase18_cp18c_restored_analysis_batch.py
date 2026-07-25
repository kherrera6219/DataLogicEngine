from backend.knowledge_algorithms.controller import CanonicalKAController


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_ka_1036_pareto_optimization_returns_only_non_dominated_options():
    result = execute(
        "KA-1036",
        {
            "objectives": [
                {
                    "name": "accuracy",
                    "direction": "maximize",
                    "weight": 2,
                },
                {
                    "name": "cost",
                    "direction": "minimize",
                    "weight": 1,
                },
            ],
            "options": [
                {
                    "option_id": "a",
                    "metrics": {"accuracy": 0.9, "cost": 10},
                },
                {
                    "option_id": "b",
                    "metrics": {"accuracy": 0.8, "cost": 5},
                },
                {
                    "option_id": "c",
                    "metrics": {"accuracy": 0.7, "cost": 12},
                },
            ],
        },
    )

    assert result.success is True
    assert set(result.output["pareto_front"]) == {"a", "b"}
    assert "c" not in result.output["pareto_front"]
    assert result.output["deterministic"] is True


def test_ka_1037_norm_emergence_reports_measured_convergence_only():
    result = execute(
        "KA-1037",
        {
            "persona_outputs": [
                {
                    "persona_id": "knowledge",
                    "content": "Adopt the validated option now.",
                    "position": "adopt",
                },
                {
                    "persona_id": "sector",
                    "content": "Adopt the validated option now.",
                    "position": "adopt",
                },
                {
                    "persona_id": "regulatory",
                    "content": "Adopt the validated option now.",
                    "position": "adopt",
                },
            ]
        },
    )

    assert result.success is True
    assert result.output["unhealthy_convergence_suspected"] is True
    assert {item["code"] for item in result.output["norm_flags"]} == {
        "position_concentration",
        "language_convergence",
    }
    assert result.output["measurement_status"] == "observational"


def test_ka_1038_cross_modal_synthesis_preserves_source_provenance():
    result = execute(
        "KA-1038",
        {
            "evidence": [
                {
                    "evidence_id": "text-1",
                    "modality": "text",
                    "extracted_content": "Revenue increased.",
                    "claims": ["Revenue increased Q2"],
                    "source_ref": "report.txt",
                },
                {
                    "evidence_id": "table-1",
                    "modality": "table",
                    "extracted_content": "Q2 revenue: 120",
                    "claims": ["Q2 revenue increased"],
                    "source_ref": "ledger.csv",
                },
            ]
        },
    )

    assert result.success is True
    assert result.output["cross_modal_claim_count"] == 1
    claim = result.output["unified_evidence"]["claims"][0]
    assert claim["evidence_ids"] == ["table-1", "text-1"]
    assert claim["modalities"] == ["table", "text"]
    assert result.output["extraction_performed"] is False


def test_ka_1041_confidence_normalization_respects_declared_scales():
    result = execute(
        "KA-1041",
        {
            "confidence_vectors": [
                {
                    "concept_id": "control-a",
                    "domain": "percent",
                    "value": 80,
                    "scale_minimum": 0,
                    "scale_maximum": 100,
                },
                {
                    "concept_id": "control-a",
                    "domain": "five-point",
                    "value": 4,
                    "scale_minimum": 0,
                    "scale_maximum": 5,
                },
            ]
        },
    )

    assert result.success is True
    assert result.output["normalized_confidence"][0]["normalized_confidence"] == 0.8
    assert result.output["calibrated_probability"] is False


def test_ka_1042_contradiction_propagation_traces_bounded_paths():
    result = execute(
        "KA-1042",
        {
            "conflicts": [
                {
                    "conflict_id": "conflict-1",
                    "node_id": "claim-a",
                    "severity": 1,
                }
            ],
            "dependency_graph": [
                {"upstream": "claim-a", "downstream": "claim-b"},
                {"upstream": "claim-b", "downstream": "claim-c"},
            ],
            "decay_per_hop": 0.5,
        },
    )

    assert result.success is True
    assert result.output["priority_fixes"][0] == {
        "node_id": "claim-b",
        "impact": 0.5,
        "source_conflict_id": "conflict-1",
        "depth": 1,
    }
    assert result.output["affected_node_count"] == 2
    assert result.output["cycle_detected"] is False


def test_ka_1045_bias_pattern_analyzer_reports_observational_disparity():
    result = execute(
        "KA-1045",
        {
            "outputs_corpus": [
                {"record_id": "a1", "group": "a", "outcome": 1},
                {"record_id": "a2", "group": "a", "outcome": 1},
                {"record_id": "b1", "group": "b", "outcome": 0},
                {"record_id": "b2", "group": "b", "outcome": 0},
            ],
            "reference_group": "a",
            "disparity_threshold": 0.5,
        },
    )

    assert result.success is True
    assert result.output["bias_patterns"][0]["group"] == "b"
    assert result.output["bias_patterns"][0]["absolute_disparity"] == 1
    assert result.output["measurement_status"] == "observational"


def test_ka_1047_meta_algorithm_selection_uses_only_approved_candidates():
    result = execute(
        "KA-1047",
        {
            "problem_signature": "retrieve and validate governed evidence",
            "required_capabilities": ["retrieval", "validation"],
            "performance_history": [
                {
                    "canonical_id": "KA-079",
                    "version": "1.0.0",
                    "capabilities": ["retrieval", "validation"],
                    "quality_score": 0.9,
                    "success_rate": 0.95,
                    "p95_latency_ms": 100,
                    "risk_class": "low",
                },
                {
                    "canonical_id": "KA-050",
                    "version": "1.0.0",
                    "capabilities": ["summarization"],
                    "quality_score": 0.99,
                    "success_rate": 0.99,
                    "p95_latency_ms": 50,
                    "risk_class": "low",
                },
            ],
        },
    )

    assert result.success is True
    assert result.output["selection_complete"] is True
    assert [item["canonical_id"] for item in result.output["tuned_pipeline"]] == [
        "KA-079"
    ]
    assert result.output["candidate_new_ka_config"] is None
    assert result.output["execution_started"] is False


def test_ka_1049_redundancy_detector_finds_exact_normalized_duplicate():
    result = execute(
        "KA-1049",
        {
            "knowledge_nodes": [
                {"node_id": "a", "content": "Validated control evidence"},
                {
                    "node_id": "b",
                    "content": "  validated   control evidence ",
                },
                {"node_id": "c", "content": "Unrelated operational note"},
            ],
            "similarity_threshold": 0.9,
        },
    )

    assert result.success is True
    assert result.output["merge_candidates"] == [
        {
            "left_node_id": "a",
            "right_node_id": "b",
            "redundancy_score": 1,
            "method": "normalized_exact_match",
            "exact_duplicate": True,
        }
    ]
    assert result.output["mutation_applied"] is False
