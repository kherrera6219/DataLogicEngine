#!/usr/bin/env python3
"""Require immutable commit pins for every external GitHub Actions dependency."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USES_PATTERN = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
COMMIT_PIN_PATTERN = re.compile(r"^[^/@\s]+/[^@\s]+@[0-9a-f]{40}$")
DOCKER_DIGEST_PATTERN = re.compile(r"^docker://[^@\s]+@sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class WorkflowPinFinding:
    level: str
    workflow: str
    reference: str
    detail: str


def inspect_workflows(repo_root: Path) -> list[WorkflowPinFinding]:
    workflows_dir = repo_root / ".github" / "workflows"
    findings: list[WorkflowPinFinding] = []
    workflow_paths = sorted((*workflows_dir.glob("*.yml"), *workflows_dir.glob("*.yaml")))
    if not workflow_paths:
        return [
            WorkflowPinFinding(
                "ERROR",
                ".github/workflows",
                "(none)",
                "No workflow files were found.",
            )
        ]

    for workflow_path in workflow_paths:
        display_path = workflow_path.relative_to(repo_root).as_posix()
        text = workflow_path.read_text(encoding="utf-8")
        for reference in USES_PATTERN.findall(text):
            if reference.startswith("./"):
                findings.append(
                    WorkflowPinFinding("OK", display_path, reference, "Local action reference.")
                )
            elif COMMIT_PIN_PATTERN.fullmatch(reference):
                findings.append(
                    WorkflowPinFinding(
                        "OK",
                        display_path,
                        reference,
                        "External action is pinned to a 40-character commit SHA.",
                    )
                )
            elif DOCKER_DIGEST_PATTERN.fullmatch(reference):
                findings.append(
                    WorkflowPinFinding(
                        "OK",
                        display_path,
                        reference,
                        "Container action is pinned to a SHA-256 digest.",
                    )
                )
            else:
                findings.append(
                    WorkflowPinFinding(
                        "ERROR",
                        display_path,
                        reference,
                        "External actions must use an immutable commit SHA or image digest.",
                    )
                )
    return findings


def _write_report(path: Path, findings: list[WorkflowPinFinding]) -> None:
    errors = [finding for finding in findings if finding.level == "ERROR"]
    payload = {
        "schema_version": "dle.workflow-pins.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "fail" if errors else "pass",
        "summary": {
            "references": len(findings),
            "errors": len(errors),
        },
        "findings": [asdict(finding) for finding in findings],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--json-report",
        type=Path,
        default=ROOT
        / "reports"
        / "production-readiness"
        / "2026"
        / "phase-14"
        / "workflow-pins.json",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    findings = inspect_workflows(repo_root)
    for finding in findings:
        print(
            f"[{finding.level}] {finding.workflow}: {finding.reference} - {finding.detail}"
        )
    _write_report(args.json_report, findings)
    errors = sum(finding.level == "ERROR" for finding in findings)
    print(
        f"[workflow-pins] status={'fail' if errors else 'pass'} "
        f"references={len(findings)} errors={errors} report={args.json_report}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
