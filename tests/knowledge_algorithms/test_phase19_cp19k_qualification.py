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
    "KA-081",
    "KA-082",
    "KA-083",
    "KA-084",
    "KA-085",
    "KA-086",
    "KA-087",
    "KA-088",
    "KA-089",
    "KA-090",
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
    "KA-023",
    "KA-052",
    "KA-064",
    "KA-1082",
    "KA-1083",
    "KA-1093",
    "KA-1105",
    "KA-003",
    "KA-011",
    "KA-015",
    "KA-017",
    "KA-025",
    "KA-040",
    "KA-018",
    "KA-079",
    "KA-1049",
    "KA-1077",
    "KA-1092",
    "KA-031",
    "KA-036",
    "KA-1073",
    "KA-1107",
    "KA-Master",
    "KA-034",
    "KA-1074",
    "KA-172",
    "KA-173",
    "KA-062",
    "KA-065",
    "KA-1071",
    "KA-1094",
    "KA-1109",
    "KA-117",
    "KA-029",
    "KA-1079",
    "KA-012",
    "KA-013",
    "KA-028",
    "KA-030",
    "KA-038",
    "KA-002",
    "KA-009",
    "KA-014",
    "KA-026",
    "KA-035",
    "KA-1041",
    "KA-1042",
    "KA-1102",
    "KA-033",
    "KA-058",
    "KA-059",
    "KA-080",
    "KA-1039",
    "KA-1040",
    "KA-1043",
    "KA-1046",
    "KA-1048",
    "KA-1076",
    "KA-1078",
    "KA-051",
    "KA-053",
    "KA-054",
    "KA-055",
    "KA-063",
    "KA-020",
    "KA-021",
    "KA-1045",
    "KA-1086",
    "KA-1088",
    "KA-1089",
    "KA-1095",
    "KA-1099",
    "KA-1104",
    "KA-1106",
    "KA-1108",
    "KA-1110",
    "KA-1112",
    "KA-116",
    "KA-016",
    "KA-027",
    "KA-1090",
    "KA-1096",
    "KA-1111",
    "KA-169",
    "KA-174",
    "KA-176",
    "KA-057",
    "KA-068",
    "KA-069",
    "KA-1037",
    "KA-1075",
    "KA-1084",
    "KA-006",
    "KA-007",
    "KA-060",
    "KA-066",
    "KA-067",
    "KA-1036",
    "KA-1044",
    "KA-1047",
    "KA-1085",
    "KA-008",
    "KA-019",
    "KA-056",
    "KA-1038",
    "KA-1087",
    *(f"L9-KA-{number:03d}" for number in range(1, 8)),
    *(f"L10-KA-{number:03d}" for number in range(1, 8)),
}


def test_cp19k_generated_matrix_is_current_complete_and_truthful():
    matrix = build_matrix()

    assert matrix["status"] == "cp19_k_in_progress"
    assert matrix["invariants"] == {
        "canonical_capabilities": 213,
        "qualified_capabilities": 171,
        "incomplete_capabilities": 42,
        "reviewed_capabilities": 171,
        "runtime_registries_added": 0,
        "findings_waived": False,
        "rebuild_authorized": False,
    }
    assert matrix["evidence_counts"]["positive_selector"] == 213
    assert matrix["evidence_counts"]["negative_selector"] == 213
    assert DEFAULT_JSON_PATH.read_text(encoding="utf-8") == json_text(matrix)
    assert DEFAULT_CSV_PATH.read_text(encoding="utf-8") == csv_text(matrix)
    assert DEFAULT_MARKDOWN_PATH.read_text(encoding="utf-8") == markdown_text(matrix)


def test_cp19k_completed_batches_have_every_required_evidence_class():
    rows = {
        row["canonical_id"]: row for row in build_matrix()["canonical_capabilities"]
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
            evidence["status"] == "qualified" for evidence in row["evidence"].values()
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


def test_cp19k_does_not_overstate_next_unreviewed_ka_041():
    row = next(
        row
        for row in build_matrix()["canonical_capabilities"]
        if row["canonical_id"] == "KA-041"
    )

    assert row["production_enabled"] is False
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
    assert evidence["qualified_capabilities"] == 171
    assert evidence["incomplete_capabilities"] == 42
    assert evidence["rebuild_authorized"] is False
    assert evidence["errors"] == []
