import json

from scripts import verify_release_ownership


def test_structured_but_unapproved_register_is_not_release_ready(tmp_path):
    phase = tmp_path / "reports" / "production-readiness" / "2026" / "phase-00"
    phase.mkdir(parents=True)
    responsibilities = [
        {
            "discipline": name,
            "responsible": "Owner",
            "approver": "Owner",
            "approval_status": "release-blocked",
        }
        for name in verify_release_ownership.DISCIPLINES
    ]
    legal = [
        {
            "area": name,
            "authority": "Owner",
            "status": "pending",
            "release_blocking": name != "microsoft_store_declarations",
        }
        for name in verify_release_ownership.LEGAL_AREAS
    ]
    (phase / "responsibility-approval.json").write_text(
        json.dumps({"responsibilities": responsibilities}), encoding="utf-8"
    )
    (phase / "legal-distribution-authority.json").write_text(
        json.dumps({"register": legal}), encoding="utf-8"
    )
    (phase / "windows-support-matrix.json").write_text(
        json.dumps({"supported": ["x"], "unsupported": ["x"], "qualification_required": ["x"]}),
        encoding="utf-8",
    )

    result = verify_release_ownership.collect_release_ownership(tmp_path)

    assert result["structure_passed"] is True
    assert result["release_ready"] is False
