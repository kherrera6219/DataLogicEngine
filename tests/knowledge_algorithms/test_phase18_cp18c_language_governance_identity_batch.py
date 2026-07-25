from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = (
    "KA-161",
    "KA-162",
    "KA-163",
    "KA-165",
    "KA-167",
    "KA-168",
    "KA-175",
    "KA-176",
    "KA-177",
    "KA-178",
)


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_10_has_one_unique_implementation_owner_per_capability():
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


def test_ka_161_translation_assembles_provenanced_accepted_segments():
    result = execute(
        "KA-161",
        {
            "source_language": "en",
            "target_language": "es",
            "segments": [
                {
                    "segment_id": "s1",
                    "source_text": "Hello",
                    "translated_text": "Hola",
                    "evidence_ref": "provider-output-1",
                    "confidence": 0.95,
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["translated_text"] == "Hola"
    assert result.output["provider_called"] is False


def test_ka_162_paraphrasing_selects_changed_candidate_with_required_terms():
    result = execute(
        "KA-162",
        {
            "source_text": "The service must retain audit logs.",
            "required_terms": ["service", "audit logs"],
            "candidates": [
                {
                    "candidate_id": "p1",
                    "text": "Audit logs must be retained by the service.",
                    "evidence_ref": "provider-output-1",
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["selected_candidate_id"] == "p1"


def test_ka_163_style_transfer_applies_transparent_plain_language_rules():
    result = execute(
        "KA-163",
        {
            "text": "Utilize the system in order to complete the task.",
            "target_style": "plain",
        },
    )
    assert result.success is True
    assert result.output["styled_text"] == "use the system to complete the task."
    assert result.output["content_generated"] is False


def test_ka_165_topic_modeling_returns_auditable_hinted_term_counts():
    result = execute(
        "KA-165",
        {
            "documents": [
                {
                    "document_id": "d1",
                    "text": "audit evidence controls audit",
                    "topic_hint": "governance",
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["topics"][0]["terms"][0] == {"term": "audit", "count": 2}
    assert result.output["method"] == "hinted_term_frequency"


def test_ka_167_keyword_extraction_ranks_repeat_term_first():
    result = execute(
        "KA-167",
        {
            "documents": [
                {"document_id": "d1", "text": "audit evidence audit"},
                {"document_id": "d2", "text": "security evidence"},
            ],
            "keywords_per_document": 2,
        },
    )
    assert result.success is True
    assert result.output["documents"][0]["keywords"][0]["term"] == "audit"
    assert result.output["method"] == "tf_idf"


def test_ka_168_explainability_links_ranked_factor_to_evidence():
    result = execute(
        "KA-168",
        {
            "decision_id": "decision-1",
            "outcome": "review",
            "factors": [
                {
                    "factor_id": "risk",
                    "label": "Risk threshold exceeded",
                    "contribution": 0.8,
                    "evidence_refs": ["trace-1"],
                }
            ],
        },
    )
    assert result.success is True
    assert result.output["explanation"]["factors"][0]["evidence_refs"] == ["trace-1"]
    assert result.output["factors_inferred"] == 0


def test_ka_175_security_audit_fails_untested_control_without_scanning():
    result = execute(
        "KA-175",
        {
            "controls": [
                {
                    "control_id": "AC-1",
                    "control_family": "access",
                    "enabled": True,
                    "tested": False,
                    "evidence_refs": [],
                    "severity_if_missing": "critical",
                }
            ]
        },
    )
    assert result.success is True
    assert result.output["audit_passed"] is False
    assert result.output["scans_executed"] == 0


def test_ka_176_governance_validation_requires_declared_approval_roles():
    result = execute(
        "KA-176",
        {
            "decisions": [
                {
                    "decision_id": "d1",
                    "risk_class": "high",
                    "policy_refs": ["policy-1"],
                    "evidence_refs": ["trace-1"],
                    "approval_roles": ["owner"],
                    "owner_recorded": True,
                }
            ],
            "required_approval_roles": {"high": ["owner", "security"]},
        },
    )
    assert result.success is True
    assert result.output["assessments"][0]["valid"] is False
    assert result.output["assessments"][0]["missing_approval_roles"] == ["security"]


def test_ka_177_policy_enforcement_uses_deny_overrides_without_applying_effect():
    result = execute(
        "KA-177",
        {
            "attributes": {"risk": "high"},
            "rules": [
                {
                    "rule_id": "allow-risk",
                    "attribute": "risk",
                    "operator": "equals",
                    "expected": "high",
                    "effect": "allow",
                },
                {
                    "rule_id": "deny-high",
                    "attribute": "risk",
                    "operator": "equals",
                    "expected": "high",
                    "effect": "deny",
                },
            ],
        },
    )
    assert result.success is True
    assert result.output["decision"] == "deny"
    assert result.output["effect_applied"] is False


def test_ka_178_identity_resolution_merges_only_verified_exact_identifier():
    result = execute(
        "KA-178",
        {
            "records": [
                {
                    "record_id": "r1",
                    "identifiers": [
                        {
                            "identifier_type": "email",
                            "value": "Owner@Example.com",
                            "verified": True,
                        }
                    ],
                },
                {
                    "record_id": "r2",
                    "identifiers": [
                        {
                            "identifier_type": "email",
                            "value": "owner@example.com",
                            "verified": True,
                        }
                    ],
                },
            ]
        },
    )
    assert result.success is True
    assert result.output["clusters"][0]["record_ids"] == ["r1", "r2"]
    assert result.output["records_merged"] == 0
