#!/usr/bin/env python3
"""Verify that every Phase 0 requirement has complete ownership and trace fields."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "reports/production-readiness/2026/phase-00/requirements-traceability.json"
REQUIRED = {
    "id", "product_intent", "ui_surface", "contract", "owning_service_or_store",
    "implementation", "automated_tests", "manual_tests", "evidence",
    "user_documentation", "target_phase", "status", "acceptance_authority",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    path = args.input if args.input.is_absolute() else ROOT / args.input
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("requirements", [])
    errors: list[str] = []
    identifiers: set[str] = set()
    for index, row in enumerate(rows):
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"row {index}: missing {', '.join(missing)}")
        identifier = row.get("id")
        if not identifier or identifier in identifiers:
            errors.append(f"row {index}: missing or duplicate id {identifier!r}")
        identifiers.add(identifier)
        if not isinstance(row.get("target_phase"), int) or not 0 <= row["target_phase"] <= 18:
            errors.append(f"{identifier}: invalid target phase")
        for field in REQUIRED - {"target_phase"}:
            if field in row and row[field] in (None, "", []):
                errors.append(f"{identifier}: empty {field}")
    if not rows:
        errors.append("no requirements found")
    result = {"requirements": len(rows), "errors": errors, "passed": not errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
