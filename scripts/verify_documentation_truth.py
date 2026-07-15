#!/usr/bin/env python3
"""Run and record the Phase 17 generated-contract and documentation truth gate."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "production-readiness" / "2026" / "phase-17"
DEFAULT_REPORT = PHASE_DIR / "documentation-truth-gate.json"


def _run(name: str, arguments: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "command": [sys.executable, *arguments],
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def verify(*, write_generated: bool = False) -> dict[str, Any]:
    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    checks = [
        _run(
            "live_route_manifest",
            [
                "scripts/verify_route_manifest.py",
                "--output",
                str(PHASE_DIR / "route-manifest.json"),
                "--fail-unclassified",
            ],
        ),
        _run(
            "product_version_parity",
            [
                "scripts/verify_product_versions.py",
                "--report",
                str(PHASE_DIR / "product-version-parity.json"),
            ],
        ),
        _run("openapi_compatibility", ["scripts/check_gateway_openapi_compatibility.py"]),
    ]
    generator = ["scripts/generate_documentation_contract_index.py"]
    if not write_generated:
        generator.append("--check")
    checks.append(_run("generated_contract_index", generator))
    checks.extend(
        [
            _run("documentation_authority", ["scripts/verify_doc_authority.py"]),
            _run("documentation_bom", ["scripts/verify_documentation_bom.py"]),
            _run("phase16_replacement", ["scripts/verify_document_replacement_closure.py"]),
            _run("phase17_history", ["scripts/consolidate_phase17_history.py"]),
            _run("requirements_traceability", ["scripts/verify_requirements_traceability.py"]),
            _run("documentation_references", ["scripts/verify_docs_references.py"]),
        ]
    )
    return {
        "schema_version": "dle.documentation-truth-gate.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "pass" if all(item["passed"] for item in checks) else "fail",
        "summary": {
            "check_count": len(checks),
            "pass_count": sum(item["passed"] for item in checks),
            "error_count": sum(not item["passed"] for item in checks),
        },
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-generated", action="store_true")
    args = parser.parse_args(argv)
    result = verify(write_generated=args.write_generated)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"Documentation truth gate: {result['status']} "
        f"checks={result['summary']['pass_count']}/{result['summary']['check_count']}"
    )
    for check in result["checks"]:
        print(f"[{'PASS' if check['passed'] else 'FAIL'}] {check['name']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
