#!/usr/bin/env python3
"""Build the truthful, generated CP19-K per-KA qualification matrix."""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.knowledge_algorithms.manifest import load_manifest
from scripts.build_ka_integration_authority import build_authority

OUTPUT_DIR = ROOT / "reports" / "production-readiness" / "2026" / "phase-19"
DEFAULT_JSON_PATH = OUTPUT_DIR / "ka-qualification-matrix.json"
DEFAULT_CSV_PATH = OUTPUT_DIR / "ka-qualification-matrix.csv"
DEFAULT_MARKDOWN_PATH = OUTPUT_DIR / "cp19-k-qualification-matrix.md"
EVIDENCE_SOURCE_PATH = ROOT / "config" / "phase19-ka-qualification-evidence.json"

PLACEHOLDER_LIMITATIONS = {
    "Phase 19 capability limitation review required.",
}
REQUIRED_TRACE_STATES = [
    "planned",
    "candidate",
    "selected",
    "admitted",
    "executing",
    "executed",
]


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _load_evidence_source() -> dict[str, Any]:
    payload = json.loads(EVIDENCE_SOURCE_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "dle.cp19-k-qualification-evidence.v1":
        raise ValueError("CP19-K evidence source schema is not supported")
    return payload


def _test_functions(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def reference_exists(reference: str | None) -> bool:
    if not reference:
        return False
    path_text, separator, node_id = reference.partition("::")
    path = ROOT / path_text
    if not path.is_file():
        return False
    if not separator:
        return True
    return bool(node_id) and node_id in _test_functions(path)


def _fixture_evidence(
    reference: str,
    *,
    canonical_id: str,
    expected_fragment: str,
) -> dict[str, Any]:
    path_text, separator, fragment = reference.partition("#")
    valid = separator == "#" and fragment == expected_fragment
    path = ROOT / path_text
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        payload = {}
        valid = False
    fixture = payload.get(expected_fragment) if isinstance(payload, dict) else None
    request = fixture.get("request") if isinstance(fixture, dict) else None
    expected = fixture.get("expected") if isinstance(fixture, dict) else None
    targets_capability = bool(
        isinstance(request, dict)
        and (
            canonical_id in request.get("requested_ids", [])
            or (
                expected_fragment == "negative_selector" and bool(request.get("stages"))
            )
        )
    )
    valid = bool(
        valid
        and payload.get("schema_version") == "dle.ka-selector-fixture.v1"
        and payload.get("canonical_id") == canonical_id
        and isinstance(request, dict)
        and targets_capability
        and isinstance(expected, dict)
        and isinstance(expected.get("selected"), bool)
        and expected.get("reason")
    )
    return {
        "status": "qualified" if valid else "missing",
        "reference": reference,
        "schema_version": payload.get("schema_version"),
    }


def _test_evidence(
    supplied: str | None,
    *,
    expected: str | None = None,
) -> dict[str, Any]:
    matches_target = expected is None or supplied == expected
    exists = matches_target and reference_exists(supplied)
    return {
        "status": "qualified" if exists else "missing",
        "reference": supplied or expected,
        "matches_authority_target": matches_target,
    }


def _review_evidence(
    value: dict[str, Any] | None,
    *,
    expected_applicability: str | None = None,
) -> dict[str, Any]:
    value = value if isinstance(value, dict) else {}
    applicability = str(value.get("applicability") or "review_required")
    rationale = str(value.get("rationale") or "").strip()
    reference = value.get("reference")
    valid_applicability = applicability in {"required", "not_applicable"}
    if expected_applicability is not None:
        valid_applicability = applicability == expected_applicability
    reference_valid = (
        reference_exists(str(reference))
        if applicability == "required"
        else reference is None
    )
    qualified = bool(valid_applicability and rationale and reference_valid)
    return {
        "status": "qualified" if qualified else "missing",
        "applicability": applicability,
        "reference": reference,
        "rationale": rationale or None,
    }


def _missing_evidence(evidence: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key, value in evidence.items():
        if isinstance(value, dict) and value.get("status") != "qualified":
            missing.append(key)
    return missing


def _validate_source(
    source: dict[str, Any],
    *,
    authority: dict[str, Any],
    manifest_version: str,
) -> None:
    if source.get("authority_version") != authority["authority_version"]:
        raise ValueError("CP19-K evidence source authority version drift")
    if source.get("manifest_version") != manifest_version:
        raise ValueError("CP19-K evidence source manifest version drift")

    authority_ids = {row["canonical_id"] for row in authority["canonical_capabilities"]}
    qualifications = source.get("qualifications")
    if not isinstance(qualifications, dict):
        raise TypeError("CP19-K evidence source qualifications must be an object")
    unknown = sorted(set(qualifications) - authority_ids)
    if unknown:
        raise ValueError(f"CP19-K evidence source has unknown IDs: {unknown}")

    batches = source.get("batches")
    if not isinstance(batches, list):
        raise TypeError("CP19-K evidence source batches must be a list")
    batch_ids = [str(batch.get("batch_id") or "") for batch in batches]
    if any(not batch_id for batch_id in batch_ids) or len(batch_ids) != len(
        set(batch_ids)
    ):
        raise ValueError("CP19-K evidence source batch IDs must be unique")
    declared_members = {
        canonical_id
        for batch in batches
        for canonical_id in batch.get("canonical_ids", [])
    }
    if declared_members != set(qualifications):
        raise ValueError("CP19-K batch membership does not match qualifications")
    for canonical_id, review in qualifications.items():
        if review.get("batch_id") not in batch_ids:
            raise ValueError(f"{canonical_id}: qualification batch is unknown")


def build_matrix() -> dict[str, Any]:
    authority = build_authority()
    manifest = load_manifest()
    source = _load_evidence_source()
    _validate_source(
        source,
        authority=authority,
        manifest_version=manifest.manifest_version,
    )

    authority_rows = {
        row["canonical_id"]: row for row in authority["canonical_capabilities"]
    }
    if set(authority_rows) != set(manifest.entries):
        raise ValueError("CP19-K authority and runtime manifest identities differ")

    reviews = source["qualifications"]
    rows: list[dict[str, Any]] = []
    for canonical_id in sorted(manifest.entries):
        definition = manifest.entries[canonical_id]
        authority_row = authority_rows[canonical_id]
        review = reviews.get(canonical_id, {})
        limitation = definition.contract.limitations.strip()
        limitation_qualified = bool(
            review.get("limitation_review") == "accepted_manifest_limitation"
            and limitation
            and limitation not in PLACEHOLDER_LIMITATIONS
        )
        semantic = _test_evidence(
            review.get("semantic_test"),
            expected=authority_row["functional_test"],
        )
        owning_path = _test_evidence(
            review.get("owning_path_test"),
            expected=authority_row["integration_test"],
        )
        trace = _test_evidence(
            review.get("trace_test"),
            expected=authority_row["integration_test"],
        )
        performance = _test_evidence(
            review.get("performance_test"),
            expected=authority_row["functional_test"],
        )
        effect_applicability = (
            "required"
            if definition.contract.effect_class == "effect_oriented_review_required"
            else "not_applicable"
        )
        evidence = {
            "semantic_test": semantic,
            "positive_selector": _fixture_evidence(
                authority_row["positive_fixture"],
                canonical_id=canonical_id,
                expected_fragment="positive_selector",
            ),
            "negative_selector": _fixture_evidence(
                authority_row["negative_fixture"],
                canonical_id=canonical_id,
                expected_fragment="negative_selector",
            ),
            "owning_path_test": owning_path,
            "limitation_review": {
                "status": "qualified" if limitation_qualified else "missing",
                "disposition": review.get("limitation_review"),
            },
            "trace_proof": {
                **trace,
                "required_states": REQUIRED_TRACE_STATES,
            },
            "security_review": _review_evidence(review.get("security_evidence")),
            "effect_review": _review_evidence(
                review.get("effect_evidence"),
                expected_applicability=effect_applicability,
            ),
            "performance_evidence": {
                **performance,
                "budget_ms": definition.contract.performance_budget_ms,
            },
        }
        missing = _missing_evidence(evidence)
        rows.append(
            {
                "canonical_id": canonical_id,
                "name": definition.name,
                "primary_owner": definition.integration.primary_owner,
                "stage": definition.integration.stage,
                "production_enabled": definition.admission.production_enabled,
                "effect_class": definition.contract.effect_class,
                "effect_port": definition.integration.effect_port,
                "limitation": limitation,
                "performance_budget_ms": (definition.contract.performance_budget_ms),
                "batch_id": review.get("batch_id"),
                "evidence": evidence,
                "missing_evidence": missing,
                "qualification_status": ("qualified" if not missing else "incomplete"),
            }
        )

    status_counts = Counter(row["qualification_status"] for row in rows)
    evidence_counts = {
        key: sum(row["evidence"][key]["status"] == "qualified" for row in rows)
        for key in rows[0]["evidence"]
    }
    qualified = status_counts["qualified"]
    return {
        "schema_version": "dle.cp19-k-qualification-matrix.v1",
        "matrix_version": "2026.08.05-cp19k.11",
        "status": (
            "cp19_k_complete" if qualified == len(rows) else "cp19_k_in_progress"
        ),
        "phase": 19,
        "checkpoint": "CP19-K",
        "authority_version": authority["authority_version"],
        "manifest_version": manifest.manifest_version,
        "evidence_source": _relative(EVIDENCE_SOURCE_PATH),
        "invariants": {
            "canonical_capabilities": len(rows),
            "qualified_capabilities": qualified,
            "incomplete_capabilities": status_counts["incomplete"],
            "reviewed_capabilities": len(reviews),
            "runtime_registries_added": 0,
            "findings_waived": False,
            "rebuild_authorized": False,
        },
        "evidence_counts": evidence_counts,
        "batches": source["batches"],
        "canonical_capabilities": rows,
    }


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def csv_text(payload: dict[str, Any]) -> str:
    buffer = io.StringIO(newline="")
    fieldnames = [
        "canonical_id",
        "name",
        "primary_owner",
        "stage",
        "production_enabled",
        "effect_class",
        "limitation",
        "performance_budget_ms",
        "batch_id",
        "qualification_status",
        "missing_evidence",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in payload["canonical_capabilities"]:
        writer.writerow(
            {
                **{key: row.get(key) for key in fieldnames},
                "missing_evidence": ";".join(row["missing_evidence"]),
            }
        )
    return buffer.getvalue()


def markdown_text(payload: dict[str, Any]) -> str:
    invariants = payload["invariants"]
    batch_rows = "\n".join(
        "| `{batch_id}` | {completed_on} | {count} | {scope} |".format(
            batch_id=batch["batch_id"],
            completed_on=batch["completed_on"],
            count=len(batch["canonical_ids"]),
            scope=batch["scope"],
        )
        for batch in payload["batches"]
    )
    return f"""# CP19-K per-KA qualification matrix

**Matrix version:** `{payload["matrix_version"]}`
**Status:** `{payload["status"]}`
**Release decision:** NO-GO; rebuild not authorized

## Current result

The generated matrix contains all {invariants["canonical_capabilities"]}
canonical capabilities. {invariants["qualified_capabilities"]} rows are fully
qualified and {invariants["incomplete_capabilities"]} remain open. A row closes
only when its individually reviewed evidence has an exact named semantic test,
both selector fixtures, a real owning-path test, an accepted limitation, causal
trace proof, and applicable security, effect, and performance evidence.

The complete row detail is in `ka-qualification-matrix.json` and
`ka-qualification-matrix.csv`.

## Completed batches

| Batch | Date | Qualified KAs | Scope |
|---|---|---:|---|
{batch_rows}

## Gate decision

CP19-K remains active. This partial matrix does not authorize CP19-L, rebuilding,
installed acceptance, signing, or production/public release.
"""


def write_or_check(*, check: bool) -> int:
    payload = build_matrix()
    outputs = {
        DEFAULT_JSON_PATH: json_text(payload),
        DEFAULT_CSV_PATH: csv_text(payload),
        DEFAULT_MARKDOWN_PATH: markdown_text(payload),
    }
    stale: list[Path] = []
    for path, content in outputs.items():
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != content:
            stale.append(path)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
    if check and stale:
        for path in stale:
            print(f"stale: {_relative(path)}")
        return 1
    if not check:
        for path in outputs:
            print(f"generated: {_relative(path)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_or_check(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
