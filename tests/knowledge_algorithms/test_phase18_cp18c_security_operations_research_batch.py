from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = (
    "KA-179",
    "KA-180",
    "KA-181",
    "KA-182",
    "KA-183",
    "KA-184",
    "KA-1114",
)


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_11_has_one_unique_implementation_owner_per_capability():
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


def test_ka_179_access_control_allows_matching_role_and_attribute_rule():
    result = execute(
        "KA-179",
        {
            "subject_id": "owner",
            "roles": ["owner"],
            "attributes": {"tenant": "local"},
            "action": "read",
            "resource_type": "trace",
            "rules": [
                {
                    "rule_id": "owner-read",
                    "actions": ["read"],
                    "resource_types": ["trace"],
                    "required_roles": ["owner"],
                    "required_attributes": {"tenant": "local"},
                    "effect": "allow",
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["decision"] == "allow"
    assert result.output["access_applied"] is False


def test_ka_180_encryption_manager_admits_metadata_only_crypto_request():
    result = execute(
        "KA-180",
        {
            "requests": [
                {
                    "request_id": "enc-1",
                    "operation": "encrypt",
                    "object_ref": "artifact-1",
                    "key_ref": "key-1",
                    "algorithm": "AES-256-GCM",
                    "purpose": "at-rest protection",
                    "caller_authorized": True,
                    "key_active": True,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["plans"][0]["decision"] == "admit"
    assert result.output["plaintext_or_key_material_processed"] is False
    assert result.output["operations_applied"] == 0


def test_ka_181_key_management_proposes_rotation_without_returning_key_material():
    result = execute(
        "KA-181",
        {
            "evaluation_date": "2026-07-25",
            "keys": [
                {
                    "key_ref": "key-1",
                    "status": "active",
                    "created_on": "2026-01-01",
                    "rotate_by": "2026-07-01",
                    "protected_storage_verified": True,
                    "usage_count": 100,
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["actions"][0]["proposed_action"] == "rotate"
    assert result.output["key_material_returned"] is False
    assert result.output["actions_applied"] == 0


def test_ka_182_threat_detection_alerts_on_trusted_threshold_signal():
    result = execute(
        "KA-182",
        {
            "signals": [
                {
                    "signal_id": "s1",
                    "signal_type": "authentication_failure",
                    "observed_count": 10,
                    "threshold": 5,
                    "source_ref": "security-log-1",
                    "trusted_source": True,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["threat_detected"] is True
    assert result.output["alerts"][0]["severity"] == "high"


def test_ka_183_vulnerability_scanning_blocks_open_high_finding_without_scanning():
    result = execute(
        "KA-183",
        {
            "findings": [
                {
                    "finding_id": "CVE-1",
                    "component_ref": "package-a@1",
                    "severity": "high",
                    "status": "open",
                    "scanner_ref": "scan-1",
                    "fixed_version": "2",
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["release_blocked"] is True
    assert result.output["scans_executed"] == 0


def test_ka_184_incident_response_builds_ordered_unapplied_plan():
    result = execute(
        "KA-184",
        {
            "incidents": [
                {
                    "incident_id": "inc-1",
                    "severity": "critical",
                    "incident_type": "data_exposure",
                    "affected_asset_refs": ["store-1"],
                    "owner_assigned": True,
                    "containment_ready": True,
                    "evidence_preservation_ready": True,
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["plans"][0]["decision"] == "activate_plan"
    assert "notify_required_stakeholders" in result.output["plans"][0]["ordered_steps"]
    assert result.output["actions_applied"] == 0


def test_ka_1114_deep_research_builds_bounded_request_without_network_or_memory():
    result = execute(
        "KA-1114",
        {
            "sub_question": "What primary evidence supports the claim?",
            "allowed_domains": ["nist.gov"],
            "maximum_sources": 10,
            "timebox_seconds": 300,
            "connector_id": "research-provider",
            "connector_approved": True,
            "policy_approved": True,
            "human_approved": True,
        },
    )
    assert result.success is True
    assert result.output["decision"] == "admit"
    assert result.output["research_request"]["memory_write_allowed"] is False
    assert result.output["provider_called"] is False
    assert result.output["network_accessed"] is False
    assert result.output["memory_written"] is False
