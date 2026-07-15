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
    inventory = build_inventory(authority)
    merge_rows = [
        row for row in inventory["documents"] if row["disposition"].startswith("merge into ")
    ]
    assert merge_rows
    assert all(row["target"] in canonical for row in merge_rows)


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
    assert result["archive_delete_authorized"] is False


def test_cp16b_product_user_documents_preserve_sources_and_truthful_boundaries():
    result = verify_product_user_docs(load_authority())
    assert result["status"] == "pass"
    assert result["verified_count"] == 5
    assert result["target_count"] == 5
    assert result["archive_delete_authorized"] is False


def test_cp16c_engineering_assurance_documents_preserve_sources_and_boundaries():
    result = verify_engineering_assurance_docs(load_authority())
    assert result["status"] == "pass"
    assert result["verified_count"] == 12
    assert result["target_count"] == 12
    assert result["archive_delete_authorized"] is False
