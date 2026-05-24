import json

from scripts import runtime_precheck, verify_lockfiles


def test_runtime_precheck_blocks_production_auto_create_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_precheck, "ROOT", tmp_path)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "true")
    monkeypatch.setenv("SESSION_SECRET", "prod-session-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example.com:5432/app")

    results = runtime_precheck.check_env_files(allow_env_from_process=True)

    assert any(
        item.level == "BLOCKER" and "AUTO_CREATE_SCHEMA=true" in item.message
        for item in results
    )


def test_runtime_precheck_resolves_flask_sqlite_instance_path(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_precheck, "ROOT", tmp_path)
    instance_dir = tmp_path / "instance"
    instance_dir.mkdir()
    (instance_dir / "ukg_database.db").write_bytes(b"sqlite")
    (tmp_path / ".env").write_text(
        "DATABASE_URL=sqlite:///ukg_database.db\nSESSION_SECRET=test-secret\n",
        encoding="utf-8",
    )

    results = runtime_precheck.check_env_files()

    assert any(
        item.level == "OK" and str(instance_dir / "ukg_database.db") in item.message
        for item in results
    )
    assert not any("Initialize local schema" in item.message for item in results)


def test_runtime_precheck_validates_pyproject_and_uv_lock_alignment(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_precheck, "ROOT", tmp_path)
    (tmp_path / "requirements.txt").write_text("Flask==3.1.2\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"datalogicengine\"\nversion = \"0.1.0\"\n",
        encoding="utf-8",
    )
    (tmp_path / "uv.lock").write_text(
        "version = 1\n\n[[package]]\nname = \"datalogicengine\"\nversion = \"0.1.0\"\nsource = { virtual = \".\" }\n",
        encoding="utf-8",
    )

    results = runtime_precheck.check_backend_dependencies()

    assert any("project.name=datalogicengine" in item.message for item in results)


def test_verify_lockfiles_fails_on_project_name_mismatch(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    uv_lock = tmp_path / "uv.lock"
    npm_lock = tmp_path / "package-lock.json"

    pyproject.write_text(
        "[project]\nname = \"datalogicengine\"\nversion = \"0.1.0\"\n",
        encoding="utf-8",
    )
    uv_lock.write_text(
        "version = 1\n\n[[package]]\nname = \"other-name\"\nversion = \"0.1.0\"\nsource = { virtual = \".\" }\n",
        encoding="utf-8",
    )
    npm_lock.write_text(json.dumps({"lockfileVersion": 3, "name": "frontend"}), encoding="utf-8")

    monkeypatch.setattr(verify_lockfiles, "PYPROJECT", pyproject)
    monkeypatch.setattr(verify_lockfiles, "UV_LOCK", uv_lock)
    monkeypatch.setattr(verify_lockfiles, "NPM_LOCK", npm_lock)

    findings = verify_lockfiles._check_uv_lock()

    assert any(
        finding.level == "ERROR" and "does not match pyproject.toml" in finding.message
        for finding in findings
    )
