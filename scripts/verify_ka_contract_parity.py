#!/usr/bin/env python3
"""Verify CP19-B canonical result-contract parity for production callers."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-19"
    / "cp19-b-contract-parity-verification.json"
)

MIGRATED_CALLERS = {
    "api": "backend/routes/ka_routes.py",
    "ka_master": "backend/knowledge_algorithms/ka_master_controller.py",
    "truthcore": "backend/truth_engine/truth_core/engine.py",
    "layer6": "backend/truth_engine/truth_gate/quant.py",
    "layer7": "backend/truth_engine/truth_core/agi_planner.py",
    "layer8": (
        "backend/truth_engine/truth_gate/"
        "trust_validation_gateway.py"
    ),
    "layer9": (
        "backend/truth_engine/truth_core/"
        "meta_reasoning_controller.py"
    ),
    "layer10": (
        "backend/truth_engine/truth_core/emergence_controller.py"
    ),
    "personas": "backend/truth_engine/truth_core/personas.py",
    "refinement": (
        "backend/truth_engine/truth_core/refinement_orchestrator.py"
    ),
    "core_engine_adapter": "core/engine/ka_engine.py",
    "core_loader_adapter": "core/knowledge_algorithm/ka_loader.py",
    "query_persona": "core/simulation/query_persona_engine.py",
    "pov": "core/simulation/pov_engine.py",
    "simulation": "core/simulation/simulation_engine.py",
    "sekre": "core/self_evolving/sekre_engine.py",
}
EXTERNAL_TYPED_SURFACES = {
    "python_sdk": (
        "sdk/UKG_Python_SDK/ukg_sdk/ka/executor.py",
        "canonical_result",
    ),
    "typescript_sdk": (
        "sdk/DataLogicEngine_TypeScript_SDK/src/ka-types.ts",
        'schema_version: "dle.ka-execution-result.v1"',
    ),
}
LEGACY_METHODS = {"execute_algorithm", "execute_legacy", "execute_ka"}
TYPED_METHODS = {"execute_typed", "execute_algorithm_plan"}
TYPED_HELPERS = {"execute_required_ka"}


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def verify() -> dict[str, Any]:
    errors: list[str] = []
    legacy_calls: list[str] = []
    typed_calls: list[str] = []
    production_files: list[Path] = []
    for source_root in ("backend", "core"):
        production_files.extend((ROOT / source_root).rglob("*.py"))

    for path in sorted(production_files):
        relative = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8"),
                filename=relative,
            )
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            errors.append(f"{relative}: cannot parse: {exc}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            location = f"{relative}:{node.lineno}"
            if name in LEGACY_METHODS:
                legacy_calls.append(location)
            if name in TYPED_METHODS | TYPED_HELPERS:
                typed_calls.append(location)

    if legacy_calls:
        errors.append(
            "legacy production KA result calls remain: "
            + ", ".join(legacy_calls)
        )

    caller_status: dict[str, dict[str, Any]] = {}
    typed_markers = tuple(sorted(TYPED_METHODS | TYPED_HELPERS))
    for subsystem, relative in MIGRATED_CALLERS.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"{relative}: migrated caller missing")
            caller_status[subsystem] = {
                "path": relative,
                "typed_boundary_present": False,
            }
            continue
        source = path.read_text(encoding="utf-8")
        typed_boundary_present = any(
            marker in source for marker in typed_markers
        )
        if not typed_boundary_present:
            errors.append(f"{relative}: typed boundary missing")
        caller_status[subsystem] = {
            "path": relative,
            "typed_boundary_present": typed_boundary_present,
        }
    for subsystem, (relative, marker) in EXTERNAL_TYPED_SURFACES.items():
        path = ROOT / relative
        typed_boundary_present = (
            path.is_file()
            and marker in path.read_text(encoding="utf-8")
        )
        if not typed_boundary_present:
            errors.append(f"{relative}: canonical SDK result marker missing")
        caller_status[subsystem] = {
            "path": relative,
            "typed_boundary_present": typed_boundary_present,
        }

    required_contracts = {
        "backend/knowledge_algorithms/contracts.py": (
            "def require_output(",
            "class KAExecutionContractError",
        ),
        "backend/knowledge_algorithms/consumer.py": (
            "def execute_required_ka(",
            "def require_output_field(",
        ),
    }
    for relative, markers in required_contracts.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in source:
                errors.append(f"{relative}: missing {marker}")

    return {
        "schema_version": "dle.cp19-b-contract-parity-verification.v1",
        "status": "pass" if not errors else "fail",
        "production_python_files_scanned": len(production_files),
        "migrated_caller_surfaces": (
            len(MIGRATED_CALLERS) + len(EXTERNAL_TYPED_SURFACES)
        ),
        "caller_status": caller_status,
        "typed_execution_call_sites": len(typed_calls),
        "legacy_execution_call_sites": legacy_calls,
        "canonical_result_schema": "dle.ka-execution-result.v1",
        "required_failure_policy": "raise_or_fail_closed",
        "remaining_semantic_integration": {
            "layer9_layer10_identity": "CP19-E",
            "selector_and_dependency_dag": "CP19-C",
            "ten_layer_product_path": "CP19-D",
            "persona_and_dsqp": "CP19-F",
            "twelve_step_workflow": "CP19-G",
            "data_knowledge_lifecycle": "CP19-H",
            "simulation_mcp_provider_operations_effects": "CP19-I",
            "api_sdk_desktop_accessibility": "CP19-J",
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
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    summary = (
        "PASS"
        if evidence["status"] == "pass"
        else "FAIL: " + "; ".join(evidence["errors"])
    )
    print(f"Phase 19 KA contract parity verification: {summary}")
    return 0 if evidence["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
