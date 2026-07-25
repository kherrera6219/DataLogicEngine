from backend.knowledge_algorithms.controller import CanonicalKAController

BATCH_IDS = (
    "KA-1039",
    "KA-1040",
    "KA-1043",
    "KA-1044",
    "KA-1046",
    "KA-1048",
)


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_batch_04_has_one_unique_implementation_owner_per_capability():
    controller = CanonicalKAController()
    definitions = [controller.get_definition(ka_id) for ka_id in BATCH_IDS]
    modules = [
        definition.implementation.entrypoint.module
        for definition in definitions
        if definition.implementation.entrypoint is not None
    ]

    assert [definition.canonical_id for definition in definitions] == list(BATCH_IDS)
    assert len(modules) == len(BATCH_IDS)
    assert len(modules) == len(set(modules))
    assert all(not definition.aliases["unscoped"] for definition in definitions)


def test_ka_1039_ontology_drift_reports_definition_and_hierarchy_changes():
    result = execute(
        "KA-1039",
        {
            "baseline_version": "v1",
            "current_version": "v2",
            "baseline_concepts": [
                {
                    "concept_id": "control",
                    "label": "Control",
                    "definition": "A documented risk reduction measure",
                    "parent_ids": ["governance"],
                }
            ],
            "current_concepts": [
                {
                    "concept_id": "control",
                    "label": "Verified Control",
                    "definition": "An independently tested safeguard",
                    "parent_ids": ["assurance"],
                },
                {
                    "concept_id": "evidence",
                    "label": "Evidence",
                    "definition": "A retained verification artifact",
                },
            ],
            "definition_drift_threshold": 0.3,
        },
    )

    assert result.success is True
    assert result.output["drift_detected"] is True
    assert result.output["added_concept_ids"] == ["evidence"]
    assert result.output["concept_drift"][0]["parents_added"] == ["assurance"]
    assert result.output["concept_drift"][0]["definition_threshold_exceeded"] is True
    assert result.output["mutation_applied"] is False


def test_ka_1040_semantic_alignment_uses_declared_synonym_overlap():
    result = execute(
        "KA-1040",
        {
            "concepts": [
                {
                    "concept_id": "client",
                    "label": "Client",
                    "synonyms": ["customer"],
                },
                {
                    "concept_id": "customer",
                    "label": "Customer",
                    "synonyms": ["client"],
                },
                {
                    "concept_id": "supplier",
                    "label": "Supplier",
                },
            ],
            "alignment_threshold": 0.8,
        },
    )

    assert result.success is True
    assert result.output["alignment_proposals"] == [
        {
            "canonical_concept_id": "client",
            "aligned_concept_id": "customer",
            "alignment_score": 1,
            "method": "declared_term_overlap",
            "shared_normalized_terms": ["client", "customer"],
            "action": "propose_alias_alignment",
        }
    ]
    assert result.output["mutation_applied"] is False


def test_ka_1043_lineage_tracker_returns_stable_topological_order():
    result = execute(
        "KA-1043",
        {
            "knowledge_id": "knowledge-1",
            "events": [
                {
                    "event_id": "event-3",
                    "version_id": "v3",
                    "parent_version_ids": ["v1"],
                    "event_type": "corrected",
                    "source_ref": "commit:3",
                },
                {
                    "event_id": "event-1",
                    "version_id": "v1",
                    "event_type": "created",
                    "source_ref": "commit:1",
                },
                {
                    "event_id": "event-2",
                    "version_id": "v2",
                    "parent_version_ids": ["v1"],
                    "event_type": "validated",
                    "source_ref": "simulation:2",
                },
            ],
        },
    )

    assert result.success is True
    assert result.output["lineage_complete"] is True
    assert result.output["topological_version_order"] == ["v1", "v2", "v3"]
    assert result.output["root_version_ids"] == ["v1"]
    assert result.output["leaf_version_ids"] == ["v2", "v3"]
    assert result.output["lineage_persisted"] is False


def test_ka_1044_composer_generates_traceable_unverified_hypothesis():
    payload = {
        "composition_goal": "reduce recovery time",
        "sources": [
            {
                "source_id": "automation",
                "statement": "Automated checks identify failed services.",
                "concepts": ["recovery", "automation"],
                "evidence_refs": ["evidence-2"],
                "confidence": 0.8,
            },
            {
                "source_id": "runbook",
                "statement": "Validated runbooks reduce operator delay.",
                "concepts": ["recovery", "operations"],
                "evidence_refs": ["evidence-1"],
                "confidence": 0.9,
            },
        ],
    }

    first = execute("KA-1044", payload)
    second = execute("KA-1044", payload)

    assert first.success is True
    assert first.output == second.output
    hypothesis = first.output["candidate_hypotheses"][0]
    assert hypothesis["source_ids"] == ["automation", "runbook"]
    assert hypothesis["evidence_refs"] == ["evidence-1", "evidence-2"]
    assert hypothesis["validation_status"] == "unverified_candidate"
    assert first.output["knowledge_persisted"] is False


def test_ka_1046_memory_patcher_plans_tier_without_applying_effect():
    result = execute(
        "KA-1046",
        {
            "updates": [
                {
                    "update_id": "update-1",
                    "knowledge_id": "knowledge-1",
                    "current_version": "v1",
                    "proposed_version": "v2",
                    "lifecycle_state": "validated",
                    "confidence": 0.95,
                    "evidence_count": 3,
                    "sensitivity": "internal",
                },
                {
                    "update_id": "update-2",
                    "knowledge_id": "knowledge-2",
                    "current_version": "v4",
                    "proposed_version": "v5",
                    "lifecycle_state": "disputed",
                    "confidence": 0.9,
                    "evidence_count": 4,
                    "sensitivity": "restricted",
                },
            ]
        },
    )

    assert result.success is True
    assert [
        operation["recommended_tier"]
        for operation in result.output["patch_operations"]
    ] == ["long_term", "quarantine"]
    assert result.output["approval_required_count"] == 1
    assert result.output["patch_applied"] is False
    assert result.output["effect_service_required"] is True


def test_ka_1048_conflict_resolver_prefers_declared_authority_without_mutation():
    result = execute(
        "KA-1048",
        {
            "assertions": [
                {
                    "assertion_id": "approved",
                    "concept_id": "control",
                    "definition": "A verified risk-reduction measure.",
                    "source_ontology": "approved",
                    "authority_priority": 10,
                    "confidence": 0.9,
                    "evidence_refs": ["policy-1"],
                },
                {
                    "assertion_id": "legacy",
                    "concept_id": "control",
                    "definition": "Any documented process.",
                    "source_ontology": "legacy",
                    "authority_priority": 5,
                    "confidence": 0.95,
                    "evidence_refs": ["legacy-1", "legacy-2"],
                },
            ]
        },
    )

    assert result.success is True
    assert result.output["resolution_proposals"][0]["preferred_assertion_id"] == (
        "approved"
    )
    assert result.output["unresolved_conflicts"] == []
    assert result.output["mutation_applied"] is False
