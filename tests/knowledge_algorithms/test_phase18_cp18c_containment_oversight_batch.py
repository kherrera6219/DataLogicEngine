from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = tuple(f"KA-{number}" for number in range(1105, 1113))


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_08_has_one_unique_implementation_owner_per_capability():
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


def test_ka_1105_conceptual_obsolescence_requires_paradigm_level_evidence():
    result = execute(
        "KA-1105",
        {
            "concepts": [
                {
                    "concept_id": "legacy-control",
                    "baseline_contradiction_rate": 0.1,
                    "current_contradiction_rate": 0.7,
                    "active_citation_count": 0,
                    "superseding_policy_refs": ["policy-v2"],
                    "paradigm_replacement_refs": ["model-v2"],
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["assessments"][0]["classification"] == (
        "obsolescence_candidate"
    )
    assert result.output["requests_dispatched"] == 0
    assert result.output["knowledge_updated"] is False


def test_ka_1106_human_override_capture_builds_stable_unapplied_signal():
    payload = {
        "overrides": [
            {
                "override_id": "override-1",
                "decision_ref": "decision-1",
                "original_outcome": "deny",
                "corrected_outcome": "review",
                "reason_code": "context_missing",
                "rationale": "Required owner context was unavailable.",
                "reviewer_role": "owner",
                "evidence_refs": ["trace-1"],
            }
        ]
    }
    first = execute("KA-1106", payload)
    second = execute("KA-1106", payload)
    assert first.success is True
    assert first.output == second.output
    assert len(first.output["records"][0]["training_signal_sha256"]) == 64
    assert first.output["training_updates_applied"] == 0


def test_ka_1107_reasoning_boundary_blocks_unauthorized_layer_entry():
    result = execute(
        "KA-1107",
        {
            "planned_steps": [
                {
                    "step_id": "step-1",
                    "capability_id": "KA-001",
                    "layer": "L7",
                    "query_class": "analysis",
                }
            ],
            "allowed_capability_ids": ["KA-001"],
            "allowed_layers": ["L1"],
            "allowed_query_classes": ["analysis"],
        },
    )
    assert result.success is True
    assert result.output["plan_allowed"] is False
    assert result.output["decisions"][0]["blockers"] == ["layer_not_allowed"]


def test_ka_1108_capability_escalation_flags_privilege_boundary_crossing():
    result = execute(
        "KA-1108",
        {
            "interactions": [
                {
                    "interaction_id": "interaction-1",
                    "source_capability_id": "KA-001",
                    "target_capability_id": "KA-002",
                    "observed_invocations": 5,
                    "authorized_invocations": 2,
                    "crossed_privilege_boundary": True,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["escalation_detected"] is True
    assert result.output["alerts"][0]["severity"] == "critical"
    assert result.output["containment_actions_applied"] == 0


def test_ka_1109_containment_classifier_denies_unconsented_personal_data():
    result = execute(
        "KA-1109",
        {
            "candidates": [
                {
                    "knowledge_id": "knowledge-1",
                    "declared_sensitivity": "restricted",
                    "contains_personal_data": True,
                    "consent_verified": False,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["decisions"][0]["containment_class"] == "never_persist"
    assert result.output["decisions"][0]["persistence_rule"] == "deny"
    assert result.output["persistence_actions_applied"] == 0


def test_ka_1110_cross_domain_coupling_blocks_unauthorized_critical_link():
    result = execute(
        "KA-1110",
        {
            "links": [
                {
                    "link_id": "link-1",
                    "source_domain": "public",
                    "target_domain": "restricted",
                    "sensitivity": "critical",
                    "authorized": False,
                    "planned_capability_ids": ["KA-001"],
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["assessments"][0]["risk_score"] == 1
    assert result.output["assessments"][0]["decision"] == "block"
    assert result.output["blocks_applied"] == 0


def test_ka_1111_long_horizon_monitor_flags_recurring_undeclared_goal():
    result = execute(
        "KA-1111",
        {
            "traces": [
                {
                    "run_id": "run-1",
                    "sequence": 1,
                    "declared_goal_ids": ["owner-goal"],
                    "observed_goal_ids": ["owner-goal", "latent-goal"],
                },
                {
                    "run_id": "run-2",
                    "sequence": 2,
                    "declared_goal_ids": ["owner-goal"],
                    "observed_goal_ids": ["owner-goal", "latent-goal"],
                },
            ]
        },
    )
    assert result.success is True
    assert result.output["drift_detected"] is True
    assert result.output["alerts"][0]["goal_id"] == "latent-goal"
    assert result.output["constraints_applied"] == 0


def test_ka_1112_self_introspection_reports_missing_override_reason():
    result = execute(
        "KA-1112",
        {
            "windows": [
                {
                    "window_id": "window-1",
                    "chaos_plan_count": 2,
                    "unapproved_chaos_count": 0,
                    "human_override_count": 3,
                    "override_without_reason_count": 1,
                    "drift_alert_count": 1,
                    "unresolved_drift_count": 0,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["audit_passed"] is False
    assert result.output["findings"][0]["finding"] == "override_reason_missing"
    assert result.output["governance_actions_applied"] == 0
