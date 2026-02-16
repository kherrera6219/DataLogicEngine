#!/usr/bin/env python3
"""
Verify Windows installer artifact integrity checksums.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


@dataclass
class InstallerIssue:
    severity: str
    artifact: str
    check: str
    detail: str


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_hash_file(hash_file: Path) -> str:
    line = hash_file.read_text(encoding="ascii").strip()
    if not line:
        raise ValueError("Checksum file is empty.")
    parts = line.split()
    expected_hash = parts[0].strip().lower()
    if len(expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in expected_hash):
        raise ValueError("Checksum file does not contain a valid SHA-256 digest.")
    return expected_hash


def verify_installers(repo_root: Path, require_artifacts: bool) -> tuple[List[InstallerIssue], dict]:
    issues: List[InstallerIssue] = []
    installers = sorted(
        artifact
        for artifact in repo_root.glob("DataLogicEngine Setup *.exe")
        if artifact.is_file() and not artifact.name.endswith(".exe.blockmap")
    )

    if not installers and require_artifacts:
        issues.append(
            InstallerIssue(
                severity="error",
                artifact="(none)",
                check="artifact_presence",
                detail="No installer artifacts were found in repository root.",
            )
        )
        return issues, {"installers": []}

    report_rows = []
    for installer in installers:
        row = {
            "artifact": installer.name,
            "sha256": None,
            "checksum_file": f"{installer.name}.sha256",
            "blockmap_present": (repo_root / f"{installer.name}.blockmap").exists(),
            "valid": True,
        }
        checksum_file = repo_root / f"{installer.name}.sha256"
        if not checksum_file.exists():
            issues.append(
                InstallerIssue(
                    severity="error",
                    artifact=installer.name,
                    check="checksum_presence",
                    detail=f"Missing checksum file: {checksum_file.name}",
                )
            )
            row["valid"] = False
            report_rows.append(row)
            continue

        try:
            expected_hash = _read_hash_file(checksum_file)
        except ValueError as exc:
            issues.append(
                InstallerIssue(
                    severity="error",
                    artifact=installer.name,
                    check="checksum_format",
                    detail=str(exc),
                )
            )
            row["valid"] = False
            report_rows.append(row)
            continue

        actual_hash = _sha256_file(installer)
        row["sha256"] = actual_hash
        if actual_hash != expected_hash:
            issues.append(
                InstallerIssue(
                    severity="error",
                    artifact=installer.name,
                    check="checksum_match",
                    detail="Installer checksum does not match its .sha256 manifest.",
                )
            )
            row["valid"] = False

        if not row["blockmap_present"]:
            issues.append(
                InstallerIssue(
                    severity="warning",
                    artifact=installer.name,
                    check="blockmap_presence",
                    detail="Installer blockmap artifact is missing.",
                )
            )
        report_rows.append(row)

    return issues, {"installers": report_rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify installer artifact checksums.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root directory containing installer artifacts.",
    )
    parser.add_argument(
        "--report",
        default="reports/installer_integrity_report.json",
        help="JSON report output path.",
    )
    parser.add_argument(
        "--require-artifacts",
        action="store_true",
        help="Fail when no installer artifacts are present.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    issues, report_body = verify_installers(repo_root=repo_root, require_artifacts=args.require_artifacts)
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]

    payload = {
        "status": "pass" if not errors else "fail",
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "total_issues": len(issues),
        },
        "results": report_body,
        "issues": [asdict(issue) for issue in issues],
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(
        f"[installer-integrity] status={payload['status']} "
        f"errors={len(errors)} warnings={len(warnings)} report={report_path}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
