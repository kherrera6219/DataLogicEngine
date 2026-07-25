#!/usr/bin/env python3
"""Verify release-governance alignment across workflows and release docs."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
DEPLOY_WORKFLOW = ROOT / ".github" / "workflows" / "deploy.yml"
RELEASE_READINESS_RECORD = ROOT / "docs" / "RELEASE_READINESS_RECORD.md"

REQUIRED_CI_TOKENS = (
    "lint:",
    "backend-test:",
    "frontend-build:",
    "windows-packaging-smoke:",
    "governance:",
    "Run deterministic startup precheck gate",
    "Validate docs references",
    "Validate SQLite/Postgres schema parity",
)

REQUIRED_DEPLOY_TOKENS = (
    "Run deterministic startup precheck gate",
    "Validate docs references",
    "Validate SQLite/Postgres schema parity",
    "Verify installer artifact integrity",
    "Production health check",
)

REQUIRED_RELEASE_READINESS_TOKENS = (
    "## Current decision",
    "**Production/public release: NO-GO.**",
    "## Candidate identity",
    "## Gate summary",
    "## Finding policy",
    "Release requires zero open P0/P1 findings",
    "## Required final evidence bundle",
    "## GO authorization template",
    "`production_authorized=false`",
    "installed and independent acceptance of the ADR-0010 object-store selection",
)


@dataclass
class Finding:
    level: str
    scope: str
    message: str


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _check_required_tokens(
    path: Path, scope: str, tokens: tuple[str, ...]
) -> list[Finding]:
    findings: list[Finding] = []
    text = _read_text(path)
    if text is None:
        return [
            Finding("ERROR", scope, f"Missing required file: {_display_path(path)}")
        ]

    findings.append(Finding("OK", scope, f"Found {_display_path(path)}"))
    for token in tokens:
        if token in text:
            findings.append(Finding("OK", scope, f"Contains required token: {token}"))
        else:
            findings.append(Finding("ERROR", scope, f"Missing required token: {token}"))
    return findings


def run_checks() -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_required_tokens(CI_WORKFLOW, "ci", REQUIRED_CI_TOKENS))
    findings.extend(
        _check_required_tokens(DEPLOY_WORKFLOW, "deploy", REQUIRED_DEPLOY_TOKENS)
    )
    findings.extend(
        _check_required_tokens(
            RELEASE_READINESS_RECORD,
            "release-readiness",
            REQUIRED_RELEASE_READINESS_TOKENS,
        )
    )
    return findings


def _write_report(path: Path, findings: list[Finding]) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "findings": [asdict(item) for item in findings],
        "summary": {
            "ok": sum(1 for item in findings if item.level == "OK"),
            "error": sum(1 for item in findings if item.level == "ERROR"),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-report",
        type=Path,
        default=Path("reports/release_governance_report.json"),
        help="Output report path (JSON).",
    )
    args = parser.parse_args(argv)

    findings = run_checks()
    for finding in findings:
        print(f"[{finding.level}] [{finding.scope}] {finding.message}")

    _write_report(args.json_report, findings)
    print(f"Report: {args.json_report}")

    has_error = any(item.level == "ERROR" for item in findings)
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
