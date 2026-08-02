#!/usr/bin/env python3
"""Verify CP19-K matrix integrity without overstating checkpoint completion."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_ka_qualification_matrix import (
    DEFAULT_CSV_PATH,
    DEFAULT_JSON_PATH,
    DEFAULT_MARKDOWN_PATH,
    OUTPUT_DIR,
    build_matrix,
    csv_text,
    json_text,
    markdown_text,
)

DEFAULT_EVIDENCE_PATH = OUTPUT_DIR / "cp19-k-qualification-verification.json"


def _check_generated(path: Path, expected: str, errors: list[str]) -> None:
    relative = path.relative_to(ROOT).as_posix()
    if not path.is_file():
        errors.append(f"{relative}: generated output missing")
    elif path.read_text(encoding="utf-8") != expected:
        errors.append(f"{relative}: generated output stale")


def verify(*, require_complete: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    matrix = build_matrix()
    _check_generated(DEFAULT_JSON_PATH, json_text(matrix), errors)
    _check_generated(DEFAULT_CSV_PATH, csv_text(matrix), errors)
    _check_generated(DEFAULT_MARKDOWN_PATH, markdown_text(matrix), errors)

    rows = matrix["canonical_capabilities"]
    ids = [row["canonical_id"] for row in rows]
    status_counts = Counter(row["qualification_status"] for row in rows)
    qualified_ids = sorted(
        row["canonical_id"]
        for row in rows
        if row["qualification_status"] == "qualified"
    )
    reviewed_ids = sorted(
        canonical_id
        for batch in matrix["batches"]
        for canonical_id in batch["canonical_ids"]
    )

    if len(rows) != 213 or len(set(ids)) != 213:
        errors.append(
            f"canonical row identity mismatch: rows={len(rows)} unique={len(set(ids))}"
        )
    if qualified_ids != reviewed_ids:
        errors.append("reviewed batch membership does not equal qualified rows")
    if matrix["invariants"]["qualified_capabilities"] != len(qualified_ids):
        errors.append("qualified row summary mismatch")
    if matrix["invariants"]["incomplete_capabilities"] != status_counts["incomplete"]:
        errors.append("incomplete row summary mismatch")
    if matrix["invariants"]["rebuild_authorized"] is not False:
        errors.append("CP19-K matrix must not authorize rebuilding")
    if matrix["invariants"]["findings_waived"] is not False:
        errors.append("CP19-K matrix must not waive findings")

    for row in rows:
        canonical_id = row["canonical_id"]
        missing = sorted(row["missing_evidence"])
        calculated = sorted(
            key
            for key, evidence in row["evidence"].items()
            if evidence.get("status") != "qualified"
        )
        if missing != calculated:
            errors.append(f"{canonical_id}: missing-evidence summary drift")
        expected_status = "qualified" if not missing else "incomplete"
        if row["qualification_status"] != expected_status:
            errors.append(f"{canonical_id}: qualification status is not truthful")
        if not row["limitation"]:
            errors.append(f"{canonical_id}: limitation text is empty")
        if row["performance_budget_ms"] <= 0:
            errors.append(f"{canonical_id}: performance budget is invalid")

    complete = len(qualified_ids) == len(rows)
    expected_matrix_status = (
        "cp19_k_complete" if complete else "cp19_k_in_progress"
    )
    if matrix["status"] != expected_matrix_status:
        errors.append("matrix checkpoint status does not match qualified rows")
    if require_complete and not complete:
        errors.append(
            f"CP19-K is incomplete: {len(rows) - len(qualified_ids)} rows remain open"
        )

    return {
        "schema_version": "dle.cp19-k-qualification-verification.v1",
        "integrity_status": "pass" if not errors else "fail",
        "checkpoint_status": "complete" if complete else "in_progress",
        "matrix_version": matrix["matrix_version"],
        "canonical_capabilities": len(rows),
        "qualified_capabilities": len(qualified_ids),
        "incomplete_capabilities": len(rows) - len(qualified_ids),
        "qualified_ids": qualified_ids,
        "evidence_counts": matrix["evidence_counts"],
        "require_complete": require_complete,
        "rebuild_authorized": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    evidence = verify(require_complete=args.require_complete)
    if not args.no_write:
        DEFAULT_EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_EVIDENCE_PATH.write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(
        "Phase 19 CP19-K qualification matrix: "
        + (
            f"{evidence['integrity_status'].upper()}; "
            f"{evidence['qualified_capabilities']}/"
            f"{evidence['canonical_capabilities']} qualified; "
            f"checkpoint {evidence['checkpoint_status']}"
        )
    )
    return 0 if evidence["integrity_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
