from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = tuple(f"KA-{number}" for number in range(1089, 1097))


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_06_has_one_unique_implementation_owner_per_capability():
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


def test_ka_1089_policy_evolution_tracks_added_removed_and_changed_requirements():
    result = execute(
        "KA-1089",
        {
            "policy_id": "policy-1",
            "versions": [
                {
                    "version_id": "v1",
                    "effective_on": "2026-01-01",
                    "source_ref": "v1.pdf",
                    "requirements": [
                        {"requirement_id": "keep", "text": "Keep logs."},
                        {"requirement_id": "remove", "text": "Legacy rule."},
                    ],
                },
                {
                    "version_id": "v2",
                    "effective_on": "2026-06-01",
                    "source_ref": "v2.pdf",
                    "requirements": [
                        {"requirement_id": "keep", "text": "Keep protected logs."},
                        {"requirement_id": "add", "text": "Encrypt logs."},
                    ],
                },
            ],
        },
    )
    assert result.success is True
    change = result.output["changes"][0]
    assert change["added_requirement_ids"] == ["add"]
    assert change["removed_requirement_ids"] == ["remove"]
    assert change["changed_requirement_ids"] == ["keep"]
    assert result.output["policy_store_updated"] is False


def test_ka_1090_compliance_regression_detects_pass_to_fail():
    result = execute(
        "KA-1090",
        {
            "baseline": [
                {
                    "control_id": "AC-1",
                    "status": "pass",
                    "evidence_refs": ["baseline"],
                }
            ],
            "candidate": [
                {
                    "control_id": "AC-1",
                    "status": "fail",
                    "evidence_refs": ["candidate"],
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["regression_detected"] is True
    assert result.output["regressions"][0]["reasons"] == ["pass_to_fail"]
    assert result.output["candidate_accepted"] is False


def test_ka_1091_scenario_archivist_builds_stable_unapplied_object_plan():
    payload = {
        "outcomes": [
            {
                "scenario_id": "scenario-1",
                "outcome_id": "outcome-1",
                "status": "completed",
                "significance": 0.9,
                "summary": "Recovery completed.",
                "artifact_refs": ["artifact-1"],
            }
        ]
    }
    first = execute("KA-1091", payload)
    second = execute("KA-1091", payload)
    assert first.success is True
    assert first.output == second.output
    assert len(first.output["archive_plans"][0]["content_sha256"]) == 64
    assert first.output["artifacts_written"] == 0


def test_ka_1092_dependency_auditor_traces_bounded_downstream_impact():
    result = execute(
        "KA-1092",
        {
            "changed_knowledge_ids": ["a"],
            "known_knowledge_ids": ["a", "b", "c"],
            "dependencies": [
                {"upstream_id": "a", "downstream_id": "b"},
                {"upstream_id": "b", "downstream_id": "c"},
            ],
        },
    )
    assert result.success is True
    assert result.output["affected_knowledge_ids"] == ["b", "c"]
    assert [row["minimum_depth"] for row in result.output["downstream_impacts"]] == [
        1,
        2,
    ]
    assert result.output["mutation_applied"] is False


def test_ka_1093_trust_decay_applies_declared_half_life_without_update():
    result = execute(
        "KA-1093",
        {
            "reference_date": "2026-01-01",
            "half_life_days": 100,
            "records": [
                {
                    "knowledge_id": "knowledge-1",
                    "current_trust": 0.8,
                    "last_used_on": "2025-09-23",
                    "risk_class": "medium",
                    "active_evidence_count": 0,
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["proposals"][0]["unused_days"] == 100
    assert result.output["proposals"][0]["proposed_trust"] == 0.4
    assert result.output["trust_updates_applied"] is False


def test_ka_1094_quarantine_engine_requires_review_for_disputed_knowledge():
    result = execute(
        "KA-1094",
        {
            "candidates": [
                {
                    "knowledge_id": "knowledge-1",
                    "validation_status": "disputed",
                    "confidence": 0.7,
                    "contradiction_count": 1,
                    "integrity_valid": True,
                    "provenance_complete": True,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["decisions"][0]["decision"] == "quarantine"
    assert result.output["decisions"][0]["human_release_review_required"] is True
    assert result.output["records_moved"] == 0


def test_ka_1095_human_escalation_requires_owner_for_policy_exception():
    result = execute(
        "KA-1095",
        {
            "cases": [
                {
                    "case_id": "case-1",
                    "risk_class": "medium",
                    "confidence": 0.9,
                    "policy_exception": True,
                    "affected_subject_count": 1,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["decisions"][0]["review_level"] == "owner_and_specialist"
    assert result.output["reviews_dispatched"] == 0
    assert result.output["decision_applied"] is False


def test_ka_1096_release_manager_stages_only_complete_candidate():
    result = execute(
        "KA-1096",
        {
            "candidates": [
                {
                    "release_id": "release-1",
                    "knowledge_version_ids": ["knowledge-1:v2"],
                    "validation_status": "passed",
                    "required_approvals": 1,
                    "recorded_approvals": 1,
                    "dependencies_ready": True,
                    "rollback_plan_ref": "rollback-1",
                    "rollout_percent": 10,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["release_plans"][0]["decision"] == "stage"
    assert result.output["release_plans"][0]["blockers"] == []
    assert result.output["releases_activated"] == 0
