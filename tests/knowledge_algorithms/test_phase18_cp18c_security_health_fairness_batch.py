from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = (
    "KA-136",
    "KA-137",
    "KA-138",
    "KA-139",
    "KA-169",
    "KA-172",
    "KA-173",
    "KA-174",
)


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_09_has_one_unique_implementation_owner_per_capability():
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


def test_ka_136_threat_model_finds_unencrypted_boundary_flow():
    result = execute(
        "KA-136",
        {
            "assets": [
                {
                    "asset_id": "gateway",
                    "criticality": "critical",
                    "privileged": True,
                },
                {
                    "asset_id": "store",
                    "criticality": "critical",
                    "stores_sensitive_data": True,
                },
            ],
            "data_flows": [
                {
                    "flow_id": "flow-1",
                    "source_asset_id": "gateway",
                    "target_asset_id": "store",
                    "crosses_trust_boundary": True,
                    "authenticated": True,
                    "encrypted": False,
                    "integrity_protected": True,
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["findings"][0]["threat"] == "information_disclosure"
    assert result.output["tests_or_controls_applied"] == 0


def test_ka_137_sensitive_data_discovery_returns_location_not_value():
    result = execute(
        "KA-137",
        {
            "documents": [
                {
                    "document_id": "document-1",
                    "text": "Contact owner@example.com.",
                }
            ],
            "detect_types": ["email"],
        },
    )
    assert result.success is True
    assert result.output["findings"][0]["data_type"] == "email"
    assert result.output["matched_values_returned"] is False
    assert "owner@example.com" not in str(result.output)


def test_ka_138_predictive_health_projects_declared_linear_trend():
    result = execute(
        "KA-138",
        {
            "series": [
                {
                    "component_id": "worker",
                    "metric": "queue_depth",
                    "values": [10, 20, 30],
                    "warning_threshold": 35,
                    "critical_threshold": 50,
                }
            ],
            "forecast_steps": 2,
        },
    )
    assert result.success is True
    assert result.output["forecasts"][0]["projected_value"] == 50
    assert result.output["forecasts"][0]["classification"] == "critical"
    assert result.output["measurement_status"] == "caller_supplied"


def test_ka_139_purple_team_reports_missing_response_control_without_attack():
    result = execute(
        "KA-139",
        {
            "scenarios": [
                {
                    "scenario_id": "scenario-1",
                    "technique_id": "T1001",
                    "severity": "high",
                    "expected_detection_control_ids": ["detect-1"],
                    "expected_response_control_ids": ["respond-1"],
                }
            ],
            "observed_control_ids": ["detect-1"],
        },
    )
    assert result.success is True
    assert result.output["assessments"][0]["coverage_ratio"] == 0.5
    assert result.output["assessments"][0]["missing_control_ids"] == ["respond-1"]
    assert result.output["adversarial_actions_executed"] == 0


def test_ka_169_fairness_audit_measures_group_disparity():
    result = execute(
        "KA-169",
        {
            "groups": [
                {
                    "group_id": "a",
                    "sample_count": 100,
                    "positive_outcome_count": 50,
                    "qualified_count": 50,
                    "qualified_positive_count": 40,
                },
                {
                    "group_id": "b",
                    "sample_count": 100,
                    "positive_outcome_count": 30,
                    "qualified_count": 50,
                    "qualified_positive_count": 25,
                },
            ],
            "maximum_allowed_disparity": 0.1,
        },
    )
    assert result.success is True
    assert result.output["demographic_parity_disparity"] == 0.2
    assert result.output["equal_opportunity_disparity"] == 0.3
    assert result.output["audit_passed"] is False


def test_ka_172_safety_check_blocks_high_risk_candidate_without_review():
    result = execute(
        "KA-172",
        {
            "candidates": [
                {
                    "candidate_id": "candidate-1",
                    "risk_level": "high",
                    "hazard_ids": ["hazard-1"],
                    "required_safeguard_ids": ["guard-1"],
                    "verified_safeguard_ids": ["guard-1"],
                    "human_reviewed": False,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["decisions"][0]["decision"] == "block"
    assert result.output["decisions"][0]["blockers"] == ["human_review_required"]


def test_ka_173_privacy_filter_removes_declared_values_from_output():
    result = execute(
        "KA-173",
        {
            "text": "Contact Alice at owner@example.com.",
            "sensitive_values": [
                {"label": "name", "value": "Alice"},
                {"label": "email", "value": "owner@example.com"},
            ],
        },
    )
    assert result.success is True
    assert result.output["filtered_text"] == (
        "Contact [REDACTED_NAME] at [REDACTED_EMAIL]."
    )
    assert "Alice" not in str(result.output)
    assert "owner@example.com" not in str(result.output)
    assert result.output["source_values_returned"] is False


def test_ka_174_compliance_check_requires_current_implementation_and_evidence():
    result = execute(
        "KA-174",
        {
            "controls": [
                {
                    "control_id": "AC-1",
                    "applicability": "applicable",
                    "implementation_status": "implemented",
                    "required_evidence_types": ["test"],
                    "evidence": {"test": ["test-report-1"]},
                },
                {
                    "control_id": "AC-2",
                    "applicability": "applicable",
                    "implementation_status": "partial",
                    "required_evidence_types": ["review"],
                },
            ]
        },
    )
    assert result.success is True
    assert [row["status"] for row in result.output["assessments"]] == [
        "pass",
        "fail",
    ]
    assert result.output["certification_claimed"] is False
