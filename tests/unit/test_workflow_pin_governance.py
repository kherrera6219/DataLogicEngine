from scripts.verify_workflow_pins import inspect_workflows


def _write_workflow(tmp_path, body: str):
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(body, encoding="utf-8")
    return workflow


def test_mutable_action_tag_is_rejected(tmp_path):
    _write_workflow(tmp_path, "steps:\n  - uses: actions/checkout@v4\n")

    findings = inspect_workflows(tmp_path)

    assert any(finding.level == "ERROR" for finding in findings)


def test_commit_pinned_and_local_actions_pass(tmp_path):
    _write_workflow(
        tmp_path,
        "steps:\n"
        "  - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4\n"
        "  - uses: ./actions/validate\n",
    )

    findings = inspect_workflows(tmp_path)

    assert findings
    assert not any(finding.level == "ERROR" for finding in findings)


def test_container_action_requires_digest(tmp_path):
    _write_workflow(tmp_path, "steps:\n  - uses: docker://alpine:3.20\n")

    findings = inspect_workflows(tmp_path)

    assert any(finding.level == "ERROR" for finding in findings)
