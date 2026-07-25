#!/usr/bin/env python3
"""Verify the CP19-A KA ownership and workflow-disposition authority."""

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

from backend.knowledge_algorithms.manifest import load_manifest
from scripts.build_ka_integration_authority import (
    DEFAULT_CSV_PATH,
    DEFAULT_JSON_PATH,
    DEFAULT_MARKDOWN_PATH,
    FINDING_TRANSFERS,
    OWNER_DEFINITIONS,
    build_authority,
    csv_text,
    json_text,
    markdown_text,
)
from scripts.build_ka_runtime_manifest import (
    DEFAULT_OUTPUT_PATH as RUNTIME_MANIFEST_PATH,
)

DEFAULT_EVIDENCE_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-19"
    / "cp19-a-integration-authority-verification.json"
)


def _check_generated(
    path: Path, expected: str, errors: list[str]
) -> None:
    relative = path.relative_to(ROOT).as_posix()
    if not path.is_file():
        errors.append(f"{relative}: generated output missing")
    elif path.read_text(encoding="utf-8") != expected:
        errors.append(f"{relative}: generated output stale")


def verify() -> dict[str, Any]:
    errors: list[str] = []
    authority = build_authority()
    _check_generated(DEFAULT_JSON_PATH, json_text(authority), errors)
    _check_generated(DEFAULT_CSV_PATH, csv_text(authority), errors)
    _check_generated(DEFAULT_MARKDOWN_PATH, markdown_text(authority), errors)

    rows = authority["canonical_capabilities"]
    ids = [row["canonical_id"] for row in rows]
    implementation_owners = [
        row["implementation_owner"] for row in rows
    ]
    owner_counts = Counter({owner: 0 for owner in OWNER_DEFINITIONS})
    owner_counts.update(row["primary_owner"] for row in rows)

    if authority["status"] != "approved_cp19_a_authority":
        errors.append("integration authority is not approved_cp19_a_authority")
    if authority["runtime_registry"] is not False:
        errors.append("integration authority must not be a runtime registry")
    if len(rows) != 213 or len(ids) != len(set(ids)):
        errors.append(
            f"canonical row identity mismatch: rows={len(rows)} unique={len(set(ids))}"
        )
    if len(set(implementation_owners)) != 213:
        errors.append(
            "implementation owners are not one-to-one with canonical capabilities"
        )
    if set(owner_counts) - set(OWNER_DEFINITIONS):
        errors.append(
            "unknown primary owners: "
            + ",".join(sorted(set(owner_counts) - set(OWNER_DEFINITIONS)))
        )
    if sum(owner_counts.values()) != 213:
        errors.append("primary owner counts do not total 213")
    if dict(sorted(owner_counts.items())) != authority["owner_counts"]:
        errors.append("owner count summary does not match rows")
    if authority["finding_transfers"] != FINDING_TRANSFERS:
        errors.append("finding transfer table drifted")

    required_fields = {
        "implementation_owner",
        "primary_owner",
        "consumer_paths",
        "selector_policy",
        "required_or_optional",
        "stage",
        "effect_transaction",
        "positive_fixture",
        "negative_fixture",
        "functional_test",
        "integration_test",
        "trace_assertion",
        "qualification",
    }
    for row in rows:
        canonical_id = row["canonical_id"]
        missing = sorted(
            field for field in required_fields if not row.get(field)
        )
        if missing:
            errors.append(
                f"{canonical_id}: missing authority fields {','.join(missing)}"
            )
        effectful = (
            row["effect_class"] == "effect_oriented_review_required"
        )
        if effectful != bool(row.get("effect_port")):
            errors.append(
                f"{canonical_id}: effect class/port ownership mismatch"
            )
        if len(row["consumer_paths"]) != len(set(row["consumer_paths"])):
            errors.append(f"{canonical_id}: duplicate consumer paths")
        expected_gates = {
            "contract": "CP19-B",
            "selector": "CP19-C",
            "product_workflow": "CP19-J",
            "per_ka_proof": "CP19-K",
            "source_exit": "CP19-L",
            "installed_exit": "CP19-M",
        }
        for key, expected in expected_gates.items():
            if row["qualification"].get(key) != expected:
                errors.append(
                    f"{canonical_id}: qualification {key} is not {expected}"
                )

    workflow_rows = authority["workflow_dispositions"]
    workflow_paths = [row["path"] for row in workflow_rows]
    if len(workflow_paths) != len(set(workflow_paths)):
        errors.append("workflow paths have duplicate dispositions")
    for row in workflow_rows:
        if not (ROOT / row["path"]).is_file():
            errors.append(f"{row['path']}: classified workflow path missing")
        for field in (
            "system",
            "disposition",
            "target_checkpoint",
            "production_policy",
        ):
            if not row.get(field):
                errors.append(f"{row['path']}: missing {field}")

    manifest = load_manifest(RUNTIME_MANIFEST_PATH)
    if manifest.capability_count != 213:
        errors.append("runtime manifest capability count is not 213")
    if (
        manifest.authority.get("integration_authority_version")
        != authority["authority_version"]
    ):
        errors.append("runtime manifest integration authority version drift")
    for canonical_id, definition in manifest.entries.items():
        expected = next(
            row for row in rows if row["canonical_id"] == canonical_id
        )
        if definition.integration.primary_owner != expected["primary_owner"]:
            errors.append(f"{canonical_id}: runtime primary owner drift")
        if definition.integration.consumer_paths != expected["consumer_paths"]:
            errors.append(f"{canonical_id}: runtime consumer path drift")
        if definition.integration.effect_port != expected["effect_port"]:
            errors.append(f"{canonical_id}: runtime effect port drift")

    stale_future_language = (
        "existing_requires_phase18_qualification",
        "blocked_pending_phase18_qualification",
        "Phase 18 production limitation review required",
        "No production guarantee until Phase 18 qualification passes",
    )
    manifest_text = RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8")
    for marker in stale_future_language:
        if marker in manifest_text:
            errors.append(f"runtime manifest retains stale future marker: {marker}")

    return {
        "schema_version": "dle.cp19-a-integration-authority-verification.v1",
        "status": "pass" if not errors else "fail",
        "authority_version": authority["authority_version"],
        "canonical_capabilities": len(rows),
        "unique_implementation_owners": len(set(implementation_owners)),
        "primary_owner_counts": dict(sorted(owner_counts.items())),
        "workflow_dispositions": len(workflow_rows),
        "finding_transfers": len(authority["finding_transfers"]),
        "runtime_registries_added": 0,
        "rebuild_authorized": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    evidence = verify()
    if not args.no_write:
        DEFAULT_EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_EVIDENCE_PATH.write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(
        "Phase 19 KA integration authority verification: "
        + (
            "PASS"
            if evidence["status"] == "pass"
            else "FAIL: " + "; ".join(evidence["errors"])
        )
    )
    return 0 if evidence["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
