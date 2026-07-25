from scripts.dev import run_precommit_checks


def test_precommit_python_lint_matches_ci_policy(monkeypatch):
    calls: list[tuple[list[str], str]] = []

    def capture(command: list[str], label: str) -> int:
        calls.append((command, label))
        return 0

    monkeypatch.setattr(run_precommit_checks, "_run", capture)

    assert run_precommit_checks.main([]) == 0
    assert calls[0] == (
        [
            run_precommit_checks.sys.executable,
            "-m",
            "ruff",
            "check",
            ".",
            "--select",
            "E9,F63,F7",
        ],
        "Python lint (ruff)",
    )
