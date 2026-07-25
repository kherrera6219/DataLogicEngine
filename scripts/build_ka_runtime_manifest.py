"""Generate the canonical Knowledge Algorithm runtime manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_ka_integration_authority import (
    DEFAULT_JSON_PATH as INTEGRATION_AUTHORITY_PATH,
)
from scripts.build_ka_integration_authority import (
    build_authority as build_integration_authority,
)

CROSSWALK_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-18"
    / "ka-capability-crosswalk.json"
)
DEFAULT_OUTPUT_PATH = (
    ROOT / "backend" / "knowledge_algorithms" / "ka_manifest.v1.generated.json"
)
SDK_OUTPUT_PATH = (
    ROOT
    / "sdk"
    / "UKG_Python_SDK"
    / "ukg_sdk"
    / "data"
    / "ka_manifest.v1.generated.json"
)
TYPESCRIPT_OUTPUT_PATH = (
    ROOT
    / "sdk"
    / "DataLogicEngine_TypeScript_SDK"
    / "src"
    / "ka-manifest.generated.ts"
)


def normalize_ka_id(value: str) -> str:
    clean = str(value).strip().upper()
    if clean == "KA-MASTER":
        return "KA-Master"
    layer_match = re.fullmatch(r"(L(?:9|10)-KA-)(\d+)", clean)
    if layer_match:
        return f"{layer_match.group(1)}{int(layer_match.group(2)):03d}"
    numeric_match = re.fullmatch(r"KA-(\d+)", clean)
    if numeric_match:
        number = int(numeric_match.group(1))
        width = 3 if number < 1000 else 4
        return f"KA-{number:0{width}d}"
    return clean


def module_from_path(path: str) -> str:
    return path.removesuffix(".py").replace("/", ".").replace("\\", ".")


def choose_entrypoint(row: dict[str, Any]) -> dict[str, Any] | None:
    implementation = row.get("implementation")
    if not implementation:
        return None
    module = module_from_path(implementation)
    if row["canonical_id"].startswith("L9-KA-"):
        classes = [
            name
            for name in row["implementation_analysis"].get("classes", [])
            if not name.endswith("Input")
        ]
        if len(classes) != 1:
            raise ValueError(
                f"{row['canonical_id']}: expected one Layer-9 execution class, "
                f"got {classes}"
            )
        return {
            "adapter": "class_execute",
            "module": module,
            "class_name": classes[0],
            "callable": "execute",
        }
    return {
        "adapter": "module_run",
        "module": module,
        "callable": "run",
    }


def build_manifest() -> dict[str, Any]:
    crosswalk = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    if crosswalk.get("status") != "approved_cp18_a_authority":
        raise ValueError("CP18-A crosswalk is not approved")
    integration_authority = build_integration_authority()
    if integration_authority.get("status") != "approved_cp19_a_authority":
        raise ValueError("CP19-A integration authority is not approved")
    integration_by_id = {
        row["canonical_id"]: row
        for row in integration_authority["canonical_capabilities"]
    }

    rows = crosswalk["canonical_capabilities"]
    scoped_alias_index = {
        alias: row["canonical_id"]
        for row in rows
        for alias in row.get("scoped_aliases", [])
    }

    def resolve_design_dependency(value: str) -> str:
        normalized = normalize_ka_id(value)
        return scoped_alias_index.get(
            f"design-v1:{normalized}",
            normalized,
        )

    entries: dict[str, dict[str, Any]] = {}
    for row in rows:
        integration = integration_by_id[row["canonical_id"]]
        design_contracts = row.get("design_contracts", [])
        versions = [
            str(contract["version"])
            for contract in design_contracts
            if contract.get("version")
        ]
        production = row.get("phase6_production_metadata") or {}
        dependencies = sorted(
            {
                resolve_design_dependency(dependency)
                for dependency in row.get("dependency_source_ids", [])
            }
        )
        existing = bool(row.get("implementation"))
        entries[row["canonical_id"]] = {
            "canonical_id": row["canonical_id"],
            "name": row["name"],
            "purpose": row.get("purpose"),
            "version": versions[0] if versions else "1.0.0",
            "identity_class": row["identity_class"],
            "aliases": {
                "scoped": row.get("scoped_aliases", []),
                "unscoped": [],
            },
            "implementation": {
                "status": (
                    "implemented_pending_phase19_integration"
                    if existing
                    else "implementation_required"
                ),
                "source": row.get("implementation"),
                "entrypoint": choose_entrypoint(row),
            },
            "contract": {
                "version": "dle.ka-execution.v1",
                "status": "pending_cp19_b_contract_parity",
                "inputs": row.get("input_descriptions", []),
                "outputs": row.get("output_descriptions", []),
                "categories": row.get("categories", []),
                "layers": row.get("layer_scope", []),
                "personas": row.get("persona_scope", []),
                "subsystems": row.get("subsystems", []),
                "dependencies": dependencies,
                "triggers": row.get("triggers", []),
                "risk_classes": row.get("risk_classes", []),
                "effect_class": row["effect_class"],
                "reads_memory": any(
                    contract.get("reads_memory")
                    for contract in design_contracts
                ),
                "writes_memory": any(
                    contract.get("writes_memory")
                    for contract in design_contracts
                ),
                "produces_artifacts": any(
                    contract.get("produces_artifacts")
                    for contract in design_contracts
                ),
                "audit_events": any(
                    contract.get("audit_events")
                    for contract in design_contracts
                ),
                "limitations": production.get("limitations")
                or "Phase 19 capability limitation review required.",
                "guarantee": production.get("guarantee")
                or (
                    "No production guarantee until CP19-K per-KA proof and "
                    "CP19-M rebuilt-installed acceptance pass."
                ),
                "performance_budget_ms": production.get(
                    "performance_budget_ms", 1000
                ),
            },
            "admission": {
                "production_enabled": bool(production.get("production_enabled")),
                "classification": production.get("classification")
                or "implementation_required",
                "deterministic": production.get("deterministic"),
                "direct_execution": (
                    "legacy_production_enabled"
                    if production.get("production_enabled")
                    else "blocked_pending_cp19_c_selector_qualification"
                ),
            },
            "integration": {
                "authority_version": integration_authority[
                    "authority_version"
                ],
                "primary_owner": integration["primary_owner"],
                "consumer_paths": integration["consumer_paths"],
                "selector_policy": integration["selector_policy"],
                "required_or_optional": integration["required_or_optional"],
                "stage": integration["stage"],
                "effect_port": integration["effect_port"],
                "effect_transaction": integration["effect_transaction"],
                "qualification": integration["qualification"],
            },
            "migration_notes": row["migration_notes"],
        }

    return {
        "schema_version": "dle.ka-runtime-manifest.v1",
        "manifest_version": "2026.07.25-cp19a.1",
        "status": "cp19_a_integration_authority",
        "authority": {
            "crosswalk": CROSSWALK_PATH.relative_to(ROOT).as_posix(),
            "crosswalk_schema_version": crosswalk["schema_version"],
            "crosswalk_source_input_sha256": crosswalk["source_input_sha256"],
            "integration_authority": INTEGRATION_AUTHORITY_PATH.relative_to(
                ROOT
            ).as_posix(),
            "integration_authority_version": integration_authority[
                "authority_version"
            ],
            "duplicate_policy": "one_semantic_capability_one_canonical_id",
        },
        "capability_count": len(entries),
        "alias_index": {
            alias: canonical_id
            for alias, canonical_id in sorted(scoped_alias_index.items())
        },
        "entries": {key: entries[key] for key in sorted(entries)},
    }


def json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def typescript_text(payload: dict[str, Any]) -> str:
    return (
        "/* Generated by scripts/build_ka_runtime_manifest.py. Do not edit. */\n"
        'import type { KARuntimeManifestCatalog } from "./ka-types.js";\n\n'
        "export const KA_RUNTIME_MANIFEST: KARuntimeManifestCatalog = "
        f"{json.dumps(payload, indent=2, ensure_ascii=False)};\n"
    )


def write_or_check(path: Path, *, check: bool) -> int:
    payload = build_manifest()
    outputs = [(path, json_text(payload))]
    if path == DEFAULT_OUTPUT_PATH:
        outputs.extend(
            [
                (SDK_OUTPUT_PATH, json_text(payload)),
                (TYPESCRIPT_OUTPUT_PATH, typescript_text(payload)),
            ]
        )
    stale = []
    for output, content in outputs:
        existing = (
            output.read_text(encoding="utf-8") if output.exists() else None
        )
        if existing != content:
            stale.append(output)
            if not check:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(content, encoding="utf-8", newline="\n")
    if check and stale:
        for output in stale:
            print(f"STALE {output.relative_to(ROOT)}")
        return 1
    action = "verified" if check else "generated"
    print(
        f"KA runtime manifests {action}: "
        + ", ".join(
            output.relative_to(ROOT).as_posix() for output, _ in outputs
        )
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output
    if not output.is_absolute():
        output = ROOT / output
    return write_or_check(output.resolve(), check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
