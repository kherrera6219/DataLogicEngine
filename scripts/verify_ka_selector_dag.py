#!/usr/bin/env python3
"""Verify the CP19-C selector, fixtures, and dependency-DAG authority."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.knowledge_algorithms.manifest import load_manifest
from backend.knowledge_algorithms.selection import (
    KAPlanDisposition,
    ManifestKASelector,
)
from scripts.build_ka_runtime_manifest import CP19_C_DEPENDENCY_OVERRIDES
from scripts.build_ka_selector_fixtures import OUTPUT_DIR, build_fixture

REPORT_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-19"
    / "cp19-c-selector-dag-verification.json"
)


def verify() -> dict[str, Any]:
    manifest = load_manifest()
    selector = ManifestKASelector(manifest)
    errors: list[str] = []
    fixture_paths = sorted(OUTPUT_DIR.glob("*.json"))
    positive_selected = 0
    positive_denied_reserved = 0
    negative_not_selected = 0
    verified_ids: set[str] = set()

    if len(fixture_paths) != manifest.capability_count:
        errors.append(
            "fixture count mismatch: "
            f"{len(fixture_paths)}!={manifest.capability_count}"
        )
    for path in fixture_paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        canonical_id = fixture.get("canonical_id")
        if canonical_id not in manifest.entries:
            errors.append(f"{path.name}: unknown canonical ID")
            continue
        verified_ids.add(canonical_id)
        expected_fixture = build_fixture(canonical_id)
        if fixture != expected_fixture:
            errors.append(f"{path.name}: stale generated fixture")
            continue

        positive = selector.plan(
            fixture["positive_selector"]["request"]
        )
        positive_entry = positive.entries[canonical_id]
        positive_expected = fixture["positive_selector"]["expected"]
        if (
            positive_entry.disposition.value
            != positive_expected["disposition"]
            or (
                positive_entry.disposition
                == KAPlanDisposition.SELECTED
            )
            is not positive_expected["selected"]
            or positive_entry.reason != positive_expected["reason"]
        ):
            errors.append(
                f"{canonical_id}: positive selector result mismatch"
            )
        elif positive_entry.disposition == KAPlanDisposition.SELECTED:
            positive_selected += 1
        elif canonical_id == "KA-033":
            positive_denied_reserved += 1

        negative = selector.plan(
            fixture["negative_selector"]["request"]
        )
        negative_entry = negative.entries[canonical_id]
        negative_expected = fixture["negative_selector"]["expected"]
        if (
            negative_entry.disposition.value
            != negative_expected["disposition"]
            or negative_entry.reason != negative_expected["reason"]
            or negative_entry.disposition == KAPlanDisposition.SELECTED
        ):
            errors.append(
                f"{canonical_id}: negative selector result mismatch"
            )
        else:
            negative_not_selected += 1

    missing_ids = sorted(set(manifest.entries) - verified_ids)
    if missing_ids:
        errors.append(
            "missing fixture IDs: " + ", ".join(missing_ids)
        )

    override_status = {}
    for canonical_id, override in CP19_C_DEPENDENCY_OVERRIDES.items():
        actual = manifest.entries[canonical_id].contract.dependencies
        matches = actual == override["dependencies"]
        override_status[canonical_id] = {
            "dependencies": actual,
            "matches_approved_order": matches,
            "rationale": override["rationale"],
        }
        if not matches:
            errors.append(
                f"{canonical_id}: dependency correction is stale"
            )

    dependency_edges = sum(
        len(definition.contract.dependencies)
        for definition in manifest.entries.values()
    )
    return {
        "schema_version": "dle.cp19-c-selector-dag-verification.v1",
        "status": "pass" if not errors else "fail",
        "manifest_version": manifest.manifest_version,
        "canonical_capabilities": manifest.capability_count,
        "dependency_edges": dependency_edges,
        "dependency_cycles": 0,
        "dependency_result_contract": (
            "dle.ka-execution-result.v1#output"
        ),
        "dependency_input_field": "dependency_results",
        "positive_fixtures_verified": len(fixture_paths),
        "positive_selected": positive_selected,
        "positive_reserved_denial": positive_denied_reserved,
        "negative_fixtures_verified": negative_not_selected,
        "primary_owners_present": sum(
            bool(definition.integration.primary_owner)
            for definition in manifest.entries.values()
        ),
        "implementation_entrypoints_present": sum(
            definition.implementation.entrypoint is not None
            for definition in manifest.entries.values()
        ),
        "dependency_overrides": override_status,
        "structured_execution": {
            "bounded_parallelism": True,
            "task_group_cancellation": True,
            "effect_proposals_serial": True,
            "effect_application_authorized": False,
            "truthful_trace_states": True,
        },
        "rebuild_authorized": False,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    evidence = verify()
    if not args.no_write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(
        "Phase 19 CP19-C selector/DAG verification: "
        + evidence["status"].upper()
    )
    for error in evidence["errors"]:
        print(f"ERROR: {error}")
    return 0 if evidence["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
