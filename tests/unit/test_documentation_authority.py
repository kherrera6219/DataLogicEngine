from __future__ import annotations

from scripts.generate_documentation_authority import (
    ROOT,
    build_inventory,
    load_authority,
    markdown_paths,
)


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
    assert inventory["status"] == "draft_pass"


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
