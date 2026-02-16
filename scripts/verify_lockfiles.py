#!/usr/bin/env python3
"""Secure dependency lockfile governance checks."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UV_LOCK = ROOT / "uv.lock"
NPM_LOCK = ROOT / "frontend" / "package-lock.json"


@dataclass
class Finding:
    level: str
    message: str


def _check_uv_lock() -> list[Finding]:
    findings: list[Finding] = []
    if not UV_LOCK.exists():
        return [Finding("ERROR", "Missing Python lockfile: uv.lock")]

    text = UV_LOCK.read_text(encoding="utf-8")
    if "[[package]]" not in text:
        findings.append(Finding("ERROR", "uv.lock appears malformed (missing [[package]] entries)."))
    else:
        findings.append(Finding("OK", "uv.lock contains package entries."))

    if "http://" in text:
        findings.append(Finding("ERROR", "uv.lock contains insecure http:// sources."))
    else:
        findings.append(Finding("OK", "uv.lock contains no insecure http:// sources."))

    return findings


def _check_npm_lock() -> list[Finding]:
    findings: list[Finding] = []
    if not NPM_LOCK.exists():
        return [Finding("ERROR", "Missing frontend lockfile: frontend/package-lock.json")]

    try:
        payload = json.loads(NPM_LOCK.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [Finding("ERROR", f"Unable to parse package-lock.json: {exc}")]

    lock_version = int(payload.get("lockfileVersion", 0))
    if lock_version < 3:
        findings.append(Finding("ERROR", f"package-lock.json lockfileVersion must be >= 3 (found {lock_version})."))
    else:
        findings.append(Finding("OK", f"package-lock.json lockfileVersion is {lock_version}."))

    serialized = json.dumps(payload)
    insecure_url_matches = re.findall(r"http://[^\"']+", serialized)
    if insecure_url_matches:
        findings.append(
            Finding(
                "ERROR",
                f"package-lock.json contains insecure http:// dependency URLs ({len(insecure_url_matches)} match(es)).",
            )
        )
    else:
        findings.append(Finding("OK", "package-lock.json contains no insecure http:// dependency URLs."))

    return findings


def _write_report(path: Path, findings: list[Finding]) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
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
        "--json-report",
        type=Path,
        default=Path("reports/lockfile_governance_report.json"),
        help="Output report path (JSON).",
    )
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    findings.extend(_check_uv_lock())
    findings.extend(_check_npm_lock())

    for finding in findings:
        print(f"[{finding.level}] {finding.message}")

    _write_report(args.json_report, findings=findings)
    print(f"Report: {args.json_report}")

    has_error = any(finding.level == "ERROR" for finding in findings)
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
