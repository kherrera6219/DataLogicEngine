import json

from scripts.verify_release_trust_policy import inspect_policy


def _policy():
    return {
        "schema_version": "dle.release-trust-policy.v1",
        "signing": {
            "production_authorized": False,
            "expected_publisher_subjects": [],
            "sha256_file_digest_required": True,
            "sha256_timestamp_digest_required": True,
            "trusted_timestamp_required": True,
            "revocation_check_required": True,
        },
        "updates": {},
        "distribution": {
            "artifact": "pending_owner_and_legal_selection",
            "regions": [],
            "authority_approved": False,
        },
    }


def test_open_approvals_are_blocked_for_engineering_evidence(tmp_path):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy()), encoding="utf-8")

    findings = inspect_policy(policy_path)

    assert not any(finding.level == "ERROR" for finding in findings)
    assert sum(finding.level == "BLOCKED" for finding in findings) == 3


def test_release_requirement_turns_open_approval_into_error(tmp_path):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy()), encoding="utf-8")

    findings = inspect_policy(
        policy_path,
        require_signing=True,
        require_updates=True,
        require_distribution=True,
    )

    assert sum(finding.level == "ERROR" for finding in findings) == 3


def test_complete_policy_passes_release_requirements(tmp_path):
    policy = _policy()
    policy["signing"]["production_authorized"] = True
    policy["signing"]["expected_publisher_subjects"] = ["CN=Approved Publisher"]
    policy["updates"] = {
        "production_qualified": True,
        "signed_metadata_qualified": True,
        "publisher_verification_qualified": True,
        "downgrade_prevention_qualified": True,
        "replay_prevention_qualified": True,
        "interrupted_update_rollback_qualified": True,
        "staged_rollout_qualified": True,
        "offline_signed_update_qualified": True,
    }
    policy["distribution"] = {
        "artifact": "signed_offline_exe",
        "regions": ["US"],
        "authority_approved": True,
    }
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    findings = inspect_policy(
        policy_path,
        require_signing=True,
        require_updates=True,
        require_distribution=True,
    )

    assert not any(finding.level in {"ERROR", "BLOCKED"} for finding in findings)
