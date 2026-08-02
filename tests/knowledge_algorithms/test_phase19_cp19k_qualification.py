"""Integrity checks for the generated, partial CP19-K qualification matrix."""

from __future__ import annotations

from scripts.build_ka_qualification_matrix import (
    DEFAULT_CSV_PATH,
    DEFAULT_JSON_PATH,
    DEFAULT_MARKDOWN_PATH,
    build_matrix,
    csv_text,
    json_text,
    markdown_text,
)
from scripts.verify_phase19_cp19k_qualification import verify

QUALIFIED_BATCHES = {
    "KA-001",
    "KA-004",
    "KA-005",
    "KA-010",
    "KA-022",
    "KA-024",
    "KA-032",
    "KA-037",
    "KA-042",
    "KA-061",
    "KA-070",
    "KA-071",
    "KA-072",
    "KA-073",
    "KA-074",
    "KA-075",
    "KA-076",
    "KA-077",
    "KA-078",
    "KA-084",
    "KA-091",
    "KA-092",
    "KA-094",
    "KA-095",
    "KA-098",
    "KA-099",
    "KA-100",
    "KA-113",
    "KA-136",
    "KA-137",
    "KA-175",
    "KA-177",
    "KA-179",
    "KA-182",
    "KA-096",
    "KA-097",
    "KA-106",
    "KA-184",
    "KA-1072",
    "KA-1080",
    "KA-1081",
    "KA-1091",
}


def test_cp19k_generated_matrix_is_current_complete_and_truthful():
    matrix = build_matrix()

    assert matrix["status"] == "cp19_k_in_progress"
    assert matrix["invariants"] == {
        "canonical_capabilities": 213,
        "qualified_capabilities": 42,
        "incomplete_capabilities": 171,
        "reviewed_capabilities": 42,
        "runtime_registries_added": 0,
        "findings_waived": False,
        "rebuild_authorized": False,
    }
    assert matrix["evidence_counts"]["positive_selector"] == 213
    assert matrix["evidence_counts"]["negative_selector"] == 213
    assert DEFAULT_JSON_PATH.read_text(encoding="utf-8") == json_text(matrix)
    assert DEFAULT_CSV_PATH.read_text(encoding="utf-8") == csv_text(matrix)
    assert DEFAULT_MARKDOWN_PATH.read_text(encoding="utf-8") == markdown_text(
        matrix
    )


def test_cp19k_completed_batches_have_every_required_evidence_class():
    rows = {
        row["canonical_id"]: row
        for row in build_matrix()["canonical_capabilities"]
    }

    assert {
        canonical_id
        for canonical_id, row in rows.items()
        if row["qualification_status"] == "qualified"
    } == QUALIFIED_BATCHES
    for canonical_id in QUALIFIED_BATCHES:
        row = rows[canonical_id]
        assert row["missing_evidence"] == []
        assert all(
            evidence["status"] == "qualified"
            for evidence in row["evidence"].values()
        )
        assert row["evidence"]["trace_proof"]["required_states"] == [
            "planned",
            "candidate",
            "selected",
            "admitted",
            "executing",
            "executed",
        ]
        assert row["limitation"]
        assert row["performance_budget_ms"] > 0


def test_cp19k_does_not_overstate_unreviewed_ka_031():
    row = next(
        row
        for row in build_matrix()["canonical_capabilities"]
        if row["canonical_id"] == "KA-031"
    )

    assert row["production_enabled"] is True
    assert row["qualification_status"] == "incomplete"
    assert {
        "semantic_test",
        "owning_path_test",
        "limitation_review",
        "trace_proof",
        "security_review",
        "effect_review",
        "performance_evidence",
    }.issubset(row["missing_evidence"])


def test_cp19k_integrity_verifier_passes_without_closing_checkpoint():
    evidence = verify()

    assert evidence["integrity_status"] == "pass"
    assert evidence["checkpoint_status"] == "in_progress"
    assert evidence["qualified_capabilities"] == 42
    assert evidence["incomplete_capabilities"] == 171
    assert evidence["rebuild_authorized"] is False
    assert evidence["errors"] == []
