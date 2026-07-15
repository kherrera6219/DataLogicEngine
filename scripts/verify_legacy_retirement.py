#!/usr/bin/env python3
"""Verify retired installer and stale release paths cannot enter production builds."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RetirementFinding:
    level: str
    check: str
    detail: str


def inspect_retirement(root: Path) -> list[RetirementFinding]:
    findings: list[RetirementFinding] = []
    policy_path = root / "config" / "legacy-retirement.json"
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [RetirementFinding("ERROR", "policy", f"Invalid retirement policy: {exc}")]
    if policy.get("schema_version") != "dle.legacy-retirement.v1":
        findings.append(RetirementFinding("ERROR", "policy", "Unsupported policy schema."))
    else:
        findings.append(RetirementFinding("OK", "policy", "Retirement policy schema is valid."))

    builder = (root / "frontend" / "electron-builder.yml").read_text(encoding="utf-8")
    package = (root / "frontend" / "package.json").read_text(encoding="utf-8")
    release_workflow = (
        root / ".github" / "workflows" / "release-installer-signing.yml"
    ).read_text(encoding="utf-8")
    release_surfaces = f"{builder}\n{package}\n{release_workflow}"
    forbidden_tokens = {
        "scripts/windows bundle": "from: ../scripts/windows",
        "legacy WiX setup": "UKG_Setup.wxs",
        "latest installer alias": "DataLogicEngine Setup Latest.exe",
    }
    for check, token in forbidden_tokens.items():
        if token in release_surfaces:
            findings.append(
                RetirementFinding("ERROR", check, f"Forbidden release token remains reachable: {token}")
            )
        else:
            findings.append(RetirementFinding("OK", check, f"Release surfaces exclude {token}."))

    if 'artifactName: "DataLogicEngine Setup ${version}.${ext}"' in builder:
        findings.append(
            RetirementFinding("OK", "artifact authority", "Only the versioned NSIS artifact is configured.")
        )
    else:
        findings.append(
            RetirementFinding("ERROR", "artifact authority", "Versioned NSIS artifact authority is missing.")
        )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/production-readiness/2026/phase-14/legacy-retirement.json"),
    )
    args = parser.parse_args(argv)
    findings = inspect_retirement(args.repo_root.resolve())
    errors = [finding for finding in findings if finding.level == "ERROR"]
    payload = {
        "schema_version": "dle.legacy-retirement-evidence.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "fail" if errors else "pass",
        "findings": [asdict(finding) for finding in findings],
    }
    report = args.report if args.report.is_absolute() else args.repo_root / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for finding in findings:
        print(f"[{finding.level}] [{finding.check}] {finding.detail}")
    print(f"Report: {report}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
