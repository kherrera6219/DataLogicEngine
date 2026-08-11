#!/usr/bin/env python3
"""Generate reviewable project-knowledge exports from live source authorities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "docs" / "spec-exports"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CANONICAL_API_CANDIDATE_MAPPINGS: dict[str, list[str]] = {
    "/enhance": ["/gateway/chat", "/v1/chat/completions"],
    "/enhance/stream": ["/gateway/chat/stream"],
    "/knowledge/ingest": ["/ingestion/local"],
    "/knowledge/ingest/{ingestion_id}/status": ["/ingestion/status/{ingestion_id}"],
    "/truth/gate/check": ["/truth/gate/evaluate"],
    "/audit/{request_id}": ["/trace/runs/{run_id}/bundle"],
    "/audit/{request_id}/download": ["/trace/runs/{run_id}/export"],
    "/audit/{request_id}/export": ["/trace/runs/{run_id}/export"],
    "/status": ["/ready"],
    "/workflow/run": ["/ka/runs"],
    "/truth/gate": ["/truth/gate/evaluate"],
}

AXIS_MANAGER_MODULES = {
    14: "core.axes.axis14_acquisition_lifecycle",
    15: "core.axes.axis15_risk_threat",
    16: "core.axes.axis16_ethics_trust",
    17: "core.axes.axis17_frost_mode",
}


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )


def _ka_registry(root: Path) -> dict[str, Any]:
    source = root / "backend" / "knowledge_algorithms" / "ka_manifest.v1.generated.json"
    manifest = json.loads(source.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    entries = list(entries.values()) if isinstance(entries, dict) else list(entries)
    algorithms = []
    for entry in entries:
        admission = entry.get("admission") or {}
        algorithms.append(
            {
                "id": entry["canonical_id"],
                "name": entry.get("name"),
                "purpose": entry.get("purpose"),
                "version": entry.get("version"),
                "production_enabled": bool(admission.get("production_enabled")),
                "classification": admission.get("classification"),
                "identity_class": entry.get("identity_class"),
                "aliases": entry.get("aliases") or {},
                "implementation": entry.get("implementation") or {},
                "contract": entry.get("contract") or {},
                "integration": entry.get("integration") or {},
                "migration_notes": entry.get("migration_notes"),
            }
        )
    return {
        "schema_version": "ukg.ka-registry-spec-export.v1",
        "status": "review export; upload to project knowledge after owner review",
        "generated_from": str(source.relative_to(root)).replace("\\", "/"),
        "manifest_version": manifest["manifest_version"],
        "capability_count": len(algorithms),
        "production_enabled_count": sum(item["production_enabled"] for item in algorithms),
        "algorithms": algorithms,
    }


def _axes_14_17() -> dict[str, Any]:
    from core.coordinate_system import UnifiedCoordinate

    return {
        "schema_version": "ukg.axis-coordinate-spec-export.v1",
        "status": "replacement block for owner review and project-knowledge upload",
        "generated_from": "core/coordinate_system.py:UnifiedCoordinate",
        "axes": {
            number: {
                "name": UnifiedCoordinate.AXIS_NAMES[number],
                "encoding": UnifiedCoordinate.AXIS_FORMATS[number],
                "manager_module": AXIS_MANAGER_MODULES[number],
            }
            for number in range(14, 18)
        },
    }


def _methods(path_item: Any) -> str:
    if not isinstance(path_item, dict):
        return ""
    methods = [
        method.upper()
        for method in path_item
        if method.lower() in {"get", "post", "put", "patch", "delete", "head", "options"}
    ]
    return ", ".join(methods)


def _api_delta(root: Path) -> str:
    canonical_path = (
        root / "docs" / "archive" / "api" / "ukg_api_v3_2-roadmap-2026-01.yaml"
    )
    live_path = root / "docs" / "openapi.yaml"
    canonical = yaml.safe_load(canonical_path.read_text(encoding="utf-8"))
    live = yaml.safe_load(live_path.read_text(encoding="utf-8"))
    canonical_paths = canonical.get("paths") or {}
    live_paths = live.get("paths") or {}

    rows = []
    counts = {"exact": 0, "candidate mapping": 0, "absent": 0}
    for path, item in canonical_paths.items():
        if path in live_paths:
            status = "exact"
            target = path
        else:
            candidates = [
                candidate
                for candidate in CANONICAL_API_CANDIDATE_MAPPINGS.get(path, [])
                if candidate in live_paths
            ]
            if candidates:
                status = "candidate mapping"
                target = ", ".join(f"`{candidate}`" for candidate in candidates)
            else:
                status = "absent"
                target = "—"
        counts[status] += 1
        rows.append(
            f"| `{path}` | {_methods(item)} | {status} | {target} |"
        )

    return "\n".join(
        [
            "# Canonical UKG API vs. current documented API",
            "",
            "| Field | Value |",
            "|---|---|",
            "| Status | Historical roadmap comparison; no compatibility or release claim |",
            "| Historical roadmap source | `docs/archive/api/ukg_api_v3_2-roadmap-2026-01.yaml` |",
            "| Supported integration authority | `docs/openapi.yaml` |",
            f"| Canonical paths | **{len(canonical_paths)}** |",
            f"| Live documented paths | **{len(live_paths)}** |",
            f"| Exact paths | **{counts['exact']}** |",
            f"| Candidate mappings | **{counts['candidate mapping']}** |",
            f"| Absent from live document | **{counts['absent']}** |",
            "",
            "Candidate mappings are name-level review leads, not assertions of request/response",
            "compatibility. D-3 formally selects docs/openapi.yaml and the live /api/v1",
            "routes as the supported product contract; the UKG v3.2 source is roadmap history.",
            "",
            "| Canonical path | Methods | Disposition | Live documented path |",
            "|---|---|---|---|",
            *rows,
            "",
        ]
    )


def generate_spec_exports(
    *, root: Path = ROOT, output_dir: Path = DEFAULT_OUTPUT_DIR
) -> dict[str, Path]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "ka_registry": output_dir / "ka_registry_213.yaml",
        "axes_14_17": output_dir / "17_axis_coordinate_schema_axes14-17.yaml",
        "api_delta": output_dir / "api_delta.md",
    }
    _write_yaml(outputs["ka_registry"], _ka_registry(root))
    _write_yaml(outputs["axes_14_17"], _axes_14_17())
    outputs["api_delta"].write_text(_api_delta(root), encoding="utf-8")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    for path in generate_spec_exports(output_dir=args.output_dir).values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
