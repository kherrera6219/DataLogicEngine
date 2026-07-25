from scripts import verify_release_governance


def test_release_governance_reports_missing_required_token(tmp_path, monkeypatch):
    ci_workflow = tmp_path / "ci.yml"
    deploy_workflow = tmp_path / "deploy.yml"
    release_readiness = tmp_path / "RELEASE_READINESS_RECORD.md"

    ci_workflow.write_text(
        "lint:\nbackend-test:\nfrontend-build:\nwindows-packaging-smoke:\n"
        "Run deterministic startup precheck gate\n"
        "Validate docs references\n"
        "Validate SQLite/Postgres schema parity\n",
        encoding="utf-8",
    )
    deploy_workflow.write_text(
        "Run deterministic startup precheck gate\n"
        "Validate docs references\n"
        "Validate SQLite/Postgres schema parity\n"
        "Verify installer artifact integrity\n"
        "Production health check\n",
        encoding="utf-8",
    )
    release_readiness.write_text(
        "## Current decision\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(verify_release_governance, "CI_WORKFLOW", ci_workflow)
    monkeypatch.setattr(verify_release_governance, "DEPLOY_WORKFLOW", deploy_workflow)
    monkeypatch.setattr(
        verify_release_governance,
        "RELEASE_READINESS_RECORD",
        release_readiness,
    )

    findings = verify_release_governance.run_checks()

    assert any(
        item.level == "ERROR" and "governance:" in item.message for item in findings
    )
    assert any(
        item.level == "ERROR" and "## Gate summary" in item.message for item in findings
    )


def test_release_governance_passes_when_all_required_tokens_exist(
    tmp_path, monkeypatch
):
    ci_workflow = tmp_path / "ci.yml"
    deploy_workflow = tmp_path / "deploy.yml"
    release_readiness = tmp_path / "RELEASE_READINESS_RECORD.md"

    ci_workflow.write_text(
        "\n".join(verify_release_governance.REQUIRED_CI_TOKENS), encoding="utf-8"
    )
    deploy_workflow.write_text(
        "\n".join(verify_release_governance.REQUIRED_DEPLOY_TOKENS),
        encoding="utf-8",
    )
    release_readiness.write_text(
        "\n".join(verify_release_governance.REQUIRED_RELEASE_READINESS_TOKENS),
        encoding="utf-8",
    )

    monkeypatch.setattr(verify_release_governance, "CI_WORKFLOW", ci_workflow)
    monkeypatch.setattr(verify_release_governance, "DEPLOY_WORKFLOW", deploy_workflow)
    monkeypatch.setattr(
        verify_release_governance,
        "RELEASE_READINESS_RECORD",
        release_readiness,
    )

    findings = verify_release_governance.run_checks()

    assert not any(item.level == "ERROR" for item in findings)
