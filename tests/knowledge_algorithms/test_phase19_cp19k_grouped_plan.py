"""Integrity checks for the grouped CP19-K completion roadmap."""

from __future__ import annotations

import json
from pathlib import Path

from backend.knowledge_algorithms.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "config" / "phase19-ka-grouped-batches.json"
MATRIX_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-19"
    / "ka-qualification-matrix.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_grouped_plan_covers_every_open_ka_exactly_once():
    plan = _load(PLAN_PATH)
    matrix = _load(MATRIX_PATH)
    planned_ids = [
        canonical_id
        for batch in plan["batches"]
        for canonical_id in batch["canonical_ids"]
    ]
    open_ids = {
        row["canonical_id"]
        for row in matrix["canonical_capabilities"]
        if row["qualification_status"] == "incomplete"
    }
    completed_ids = {
        canonical_id
        for batch in plan["batches"]
        if batch["batch_number"] in plan["completed_batch_numbers"]
        for canonical_id in batch["canonical_ids"]
    }
    remaining_planned_ids = set(planned_ids) - completed_ids

    assert plan["baseline_matrix_version"] == matrix["matrix_version"]
    assert plan["baseline_qualified_capabilities"] == 27
    assert plan["planned_capabilities"] == 186
    assert plan["planned_batch_count"] == 36
    assert plan["batch_number_range"] == [8, 43]
    assert plan["completed_batch_numbers"] == [8, 9, 10, 11, 12]
    assert plan["next_batch_number"] == 13
    assert plan["current_qualified_capabilities"] == 58
    assert plan["current_open_capabilities"] == 155
    assert len(plan["batches"]) == 36
    assert len(planned_ids) == len(set(planned_ids)) == 186
    assert remaining_planned_ids == open_ids


def test_grouped_batches_have_one_owner_bounded_size_and_dependency_order():
    plan = _load(PLAN_PATH)
    matrix = _load(MATRIX_PATH)
    manifest = load_manifest()
    rows = {
        row["canonical_id"]: row
        for row in matrix["canonical_capabilities"]
    }
    batch_by_id = {
        canonical_id: batch["batch_number"]
        for batch in plan["batches"]
        for canonical_id in batch["canonical_ids"]
    }

    assert [batch["batch_number"] for batch in plan["batches"]] == list(
        range(8, 44)
    )
    assert len({batch["batch_id"] for batch in plan["batches"]}) == 36
    for batch in plan["batches"]:
        canonical_ids = batch["canonical_ids"]
        assert 2 <= len(canonical_ids) <= 8
        assert batch["cohesion"].strip()
        assert batch["effect_boundary"].strip()
        assert {
            rows[canonical_id]["primary_owner"]
            for canonical_id in canonical_ids
        } == {batch["owner"]}
        for canonical_id in canonical_ids:
            for dependency_id in manifest.entries[
                canonical_id
            ].contract.dependencies:
                dependency_batch = batch_by_id.get(dependency_id)
                if dependency_batch is not None:
                    assert dependency_batch <= batch["batch_number"], (
                        f"{canonical_id} in batch {batch['batch_number']} "
                        f"depends on later batch {dependency_batch}: "
                        f"{dependency_id}"
                    )
