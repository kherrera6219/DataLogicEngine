"""Verify the approved Phase 18 Knowledge Algorithm capability authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_ka_capability_inventory import (
    DEFAULT_OUTPUT_DIR,
    ORIGINAL_REGISTRY_PATH,
    SDK_REGISTRY_PATH,
    build_inventory,
    load_live_registry,
    output_payloads,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CANONICAL_CAPABILITIES = 213
BASELINE_EXISTING_IMPLEMENTATIONS = 132
BASELINE_REQUIRED_IMPLEMENTATIONS = 81
EXPECTED_GENERIC_SCAFFOLDS = 64


def verify() -> tuple[list[str], dict[str, Any]]:
    inventory, crosswalk = build_inventory()
    summary = crosswalk["summary"]
    errors: list[str] = []

    expected_counts = {
        "canonical_capability_proposals": EXPECTED_CANONICAL_CAPABILITIES,
        "generated_generic_scaffolds": EXPECTED_GENERIC_SCAFFOLDS,
        "unclassified_source_definitions": 0,
        "semantic_duplicate_aliases": 1,
        "unresolved_semantic_duplicate_candidates": 0,
        "exact_canonical_name_collisions": 0,
        "exact_canonical_purpose_collisions": 0,
        "exact_canonical_contract_collisions": 0,
        "unclassified_implementation_surfaces": 0,
        "unclassified_integration_surfaces": 0,
    }
    for key, expected in expected_counts.items():
        actual = summary.get(key)
        if actual != expected:
            errors.append(f"{key}: expected {expected}, got {actual}")

    existing = summary["existing_implementation_proposals"]
    required = summary["implementation_required_proposals"]
    if existing + required != EXPECTED_CANONICAL_CAPABILITIES:
        errors.append(
            "implementation accounting does not equal the canonical "
            f"capability count: {existing} + {required}"
        )
    if existing < BASELINE_EXISTING_IMPLEMENTATIONS:
        errors.append(
            "existing implementations regressed below the CP18-A baseline: "
            f"{existing} < {BASELINE_EXISTING_IMPLEMENTATIONS}"
        )
    if required > BASELINE_REQUIRED_IMPLEMENTATIONS:
        errors.append(
            "implementation gaps exceed the CP18-A baseline: "
            f"{required} > {BASELINE_REQUIRED_IMPLEMENTATIONS}"
        )

    if inventory["status"] != "cp18_a_inventory_verified":
        errors.append(f"inventory status is not approved: {inventory['status']}")
    if crosswalk["status"] != "approved_cp18_a_authority":
        errors.append(f"crosswalk status is not approved: {crosswalk['status']}")
    if inventory["source_input_sha256"] != crosswalk["source_input_sha256"]:
        errors.append("inventory and crosswalk source-input digests differ")

    canonical_rows = crosswalk["canonical_capabilities"]
    rows_by_id = {row["canonical_id"]: row for row in canonical_rows}
    if len(rows_by_id) != len(canonical_rows):
        errors.append("canonical capability IDs are not unique")

    required_fields = {
        "canonical_id",
        "name",
        "identity_class",
        "implementation_status",
        "effect_class",
        "contract_status",
        "input_descriptions",
        "output_descriptions",
        "categories",
        "layer_scope",
        "persona_scope",
        "subsystems",
        "dependency_source_ids",
        "triggers",
        "risk_classes",
        "design_contracts",
        "migration_notes",
        "source_records",
        "scoped_aliases",
    }
    for row in canonical_rows:
        missing = sorted(required_fields - set(row))
        if missing:
            errors.append(f"{row.get('canonical_id')}: missing fields {missing}")
        if not row.get("name") or not row.get("migration_notes"):
            errors.append(f"{row.get('canonical_id')}: empty name or migration notes")
        if row.get("implementation"):
            analysis = row.get("implementation_analysis") or {}
            if not analysis.get("exists") or not analysis.get(
                "has_execution_entry_point"
            ):
                errors.append(
                    f"{row['canonical_id']}: implementation missing or has no "
                    "run/execute entry point"
                )

    live = load_live_registry()
    for ka_id, implementation in live.items():
        row = rows_by_id.get(ka_id)
        if row is None:
            errors.append(f"{ka_id}: live registry ID is not canonical")
            continue
        expected_path = implementation.rsplit(".", 1)[0].replace(".", "/") + ".py"
        if row.get("implementation") != expected_path:
            errors.append(
                f"{ka_id}: implementation changed from {expected_path} "
                f"to {row.get('implementation')}"
            )
    for number in range(1, 8):
        ka_id = f"L9-KA-{number:03d}"
        if ka_id not in rows_by_id:
            errors.append(f"{ka_id}: Layer-9 implementation is not canonical")

    original_source = ORIGINAL_REGISTRY_PATH.relative_to(ROOT).as_posix()
    original_rows = [
        row
        for row in inventory["source_definitions"]
        if row["source"] == original_source
    ]
    if len(original_rows) != summary["original_design_rows"]:
        errors.append(
            "original design registry row count does not match classified definitions"
        )
    for row in original_rows:
        if not row.get("canonical_id") or row["canonical_id"] not in rows_by_id:
            errors.append(
                f"{row['source_id']}: original design capability is unresolved"
            )

    sdk_source = SDK_REGISTRY_PATH.relative_to(ROOT).as_posix()
    sdk_rows = [
        row for row in inventory["source_definitions"] if row["source"] == sdk_source
    ]
    if len(sdk_rows) != summary["sdk_registry_rows"]:
        errors.append("SDK registry row count does not match classified definitions")
    for row in sdk_rows:
        if not row.get("canonical_id") or row["canonical_id"] not in rows_by_id:
            errors.append(f"{row['source_id']}: SDK capability is unresolved")

    aliases: dict[str, str] = {}
    for row in canonical_rows:
        for alias in row["scoped_aliases"]:
            prior = aliases.setdefault(alias, row["canonical_id"])
            if prior != row["canonical_id"]:
                errors.append(
                    f"{alias}: scoped alias resolves to both {prior} and "
                    f"{row['canonical_id']}"
                )

    for conflict in inventory["identity_conflicts"]:
        if conflict.get(
            "status"
        ) != "classified_by_scoped_alias_or_restored_id" or not conflict.get(
            "canonical_resolutions"
        ):
            errors.append(f"{conflict.get('source_id')}: unresolved identity conflict")

    if rows_by_id.get("KA-113", {}).get("name") != "Complexity Router":
        errors.append("KA-113 reviewed semantic-equivalence decision is missing")
    if rows_by_id.get("KA-1113") is not None:
        errors.append("KA-113 was incorrectly duplicated as KA-1113")
    if rows_by_id.get("KA-036", {}).get("name") != "Complexity Estimator":
        errors.append("KA-036 current executable identity was overwritten")
    if rows_by_id.get("KA-1036", {}).get("name") != "Pareto Optimization Engine":
        errors.append("KA-036 original design capability was not restored as KA-1036")
    if "KA-133" in rows_by_id:
        errors.append("generated KA-133 duplicates the canonical chaos governor")
    if "generated-v1:KA-133" not in rows_by_id.get("KA-1101", {}).get(
        "scoped_aliases", []
    ):
        errors.append("KA-133 compatibility alias is not bound to KA-1101")
    if (
        rows_by_id.get("L10-KA-006", {}).get("name")
        != "Layer-10 Belief-Decay Trust Gate"
    ):
        errors.append("Layer-10 trust gate does not have a unique canonical name")

    duplicate_review = crosswalk.get("duplicate_review") or {}
    for candidate in duplicate_review.get("reviewed_candidate_pairs", []):
        if candidate.get("disposition") != "reviewed_materially_distinct":
            errors.append(
                f"{candidate.get('canonical_ids')}: semantic duplicate candidate "
                "does not have a material-distinctness decision"
            )

    expected_payloads = output_payloads(DEFAULT_OUTPUT_DIR)
    for path, content in expected_payloads.items():
        if not path.exists():
            errors.append(f"{path.relative_to(ROOT)}: generated evidence missing")
        elif path.read_text(encoding="utf-8") != content:
            errors.append(f"{path.relative_to(ROOT)}: generated evidence is stale")

    result = {
        "schema_version": "dle.ka-capability-inventory-verification.v1",
        "status": "pass" if not errors else "fail",
        "source_input_sha256": inventory["source_input_sha256"],
        "canonical_capabilities": summary["canonical_capability_proposals"],
        "existing_implementations": summary["existing_implementation_proposals"],
        "implementation_required": summary["implementation_required_proposals"],
        "classified_identity_conflicts": summary["classified_identity_conflicts"],
        "semantic_duplicate_aliases": summary["semantic_duplicate_aliases"],
        "reviewed_distinct_candidate_pairs": summary[
            "reviewed_distinct_candidate_pairs"
        ],
        "unresolved_semantic_duplicate_candidates": summary[
            "unresolved_semantic_duplicate_candidates"
        ],
        "exact_canonical_name_collisions": summary["exact_canonical_name_collisions"],
        "exact_canonical_purpose_collisions": summary[
            "exact_canonical_purpose_collisions"
        ],
        "exact_canonical_contract_collisions": summary[
            "exact_canonical_contract_collisions"
        ],
        "implementation_surfaces": summary["implementation_surfaces"],
        "integration_surfaces": summary["integration_surfaces"],
        "unclassified_total": (
            summary["unclassified_source_definitions"]
            + summary["unclassified_implementation_surfaces"]
            + summary["unclassified_integration_surfaces"]
        ),
        "errors": errors,
    }
    return errors, result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors, result = verify()
    if args.json:
        print(json.dumps(result, indent=2))
    elif errors:
        print("Phase 18 KA capability inventory verification: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print(
            "Phase 18 KA capability inventory verification: PASS "
            f"(canonical={result['canonical_capabilities']}, "
            f"existing={result['existing_implementations']}, "
            f"build={result['implementation_required']}, "
            f"duplicate_aliases={result['semantic_duplicate_aliases']}, "
            "duplicate_collisions=0, "
            f"unclassified={result['unclassified_total']})"
        )
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
