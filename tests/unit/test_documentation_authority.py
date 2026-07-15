from __future__ import annotations

from scripts.generate_documentation_authority import (
    ROOT,
    build_inventory,
    load_authority,
    markdown_paths,
)
from scripts.verify_doc_authority import verify as verify_doc_authority
from scripts.verify_engineering_assurance_docs import (
    verify as verify_engineering_assurance_docs,
)
from scripts.verify_product_user_docs import verify as verify_product_user_docs
from scripts.verify_submission_dossier import verify as verify_submission_dossier


def test_phase16_canonical_set_is_exactly_thirty_with_unique_ids_and_paths():
    authority = load_authority()
    documents = authority["canonical_documents"]
    assert len(documents) == 30
    assert len({item["id"] for item in documents}) == 30
    assert len({item["path"] for item in documents}) == 30
    assert all(item["class"] in authority["document_classes"] for item in documents)


def test_every_root_and_docs_markdown_has_one_disposition():
    inventory = build_inventory(load_authority())
    assert [row["path"] for row in inventory["documents"]] == markdown_paths(ROOT)
    assert inventory["unclassified"] == []
    assert inventory["duplicate_routes"] == []
    assert inventory["status"].endswith("_pass")


def test_every_merge_target_is_in_the_canonical_set():
    authority = load_authority()
    canonical = {item["path"] for item in authority["canonical_documents"]}
    merge_routes = authority["merge_routes"]
    assert merge_routes
    assert all(target in canonical for target in merge_routes)
    assert sum(len(sources) for sources in merge_routes.values()) == 72


def test_no_canonical_document_is_routed_as_historical_or_merge_input():
    authority = load_authority()
    canonical = {item["path"] for item in authority["canonical_documents"]}
    inventory = build_inventory(authority)
    rows = {row["path"]: row for row in inventory["documents"]}
    for path in canonical & set(rows):
        assert rows[path]["disposition"] == "authoritative input"
        assert rows[path]["cap_counted"] is True


def test_existing_canonical_documents_have_controlled_headers():
    result = verify_doc_authority(load_authority())
    assert result["status"] == "pass"
    assert result["existing_canonical_count"] >= 15
    assert result["controlled_header_pass_count"] == result["existing_canonical_count"]
    assert result["planned_canonical_count"] <= 15
    assert result["existing_canonical_count"] + result["planned_canonical_count"] == 30
    assert result["archive_delete_authorized"] is True


def test_cp16b_product_user_documents_preserve_sources_and_truthful_boundaries():
    result = verify_product_user_docs(load_authority())
    assert result["status"] == "pass"
    assert result["verified_count"] == 5
    assert result["target_count"] == 5
    assert result["archive_delete_authorized"] is True


def test_cp16c_engineering_assurance_documents_preserve_sources_and_boundaries():
    result = verify_engineering_assurance_docs(load_authority())
    assert result["status"] == "pass"
    assert result["verified_count"] == 12
    assert result["target_count"] == 12
    assert result["archive_delete_authorized"] is True


def test_cp16d_e_external_review_records_remain_fail_closed():
    result = verify_submission_dossier(load_authority())
    assert result["status"] == "pass"
    assert result["verified_count"] == 3
    assert result["target_count"] == 3
    assert result["archive_delete_authorized"] is True


def test_cp16f_document_replacement_sources_links_and_retained_evidence_close():
    import json

    from scripts.verify_document_replacement_closure import (
        DEFAULT_BASELINE,
        verify as verify_replacement,
    )

    baseline = json.loads(DEFAULT_BASELINE.read_text(encoding="utf-8"))
    result = verify_replacement(load_authority(), baseline)
    assert result["status"] == "pass"
    assert result["summary"]["source_count"] == 72
    assert result["summary"]["active_source_count"] == 0
    assert result["summary"]["archived_source_count"] == 72
    assert result["summary"]["verified_target_count"] == 18
    assert result["summary"]["unmigrated_link_count"] == 0
    assert result["summary"]["retained_evidence_pass_count"] == 72
