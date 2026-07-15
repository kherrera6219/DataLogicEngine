#!/usr/bin/env python3
"""Verify Phase 0 release disciplines and legal decisions have explicit owners."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "reports/production-readiness/2026/phase-00"
DISCIPLINES = {
    "product", "architecture", "application_security", "privacy", "data_integrity",
    "internal_services", "ai_quality", "api_sdk_compatibility",
    "accessibility_usability", "installer_signing", "documentation", "release", "support",
}
LEGAL_AREAS = {
    "product_name_and_branding", "eula_and_terms", "privacy_notice_and_consent",
    "openai_provider_terms", "google_provider_terms", "podman_and_bundled_services",
    "open_source_notices", "export_and_commercial_distribution",
    "microsoft_store_declarations", "code_signing_identity", "distribution_authority",
}


def collect_release_ownership(root: Path = ROOT) -> dict:
    phase = root / "reports/production-readiness/2026/phase-00"
    ownership = json.loads((phase / "responsibility-approval.json").read_text(encoding="utf-8"))
    legal = json.loads((phase / "legal-distribution-authority.json").read_text(encoding="utf-8"))
    windows = json.loads((phase / "windows-support-matrix.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    responsibilities = ownership.get("responsibilities", [])
    found_disciplines = {row.get("discipline") for row in responsibilities}
    for row in responsibilities:
        if not row.get("responsible") or not row.get("approver") or not row.get("approval_status"):
            errors.append(f"incomplete responsibility: {row.get('discipline')}")
    if DISCIPLINES - found_disciplines:
        errors.append(f"missing disciplines: {sorted(DISCIPLINES - found_disciplines)}")
    register = legal.get("register", [])
    found_areas = {row.get("area") for row in register}
    for row in register:
        if not row.get("authority") or not row.get("status") or "release_blocking" not in row:
            errors.append(f"incomplete legal authority: {row.get('area')}")
    if LEGAL_AREAS - found_areas:
        errors.append(f"missing legal areas: {sorted(LEGAL_AREAS - found_areas)}")
    for section in ("supported", "unsupported", "qualification_required"):
        if not windows.get(section):
            errors.append(f"Windows matrix missing {section}")
    blocked_approvals = sum(row.get("approval_status") == "release-blocked" for row in responsibilities)
    blocked_legal = sum(bool(row.get("release_blocking")) for row in register)
    return {
        "schema_version": "dle.release-ownership-evidence.v1",
        "ownership_rows": len(responsibilities),
        "legal_rows": len(register),
        "blocked_independent_approvals": blocked_approvals,
        "release_blocking_legal_actions": blocked_legal,
        "errors": errors,
        "structure_passed": not errors,
        "release_ready": not errors and blocked_approvals == 0 and blocked_legal == 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/production-readiness/2026/phase-14/distribution-authority.json"),
    )
    parser.add_argument("--require-release-ready", action="store_true")
    args = parser.parse_args(argv)
    result = collect_release_ownership(args.repo_root.resolve())
    report = args.report if args.report.is_absolute() else args.repo_root / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["structure_passed"]:
        return 1
    if args.require_release_ready and not result["release_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
