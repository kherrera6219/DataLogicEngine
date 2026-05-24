import subprocess
import sys

import scripts.deploy as deploy


def test_run_database_migrations_uses_flask_migrate(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="upgraded", stderr="")

    monkeypatch.setattr(deploy.subprocess, "run", fake_run)
    monkeypatch.delenv("FLASK_APP", raising=False)

    assert deploy.run_database_migrations() is True
    command, kwargs = calls[0]
    assert command == [sys.executable, "-m", "flask", "db", "upgrade"]
    assert kwargs["check"] is True
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["env"]["FLASK_APP"] == "app.py"


def test_run_database_migrations_fails_on_command_error(monkeypatch):
    def fake_run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, output="bad", stderr="failed")

    monkeypatch.setattr(deploy.subprocess, "run", fake_run)

    assert deploy.run_database_migrations() is False


def test_collect_static_files_copies_build_tree_without_shell(tmp_path, monkeypatch):
    frontend_build = tmp_path / "frontend" / "build"
    asset_dir = frontend_build / "assets"
    asset_dir.mkdir(parents=True)
    (frontend_build / "index.html").write_text("<html></html>", encoding="utf-8")
    (asset_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("collect_static_files must not call subprocess.run")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(deploy.subprocess, "run", fail_if_called)

    assert deploy.collect_static_files() is True
    assert (tmp_path / "static" / "index.html").read_text(encoding="utf-8") == "<html></html>"
    assert (tmp_path / "static" / "assets" / "app.js").read_text(encoding="utf-8") == "console.log('ok')"


def test_collect_static_files_returns_false_when_build_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert deploy.collect_static_files() is False
