import subprocess

from scripts import dev_doctor


def test_check_git_hooks_reports_configured_repo_path(tmp_path, monkeypatch):
    (tmp_path / ".githooks").mkdir()

    monkeypatch.setattr(dev_doctor.shutil, "which", lambda name: "C:/Program Files/Git/bin/git.exe")
    monkeypatch.setattr(
        dev_doctor.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            0,
            stdout=".githooks\n",
            stderr="",
        ),
    )

    findings = dev_doctor._check_git_hooks(root=tmp_path)

    assert any(
        item.level == "OK" and "Git hooks path configured as .githooks." in item.message
        for item in findings
    )


def test_check_git_hooks_recommends_bootstrap_when_unset(tmp_path, monkeypatch):
    (tmp_path / ".githooks").mkdir()

    monkeypatch.setattr(dev_doctor.shutil, "which", lambda name: "C:/Program Files/Git/bin/git.exe")
    monkeypatch.setattr(
        dev_doctor.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            0,
            stdout="",
            stderr="",
        ),
    )

    findings = dev_doctor._check_git_hooks(root=tmp_path)

    assert any(
        item.level == "ACTION" and "git config core.hooksPath .githooks" in item.message
        for item in findings
    )


def test_main_allows_action_items_without_strict_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dev_doctor,
        "_collect_runtime_findings",
        lambda **kwargs: [dev_doctor.Finding("runtime", "ACTION", "Set a provider key.")],
    )
    monkeypatch.setattr(
        dev_doctor,
        "_collect_parity_findings",
        lambda **kwargs: [dev_doctor.Finding("parity", "OK", "Parity aligned.")],
    )
    monkeypatch.setattr(
        dev_doctor,
        "_collect_lockfile_findings",
        lambda: [dev_doctor.Finding("lockfiles", "OK", "Lockfiles aligned.")],
    )
    monkeypatch.setattr(
        dev_doctor,
        "_check_git_hooks",
        lambda root=dev_doctor.ROOT: [dev_doctor.Finding("git", "OK", "Hooks configured.")],
    )

    report_path = tmp_path / "dev_doctor.json"
    exit_code = dev_doctor.main(["--json-report", str(report_path)])

    assert exit_code == 0
    assert report_path.exists()


def test_main_fails_on_action_items_in_strict_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(
        dev_doctor,
        "_collect_runtime_findings",
        lambda **kwargs: [dev_doctor.Finding("runtime", "ACTION", "Set a provider key.")],
    )
    monkeypatch.setattr(
        dev_doctor,
        "_collect_parity_findings",
        lambda **kwargs: [dev_doctor.Finding("parity", "OK", "Parity aligned.")],
    )
    monkeypatch.setattr(
        dev_doctor,
        "_collect_lockfile_findings",
        lambda: [dev_doctor.Finding("lockfiles", "OK", "Lockfiles aligned.")],
    )
    monkeypatch.setattr(
        dev_doctor,
        "_check_git_hooks",
        lambda root=dev_doctor.ROOT: [dev_doctor.Finding("git", "OK", "Hooks configured.")],
    )

    report_path = tmp_path / "dev_doctor_strict.json"
    exit_code = dev_doctor.main(["--strict", "--json-report", str(report_path)])

    assert exit_code == 1
    assert report_path.exists()
