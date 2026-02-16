#!/usr/bin/env python3
"""Validate local/CI environment parity expectations for DataLogicEngine."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PYTHON = (3, 11)
EXPECTED_NODE_MAJOR = 20


@dataclass
class Finding:
    level: str
    message: str


def _run_version_command(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    output = (completed.stdout or completed.stderr).strip()
    return output or None


def _resolve_bin(name: str) -> str | None:
    return shutil.which(name) or shutil.which(f"{name}.cmd")


def _extract_version_tuple(raw: str | None) -> tuple[int, ...] | None:
    if not raw:
        return None
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", raw)
    if not match:
        return None
    return tuple(int(part) for part in match.groups(default="0"))


def _check_python(strict: bool) -> list[Finding]:
    findings: list[Finding] = []
    current = sys.version_info[:3]
    if strict:
        if current[:2] != EXPECTED_PYTHON:
            findings.append(
                Finding(
                    "ERROR",
                    f"Python parity mismatch: expected {EXPECTED_PYTHON[0]}.{EXPECTED_PYTHON[1]}, got {current[0]}.{current[1]}",
                )
            )
        else:
            findings.append(Finding("OK", f"Python version matches CI parity: {current[0]}.{current[1]}"))
    else:
        if current[:2] < EXPECTED_PYTHON:
            findings.append(
                Finding(
                    "ERROR",
                    f"Python >= {EXPECTED_PYTHON[0]}.{EXPECTED_PYTHON[1]} required; found {current[0]}.{current[1]}",
                )
            )
        else:
            findings.append(Finding("OK", f"Python compatibility satisfied: {current[0]}.{current[1]}"))
    return findings


def _check_node(strict: bool) -> list[Finding]:
    findings: list[Finding] = []

    node_bin = _resolve_bin("node")
    npm_bin = _resolve_bin("npm")
    node_version = _extract_version_tuple(_run_version_command([node_bin, "--version"])) if node_bin else None
    npm_version = _extract_version_tuple(_run_version_command([npm_bin, "--version"])) if npm_bin else None

    if not node_version:
        findings.append(Finding("ERROR", "Node.js not found in PATH."))
    else:
        node_major = node_version[0]
        if strict and node_major != EXPECTED_NODE_MAJOR:
            findings.append(
                Finding(
                    "ERROR",
                    f"Node parity mismatch: expected major {EXPECTED_NODE_MAJOR}, got {node_major}",
                )
            )
        elif not strict and node_major < EXPECTED_NODE_MAJOR:
            findings.append(
                Finding(
                    "ERROR",
                    f"Node.js >= {EXPECTED_NODE_MAJOR} required; found major {node_major}",
                )
            )
        else:
            findings.append(Finding("OK", f"Node.js version accepted: {'.'.join(map(str, node_version[:3]))}"))

    if not npm_version:
        findings.append(Finding("ERROR", "npm not found in PATH."))
    else:
        findings.append(Finding("OK", f"npm detected: {'.'.join(map(str, npm_version[:3]))}"))

    return findings


def _check_required_files() -> list[Finding]:
    findings: list[Finding] = []
    required_paths = [
        ROOT / "requirements.txt",
        ROOT / "uv.lock",
        ROOT / "frontend" / "package-lock.json",
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / ".env.template",
    ]
    for path in required_paths:
        if path.exists():
            findings.append(Finding("OK", f"Found required parity file: {path.relative_to(ROOT)}"))
        else:
            findings.append(Finding("ERROR", f"Missing required parity file: {path.relative_to(ROOT)}"))
    return findings


def _check_ci_version_pins() -> list[Finding]:
    findings: list[Finding] = []
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    if not workflow.exists():
        findings.append(Finding("ERROR", "CI workflow missing: .github/workflows/ci.yml"))
        return findings

    text = workflow.read_text(encoding="utf-8")
    if "python-version: '3.11'" in text:
        findings.append(Finding("OK", "CI workflow pins Python 3.11"))
    else:
        findings.append(Finding("ERROR", "CI workflow is missing Python 3.11 pin"))

    if "node-version: '20'" in text:
        findings.append(Finding("OK", "CI workflow pins Node 20"))
    else:
        findings.append(Finding("ERROR", "CI workflow is missing Node 20 pin"))
    return findings


def _write_report(path: Path, strict: bool, findings: list[Finding]) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict": strict,
        "findings": [asdict(item) for item in findings],
        "summary": {
            "ok": sum(1 for item in findings if item.level == "OK"),
            "error": sum(1 for item in findings if item.level == "ERROR"),
            "warn": sum(1 for item in findings if item.level == "WARN"),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require exact parity with CI toolchain versions.",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=Path("reports/environment_parity_report.json"),
        help="Output report path (JSON).",
    )
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    findings.extend(_check_python(strict=args.strict))
    findings.extend(_check_node(strict=args.strict))
    findings.extend(_check_required_files())
    findings.extend(_check_ci_version_pins())

    for finding in findings:
        print(f"[{finding.level}] {finding.message}")

    _write_report(args.json_report, strict=args.strict, findings=findings)
    print(f"Report: {args.json_report}")

    has_error = any(finding.level == "ERROR" for finding in findings)
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
