#!/usr/bin/env python3
"""Verify the Phase 16 canonical-document cap, BOM, and disposition coverage."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

try:
    from generate_documentation_authority import (
        DEFAULT_BOM,
        DEFAULT_CONFIG,
        DEFAULT_CROSSWALK,
        DEFAULT_REPORT,
        ROOT,
        load_authority,
        markdown_paths,
    )
except ModuleNotFoundError:  # Imported as scripts.verify_documentation_bom in tests.
    from scripts.generate_documentation_authority import (
        DEFAULT_BOM,
        DEFAULT_CONFIG,
        DEFAULT_CROSSWALK,
        DEFAULT_REPORT,
        ROOT,
        load_authority,
        markdown_paths,
    )


DEFAULT_VERIFICATION = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-16"
    / "documentation-bom-verification.json"
)


def verify(
    authority: dict[str, Any],
    inventory: dict[str, Any],
    *,
    root: Path = ROOT,
    bom: Path = DEFAULT_BOM,
    crosswalk: Path = DEFAULT_CROSSWALK,
) -> dict[str, Any]:
    errors: list[str] = []
    canonical = authority.get("canonical_documents", [])
    limit = int(authority.get("max_hand_maintained_canonical_documents", 0))
    ids = [item.get("id") for item in canonical]
    paths = [item.get("path") for item in canonical]
    classes = set(authority.get("document_classes", {}))
    if len(canonical) > limit:
        errors.append(f"canonical_limit_exceeded:{len(canonical)}>{limit}")
    if len(canonical) != 30:
        errors.append(f"phase16_target_count_mismatch:{len(canonical)}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate_document_id")
    if len(paths) != len(set(paths)):
        errors.append("duplicate_canonical_path")
    for item in canonical:
        if item.get("class") not in classes:
            errors.append(f"unknown_document_class:{item.get('path')}")

    rows = inventory.get("documents", [])
    row_paths = [row.get("path") for row in rows]
    expected_paths = markdown_paths(root)
    if row_paths != expected_paths:
        errors.append("markdown_inventory_drift")
    if inventory.get("unclassified"):
        errors.append("unclassified_documents")
    if inventory.get("duplicate_routes"):
        errors.append("duplicate_merge_routes")
    canonical_paths = set(paths)
    for row in rows:
        disposition = str(row.get("disposition") or "")
        if disposition.startswith("merge into ") and row.get("target") not in canonical_paths:
            errors.append(f"merge_target_not_canonical:{row.get('path')}")
    if not bom.is_file():
        errors.append("documentation_bom_missing")
    if not crosswalk.is_file():
        errors.append("documentation_crosswalk_missing")

    return {
        "schema_version": "dle.documentation-bom-verification.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "pass" if not errors else "fail",
        "canonical_count": len(canonical),
        "canonical_limit": limit,
        "inventory_count": len(rows),
        "errors": sorted(set(errors)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--bom", type=Path, default=DEFAULT_BOM)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--report", type=Path, default=DEFAULT_VERIFICATION)
    args = parser.parse_args(argv)
    authority = load_authority(args.config)
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    result = verify(
        authority,
        inventory,
        bom=args.bom,
        crosswalk=args.crosswalk,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"Documentation BOM verification: {result['status']} "
        f"canonical={result['canonical_count']}/{result['canonical_limit']} "
        f"inventory={result['inventory_count']} errors={len(result['errors'])}"
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
