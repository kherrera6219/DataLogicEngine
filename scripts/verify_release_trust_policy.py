#!/usr/bin/env python3
"""Validate release signing, update, and distribution authorization policy."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "release-trust-policy.json"
SCHEMA_VERSION = "dle.release-trust-policy.v1"
UPDATE_GATES = (
    "production_qualified",
    "signed_metadata_qualified",
    "publisher_verification_qualified",
    "downgrade_prevention_qualified",
    "replay_prevention_qualified",
    "interrupted_update_rollback_qualified",
    "staged_rollout_qualified",
    "offline_signed_update_qualified",
)


@dataclass(frozen=True)
class TrustFinding:
    level: str
    scope: str
    detail: str


def inspect_policy(
    policy_path: Path,
    *,
    require_signing: bool = False,
    require_updates: bool = False,
    require_distribution: bool = False,
) -> list[TrustFinding]:
    if not policy_path.is_file():
        return [TrustFinding("ERROR", "policy", f"Missing policy: {policy_path}")]
    try:
        policy: dict[str, Any] = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [TrustFinding("ERROR", "policy", f"Invalid policy JSON: {exc}")]

    findings: list[TrustFinding] = []
    if policy.get("schema_version") == SCHEMA_VERSION:
        findings.append(TrustFinding("OK", "policy", "Release trust schema is valid."))
    else:
        findings.append(TrustFinding("ERROR", "policy", "Release trust schema is invalid."))

    signing = policy.get("signing") if isinstance(policy.get("signing"), dict) else {}
    subjects = signing.get("expected_publisher_subjects")
    signing_ready = signing.get("production_authorized") is True and isinstance(subjects, list) and bool(subjects)
    findings.append(
        TrustFinding(
            "OK" if signing_ready else ("ERROR" if require_signing else "BLOCKED"),
            "signing",
            "Production publisher signing is authorized with an approved subject."
            if signing_ready
            else "Production publisher/signing authority is not approved.",
        )
    )
    for field in (
        "sha256_file_digest_required",
        "sha256_timestamp_digest_required",
        "trusted_timestamp_required",
        "revocation_check_required",
    ):
        if signing.get(field) is not True:
            findings.append(
                TrustFinding("ERROR", "signing", f"Required signing control is disabled: {field}.")
            )

    updates = policy.get("updates") if isinstance(policy.get("updates"), dict) else {}
    open_update_gates = [gate for gate in UPDATE_GATES if updates.get(gate) is not True]
    findings.append(
        TrustFinding(
            "OK" if not open_update_gates else ("ERROR" if require_updates else "BLOCKED"),
            "updates",
            "All signed-update qualification gates are approved."
            if not open_update_gates
            else f"Open signed-update gates: {', '.join(open_update_gates)}.",
        )
    )

    distribution = (
        policy.get("distribution") if isinstance(policy.get("distribution"), dict) else {}
    )
    distribution_ready = (
        distribution.get("authority_approved") is True
        and isinstance(distribution.get("regions"), list)
        and bool(distribution.get("regions"))
        and distribution.get("artifact") not in {None, "", "pending_owner_and_legal_selection"}
    )
    findings.append(
        TrustFinding(
            "OK" if distribution_ready else ("ERROR" if require_distribution else "BLOCKED"),
            "distribution",
            "Distribution artifact, regions, and authority are approved."
            if distribution_ready
            else "Distribution artifact, regions, or legal authority remain unapproved.",
        )
    )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--require-signing", action="store_true")
    parser.add_argument("--require-updates", action="store_true")
    parser.add_argument("--require-distribution", action="store_true")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/production-readiness/2026/phase-14/release-trust-policy.json"),
    )
    args = parser.parse_args(argv)

    findings = inspect_policy(
        args.policy,
        require_signing=args.require_signing,
        require_updates=args.require_updates,
        require_distribution=args.require_distribution,
    )
    for finding in findings:
        print(f"[{finding.level}] [{finding.scope}] {finding.detail}")
    payload = {
        "schema_version": "dle.release-trust-policy-evidence.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "policy": str(args.policy),
        "release_required": {
            "signing": args.require_signing,
            "updates": args.require_updates,
            "distribution": args.require_distribution,
        },
        "findings": [asdict(finding) for finding in findings],
        "status": "fail" if any(item.level == "ERROR" for item in findings) else "pass",
    }
    report = args.report if args.report.is_absolute() else ROOT / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {report}")
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
