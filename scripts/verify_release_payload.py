#!/usr/bin/env python3
"""Verify that a Windows release payload contains runtime assets but no dev leakage."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_BACKEND_FILES = (
    "DataLogic_Backend.exe",
    "_internal/config/product-versions.json",
    "_internal/config/provider_manifest.v1.json",
    "_internal/deploy/internal-data-plane.candidate-lock.json",
    "_internal/migrations/alembic.ini",
    "_internal/core/data/ka_registry.json",
    "_internal/backend/dsqp/templates/default.json",
    "_internal/backend/knowledge_algorithms/ka_registry.yaml",
    "_internal/backend/security/prompts/defense_supervisor.txt",
    "_internal/backend/api/specs/ukg_api_v3_2.yaml",
    "_internal/core/persona/quad/config/quad_config.yaml",
    "_internal/docs/evaluation/AI_SYSTEM_CARD.md",
)

FORBIDDEN_PARTS = {"test", "tests", "testing", "__pycache__", ".pytest_cache"}
APP_SOURCE_ROOTS = ("_internal/backend/", "_internal/core/")


def verify_payload(backend_root: Path, electron_compile_root: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    backend_files = sorted(path for path in backend_root.rglob("*") if path.is_file()) if backend_root.is_dir() else []
    relative_files = [path.relative_to(backend_root).as_posix() for path in backend_files]
    relative_set = set(relative_files)

    if not backend_root.is_dir():
        issues.append({"check": "backend_root", "path": str(backend_root), "detail": "Backend payload root is missing."})
    for required in REQUIRED_BACKEND_FILES:
        if required not in relative_set:
            issues.append({"check": "required_runtime_asset", "path": required, "detail": "Required runtime asset is missing."})

    for relative in relative_files:
        parts = {part.lower() for part in Path(relative).parts}
        if parts.intersection(FORBIDDEN_PARTS):
            issues.append({"check": "development_tree", "path": relative, "detail": "Test or cache content is forbidden in the release payload."})
        if relative.lower().endswith((".py", ".pyc")) and relative.startswith(APP_SOURCE_ROOTS):
            issues.append({"check": "application_source", "path": relative, "detail": "Application source is forbidden in the frozen payload."})

    compiled_files = (
        sorted(path for path in electron_compile_root.rglob("*") if path.is_file())
        if electron_compile_root.is_dir()
        else []
    )
    compiled_relative = [path.relative_to(electron_compile_root).as_posix() for path in compiled_files]
    for relative in compiled_relative:
        lower = relative.lower()
        if lower.endswith((".test.js", ".spec.js", ".test.js.map", ".spec.js.map")):
            issues.append({"check": "electron_test_bundle", "path": relative, "detail": "Compiled Electron tests are forbidden in the release payload."})

    return {
        "schema_version": "dle.release-payload-verification.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "pass" if not issues else "fail",
        "summary": {
            "backend_file_count": len(relative_files),
            "backend_size_bytes": sum(path.stat().st_size for path in backend_files),
            "electron_compiled_file_count": len(compiled_relative),
            "issue_count": len(issues),
        },
        "required_backend_files": list(REQUIRED_BACKEND_FILES),
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-root", type=Path, default=ROOT / "dist" / "DataLogic_Backend")
    parser.add_argument("--electron-compile-root", type=Path, default=ROOT / "frontend" / "dist-electron")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)

    result = verify_payload(args.backend_root, args.electron_compile_root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"Release payload: {result['status']} files={result['summary']['backend_file_count']} "
        f"issues={result['summary']['issue_count']} report={args.report}"
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
