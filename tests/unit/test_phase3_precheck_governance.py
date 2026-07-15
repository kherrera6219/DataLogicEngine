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


def test_runtime_precheck_blocks_production_sqlite_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_precheck, "ROOT", tmp_path)
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "false")
    monkeypatch.setenv("SESSION_SECRET", "prod-session-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///production.sqlite")

    results = runtime_precheck.check_env_files(allow_env_from_process=True)

    assert any(
        item.level == "BLOCKER" and "Supervised PostgreSQL is required" in item.message
        for item in results
    )


def test_runtime_precheck_resolves_flask_sqlite_instance_path(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_precheck, "ROOT", tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
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


def test_runtime_precheck_accepts_explicit_in_memory_sqlite_for_ci(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_precheck, "ROOT", tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SESSION_SECRET", "ci-session-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-key-for-ci")

    results = runtime_precheck.check_env_files(allow_env_from_process=True)

    assert any(
        item.level == "OK" and "in-memory database configured" in item.message
        for item in results
    )
    assert not any("Initialize local schema" in item.message for item in results)


def test_runtime_precheck_requires_hash_locked_release_dependencies(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_precheck, "ROOT", tmp_path)
    (tmp_path / "requirements.txt").write_text("Flask==3.1.2\n", encoding="utf-8")
    (tmp_path / "requirements.lock").write_text(
        "# source-sha256: placeholder\nFlask==3.1.2 --hash=sha256:" + "a" * 64 + "\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = \"datalogicengine\"\nversion = \"1.2.0\"\ndependencies = []\n",
        encoding="utf-8",
    )

    results = runtime_precheck.check_backend_dependencies()

    assert any("Hash-locked release dependencies" in item.message for item in results)
    assert any("project.name=datalogicengine" in item.message for item in results)


def test_verify_lockfiles_rejects_root_uv_lock_and_pyproject_runtime_dependencies(tmp_path, monkeypatch):
    pyproject = tmp_path / "pyproject.toml"
    uv_lock = tmp_path / "uv.lock"

    pyproject.write_text(
        "[project]\nname = \"datalogicengine\"\nversion = \"1.2.0\"\ndependencies = [\"Flask==3.1.3\"]\n",
        encoding="utf-8",
    )
    uv_lock.write_text("version = 1\n", encoding="utf-8")

    monkeypatch.setattr(verify_lockfiles, "PYPROJECT", pyproject)
    monkeypatch.setattr(verify_lockfiles, "UV_LOCK", uv_lock)

    findings = verify_lockfiles._check_uv_lock()

    assert any(finding.level == "ERROR" and "must be absent" in finding.message for finding in findings)
    assert any(finding.level == "ERROR" and "second root runtime" in finding.message for finding in findings)
