"""Verify the Phase 18 single-manifest, single-controller runtime boundary."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.knowledge_algorithms.manifest import load_manifest
from scripts.build_ka_runtime_manifest import (
    DEFAULT_OUTPUT_PATH,
    SDK_OUTPUT_PATH,
    TYPESCRIPT_OUTPUT_PATH,
    build_manifest,
    json_text,
    typescript_text,
)

DEFAULT_EVIDENCE_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-18"
    / "cp18-b-runtime-authority.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_entrypoints(
    manifest_entries: dict[str, Any],
) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    source_owners: dict[str, str] = {}
    adapter_counts: dict[str, int] = {}
    for canonical_id, definition in manifest_entries.items():
        implementation = definition.implementation
        entrypoint = implementation.entrypoint
        if entrypoint is None:
            continue
        source = str(implementation.source)
        prior_owner = source_owners.setdefault(source, canonical_id)
        if prior_owner != canonical_id:
            errors.append(
                f"{source}: implementation owned by both "
                f"{prior_owner} and {canonical_id}"
            )
        path = ROOT / source
        if not path.is_file():
            errors.append(f"{canonical_id}: missing implementation {source}")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=source)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            errors.append(f"{canonical_id}: unreadable implementation: {exc}")
            continue
        functions = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        classes = {
            node.name: {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        }
        adapter_counts[entrypoint.adapter] = (
            adapter_counts.get(entrypoint.adapter, 0) + 1
        )
        if entrypoint.adapter == "module_run":
            if entrypoint.callable not in functions:
                errors.append(
                    f"{canonical_id}: missing function {entrypoint.callable}"
                )
        elif entrypoint.adapter == "class_execute":
            methods = classes.get(entrypoint.class_name or "", set())
            if entrypoint.callable not in methods:
                errors.append(
                    f"{canonical_id}: missing "
                    f"{entrypoint.class_name}.{entrypoint.callable}"
                )
        else:
            errors.append(
                f"{canonical_id}: unsupported adapter {entrypoint.adapter}"
            )
    return errors, adapter_counts


def _verify_runtime_boundaries() -> list[str]:
    errors: list[str] = []
    canonical_module = "from backend.knowledge_algorithms.controller import"
    adapters = (
        ROOT / "core" / "engine" / "ka_engine.py",
        ROOT / "core" / "knowledge_algorithm" / "ka_loader.py",
    )
    for path in adapters:
        text = path.read_text(encoding="utf-8")
        if canonical_module not in text or "CanonicalKAController" not in text:
            errors.append(
                f"{path.relative_to(ROOT).as_posix()}: "
                "does not delegate to CanonicalKAController"
            )
        for forbidden in ("importlib.import_module", "yaml.safe_load", ".rglob("):
            if forbidden in text:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()}: "
                    f"private runtime marker remains: {forbidden}"
                )

    sdk_handler_path = (
        ROOT
        / "sdk"
        / "UKG_Python_SDK"
        / "ukg_sdk"
        / "ka"
        / "handlers.py"
    )
    if sdk_handler_path.exists():
        errors.append("SDK private KA handler module still exists")
    builtins_path = sdk_handler_path.with_name("builtins.py")
    if "def ka_" in builtins_path.read_text(encoding="utf-8"):
        errors.append("SDK builtins still contains private KA implementations")
    for path in (
        ROOT / "backend" / "knowledge_algorithms"
    ).glob("*.py"):
        if "ukg_sdk.ka.handlers" in path.read_text(
            encoding="utf-8", errors="replace"
        ):
            errors.append(
                f"{path.relative_to(ROOT).as_posix()}: "
                "imports the removed SDK handler runtime"
            )
    return errors


def verify() -> dict[str, Any]:
    errors: list[str] = []
    expected = build_manifest()
    expected_json = json_text(expected)
    expected_typescript = typescript_text(expected)
    output_expectations = {
        DEFAULT_OUTPUT_PATH: expected_json,
        SDK_OUTPUT_PATH: expected_json,
        TYPESCRIPT_OUTPUT_PATH: expected_typescript,
    }
    for path, content in output_expectations.items():
        if not path.is_file():
            errors.append(
                f"{path.relative_to(ROOT).as_posix()}: generated catalog missing"
            )
        elif path.read_text(encoding="utf-8") != content:
            errors.append(
                f"{path.relative_to(ROOT).as_posix()}: generated catalog stale"
            )

    manifest = load_manifest(DEFAULT_OUTPUT_PATH)
    entrypoint_errors, adapter_counts = _verify_entrypoints(manifest.entries)
    errors.extend(entrypoint_errors)
    errors.extend(_verify_runtime_boundaries())

    implemented = sum(
        definition.implementation.entrypoint is not None
        for definition in manifest.entries.values()
    )
    missing = manifest.capability_count - implemented
    if manifest.capability_count != 213:
        errors.append(
            f"expected 213 canonical capabilities, got {manifest.capability_count}"
        )
    if implemented != 132 or missing != 81:
        errors.append(
            f"expected 132 existing and 81 gaps, got {implemented} and {missing}"
        )
    if "KA-133" in manifest.entries:
        errors.append("duplicate KA-133 was reintroduced as a canonical capability")
    if manifest.alias_index.get("generated-v1:KA-133") != "KA-1101":
        errors.append("reviewed Chaos Injection alias is missing or misrouted")

    evidence = {
        "schema_version": "dle.cp18-b-runtime-authority.v1",
        "status": "pass" if not errors else "fail",
        "manifest_version": manifest.manifest_version,
        "canonical_capabilities": manifest.capability_count,
        "existing_implementations": implemented,
        "implementation_gaps": missing,
        "duplicate_canonical_collisions": 0 if not errors else None,
        "reviewed_duplicate_aliases": 1,
        "scoped_aliases": len(manifest.alias_index),
        "adapter_counts": adapter_counts,
        "generated_catalogs": {
            path.relative_to(ROOT).as_posix(): (
                _sha256(path) if path.is_file() else None
            )
            for path in output_expectations
        },
        "single_controller": (
            "backend.knowledge_algorithms.controller.CanonicalKAController"
        ),
        "private_sdk_handler_runtime_present": False,
        "errors": errors,
    }
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence",
        type=Path,
        default=DEFAULT_EVIDENCE_PATH,
        help="Path for machine-readable verification evidence.",
    )
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = verify()
    if not args.no_write:
        output = args.evidence
        if not output.is_absolute():
            output = ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    summary = (
        "PASS"
        if evidence["status"] == "pass"
        else "FAIL: " + "; ".join(evidence["errors"])
    )
    print(f"Phase 18 KA runtime authority verification: {summary}")
    return 0 if evidence["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
