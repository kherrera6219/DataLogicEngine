#!/usr/bin/env python3
"""Verify complete, single-valued dispositions for the Phase 0 feature ledger."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "reports/production-readiness/2026/phase-00"
DEFAULT_INPUT = PHASE / "feature-disposition.json"
ALLOWED = {"ship", "finish", "disable", "defer", "remove"}
REQUIRED = {"id", "kind", "source", "disposition", "rationale", "target_phase", "owner", "verification_status"}


def expected_count() -> int:
    runtime = json.loads((PHASE / "runtime/runtime-surfaces.json").read_text(encoding="utf-8"))
    ui = json.loads((PHASE / "runtime/ui-controls.json").read_text(encoding="utf-8"))
    services = json.loads((PHASE / "runtime/service-consumers.json").read_text(encoding="utf-8"))
    runtime_keys = (
        "flask_routes", "graphql_operations", "electron_ipc", "websocket_sse",
        "preload_exports", "mcp_methods", "local_file_entries", "external_network_domains",
    )
    service_count = sum(len(rows) for rows in services["service_consumers"].values())
    return (
        len(ui["pages"])
        + len(ui["controls"])
        + sum(len(runtime.get(key, [])) for key in runtime_keys)
        + service_count
        + len(services["fallback_references"])
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    path = args.input if args.input.is_absolute() else ROOT / args.input
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("features", [])
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
        if row.get("disposition") not in ALLOWED:
            errors.append(f"{identifier}: invalid disposition {row.get('disposition')!r}")
        if not row.get("owner") or not row.get("rationale"):
            errors.append(f"{identifier}: owner and rationale are required")
    expected = expected_count()
    if len(rows) != expected:
        errors.append(f"feature coverage mismatch: expected {expected}, found {len(rows)}")
    result = {
        "features": len(rows),
        "expected": expected,
        "dispositions": Counter(row.get("disposition") for row in rows),
        "errors": errors,
        "passed": not errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
