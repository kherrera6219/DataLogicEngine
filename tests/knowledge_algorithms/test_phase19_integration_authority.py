from __future__ import annotations

from backend.knowledge_algorithms.ka_master_controller import KAMasterController
from backend.knowledge_algorithms.manifest import load_manifest
from scripts.build_ka_integration_authority import (
    DEFAULT_CSV_PATH,
    DEFAULT_JSON_PATH,
    DEFAULT_MARKDOWN_PATH,
    build_authority,
    csv_text,
    json_text,
    markdown_text,
)


def test_cp19a_authority_is_current_complete_and_not_a_runtime_registry():
    authority = build_authority()

    assert authority["status"] == "approved_cp19_a_authority"
    assert authority["runtime_registry"] is False
    assert authority["invariants"] == {
        "canonical_capabilities": 213,
        "unique_implementation_owners": 213,
        "unowned_capabilities": 0,
        "duplicate_primary_owners": 0,
        "runtime_registries_added": 0,
        "findings_waived": False,
        "rebuild_authorized": False,
    }
    assert sum(authority["owner_counts"].values()) == 213
    assert DEFAULT_JSON_PATH.read_text(encoding="utf-8") == json_text(authority)
    assert DEFAULT_CSV_PATH.read_text(encoding="utf-8") == csv_text(authority)
    assert DEFAULT_MARKDOWN_PATH.read_text(encoding="utf-8") == markdown_text(authority)


def test_cp19a_every_ka_has_one_owner_consumers_and_evidence_destinations():
    rows = build_authority()["canonical_capabilities"]

    assert len(rows) == 213
    assert len({row["canonical_id"] for row in rows}) == 213
    assert len({row["implementation_owner"] for row in rows}) == 213
    for row in rows:
        assert row["primary_owner"]
        assert row["consumer_paths"]
        assert len(row["consumer_paths"]) == len(set(row["consumer_paths"]))
        assert row["selector_policy"]
        assert row["required_or_optional"]
        assert row["stage"]
        assert row["positive_fixture"].endswith("#positive_selector")
        assert row["negative_fixture"].endswith("#negative_selector")
        assert "::test_" in row["functional_test"]
        assert "::test_" in row["integration_test"]
        assert row["trace_assertion"]
        assert row["qualification"]["contract"] == "CP19-B"
        assert row["qualification"]["selector"] == "CP19-C"
        assert row["qualification"]["source_exit"] == "CP19-L"
        assert row["qualification"]["installed_exit"] == "CP19-M"
        effectful = row["effect_class"] == "effect_oriented_review_required"
        assert bool(row["effect_port"]) is effectful


def test_cp19a_workflow_dispositions_are_unique_and_complete():
    dispositions = build_authority()["workflow_dispositions"]

    paths = [row["path"] for row in dispositions]
    assert len(paths) == len(set(paths))
    assert {
        "canonical_product_owner",
        "canonical_stage_library",
        "canonical_candidate",
        "broken_reference_removal_candidate",
        "legacy_nonproduction",
        "legacy_parallel_orchestrator",
        "legacy_reference_engine",
    }.issubset({row["disposition"] for row in dispositions})
    for row in dispositions:
        assert row["target_checkpoint"].startswith("CP19-")
        assert row["production_policy"]


def test_cp19a_runtime_manifest_consumes_the_integration_authority():
    authority = build_authority()
    rows = {row["canonical_id"]: row for row in authority["canonical_capabilities"]}
    manifest = load_manifest()

    assert manifest.status == "cp19_j_product_workflow_authority"
    assert (
        manifest.authority["integration_authority_version"]
        == authority["authority_version"]
    )
    assert manifest.capability_count == 213
    for canonical_id, definition in manifest.entries.items():
        expected = rows[canonical_id]
        assert definition.integration.primary_owner == expected["primary_owner"]
        assert definition.integration.consumer_paths == expected["consumer_paths"]
        assert definition.integration.effect_port == expected["effect_port"]


def test_cp19a_catalog_cards_expose_owner_and_selection_authority():
    card = KAMasterController().get_available_algorithms()["KA-071"]["metadata"]

    assert card["Primary_Owner"] == "ingestion"
    assert card["Owner"] == "ingestion"
    assert "canonical_controller" in card["Consumer_Paths"]
    assert card["Integration_Stage"] == "ingestion_pipeline"
    assert card["Selector_Policy"]
    assert card["Effect_Port"] == "ingestion_service"
