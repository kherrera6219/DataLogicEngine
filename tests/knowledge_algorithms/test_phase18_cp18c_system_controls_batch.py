from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = tuple(f"KA-{number}" for number in range(1097, 1105))


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_07_has_one_unique_implementation_owner_per_capability():
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


def test_ka_1097_performance_optimizer_proposes_bounded_unapplied_adjustment():
    result = execute(
        "KA-1097",
        {
            "metrics": [
                {
                    "component_id": "retrieval",
                    "metric": "latency_ms",
                    "observed": 200,
                    "target_maximum": 100,
                    "current_setting": 4,
                    "minimum_setting": 1,
                    "maximum_setting": 8,
                }
            ],
            "maximum_adjustment_ratio": 0.25,
        },
    )
    assert result.success is True
    assert result.output["proposals"][0]["proposed_setting"] == 5
    assert result.output["settings_applied"] == 0


def test_ka_1098_self_evaluation_aggregates_supplied_benchmark_results():
    result = execute(
        "KA-1098",
        {
            "results": [
                {
                    "case_id": "case-1",
                    "suite": "retrieval",
                    "passed": True,
                    "score": 0.9,
                    "latency_ms": 100,
                },
                {
                    "case_id": "case-2",
                    "suite": "retrieval",
                    "passed": False,
                    "score": 0.7,
                    "latency_ms": 200,
                },
            ],
            "minimum_pass_ratio": 0.5,
            "minimum_mean_score": 0.8,
        },
    )
    assert result.success is True
    assert result.output["suite_results"][0]["pass_ratio"] == 0.5
    assert result.output["suite_results"][0]["mean_score"] == 0.8
    assert result.output["benchmarks_executed"] is False


def test_ka_1099_system_integrity_flags_hash_and_dependency_failures():
    result = execute(
        "KA-1099",
        {
            "components": [
                {
                    "component_id": "api",
                    "status": "degraded",
                    "expected_sha256": "a" * 64,
                    "observed_sha256": "b" * 64,
                },
                {
                    "component_id": "worker",
                    "status": "ready",
                    "required_dependency_ids": ["api"],
                },
            ]
        },
    )
    assert result.success is True
    assert result.output["integrity_valid"] is False
    assert result.output["findings"][0]["reasons"] == [
        "status_degraded",
        "hash_mismatch",
    ]
    assert result.output["findings"][1]["reasons"] == ["dependency_not_ready"]


def test_ka_1100_system_evolution_requires_human_approval_for_algorithm_change():
    result = execute(
        "KA-1100",
        {
            "proposals": [
                {
                    "proposal_id": "proposal-1",
                    "change_class": "algorithm",
                    "validation_passed": True,
                    "rollback_plan_ref": "rollback-1",
                    "affected_capability_count": 1,
                    "expected_improvement": 0.2,
                    "risk_score": 0.1,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["decisions"][0]["decision"] == "block"
    assert result.output["decisions"][0]["blockers"] == [
        "human_approval_required"
    ]
    assert result.output["changes_applied"] == 0


def test_ka_1101_chaos_governor_approves_safe_plan_without_injecting_fault():
    result = execute(
        "KA-1101",
        {
            "proposals": [
                {
                    "proposal_id": "chaos-1",
                    "environment": "test",
                    "fault_type": "latency",
                    "target_service": "redis",
                    "magnitude": 0.1,
                    "duration_seconds": 30,
                    "rollback_verified": True,
                    "monitoring_ready": True,
                }
            ],
            "allowed_services": ["redis"],
        },
    )
    assert result.success is True
    assert result.output["decisions"][0]["decision"] == "approve_plan"
    assert result.output["faults_injected"] == 0


def test_ka_1102_global_entropy_quantifies_even_distribution():
    result = execute(
        "KA-1102",
        {
            "categories": [
                {"category": "a", "count": 5},
                {"category": "b", "count": 5},
            ]
        },
    )
    assert result.success is True
    assert result.output["entropy_bits"] == 1
    assert result.output["normalized_entropy"] == 1


def test_ka_1103_simulation_rollback_approves_verified_ancestor_without_applying():
    result = execute(
        "KA-1103",
        {
            "simulation_id": "simulation-1",
            "current_checkpoint_id": "c2",
            "target_checkpoint_id": "c1",
            "checkpoints": [
                {
                    "checkpoint_id": "c1",
                    "sequence": 1,
                    "state_sha256": "a" * 64,
                    "verified": True,
                },
                {
                    "checkpoint_id": "c2",
                    "sequence": 2,
                    "state_sha256": "b" * 64,
                    "parent_checkpoint_id": "c1",
                    "verified": True,
                },
            ],
        },
    )
    assert result.success is True
    assert result.output["decision"] == "approve_plan"
    assert result.output["rollback_path"] == ["c2", "c1"]
    assert result.output["rollback_applied"] is False


def test_ka_1104_truth_utility_arbiter_never_relaxes_truth_floor():
    result = execute(
        "KA-1104",
        {
            "options": [
                {
                    "option_id": "truthful",
                    "truth_confidence": 0.9,
                    "utility_score": 0.7,
                    "harm_risk": 0.1,
                    "evidence_refs": ["evidence-1"],
                },
                {
                    "option_id": "useful-but-unsupported",
                    "truth_confidence": 0.4,
                    "utility_score": 1.0,
                    "harm_risk": 0.1,
                    "evidence_refs": ["evidence-2"],
                },
            ]
        },
    )
    assert result.success is True
    assert result.output["selected_option_id"] == "truthful"
    assert result.output["truth_floor_relaxed"] is False
    assert result.output["decision_applied"] is False
