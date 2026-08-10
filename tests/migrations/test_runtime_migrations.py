"""Managed startup migration wiring and credential-lifetime tests."""

from __future__ import annotations

from flask import Flask, has_app_context
import pytest

from app import create_app
from backend.runtime import RuntimePhase
from backend.runtime.ownership import InstallationIdentity
from backend.storage import runtime_migrations


class Closeable:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_runtime_migration_resources_close_owned_clients():
    resources = runtime_migrations.RuntimeMigrationResources()
    first = resources.own(Closeable())
    second = resources.own(Closeable())

    resources.close()

    assert first.closed is True
    assert second.closed is True


def test_managed_migration_wrapper_removes_dedicated_credential(monkeypatch, tmp_path):
    app = Flask("managed-migration-wrapper")
    app.config["APP_VERSION"] = "0.1.1"
    runtime = type("Runtime", (), {"runtime_root": tmp_path})()

    class Coordinator:
        def run(self):
            assert has_app_context()
            app.config["DLE_MIGRATION_DATABASE_URL"] = "postgresql://migration-secret"
            return {"status": "ready"}

    monkeypatch.setattr(
        runtime_migrations,
        "build_managed_migration_coordinator",
        lambda *_args: Coordinator(),
    )
    monkeypatch.setattr(
        runtime_migrations,
        "synchronize_postgresql_sequences",
        lambda _engine: {},
    )

    result = runtime_migrations.run_managed_data_plane_migrations(app, runtime)

    assert result == {"status": "ready"}
    assert "DLE_MIGRATION_DATABASE_URL" not in app.config


def test_podman_startup_runs_migrations_before_stores(monkeypatch, tmp_path):
    observed = []
    monkeypatch.setattr(
        runtime_migrations,
        "run_managed_data_plane_migrations",
        lambda *_args: observed.append("migrations") or {"status": "ready"},
    )
    app = create_app(
        "testing",
        config_overrides={
            "DLE_RUNTIME_ROOT": str(tmp_path / "runtime"),
            "DLE_CONFIGURE_LOGGING": False,
            "DLE_START_MANAGED_SERVICES": False,
            "DLE_INITIALIZE_STORES": False,
            "DLE_START_BACKGROUND_WORKERS": False,
        },
    )
    app.config["DLE_DATA_PLANE_DRIVER"] = "podman"
    app.config["DLE_MANAGED_DATA_SERVICES"] = ()
    runtime = app.extensions["dle_runtime"]
    runtime.on_phase(
        RuntimePhase.STORES,
        lambda _runtime: observed.append("stores"),
    )

    runtime.start()
    try:
        assert observed[:2] == ["migrations", "stores"]
        assert app.extensions["dle_migration_ledger"] == {"status": "ready"}
    finally:
        runtime.shutdown()


def test_managed_migration_failure_blocks_later_startup_phases(monkeypatch, tmp_path):
    def fail(*_args):
        raise RuntimeError("migration_gate_failed")

    monkeypatch.setattr(runtime_migrations, "run_managed_data_plane_migrations", fail)
    app = create_app(
        "testing",
        config_overrides={
            "DLE_RUNTIME_ROOT": str(tmp_path / "runtime-failure"),
            "DLE_CONFIGURE_LOGGING": False,
            "DLE_START_MANAGED_SERVICES": False,
            "DLE_INITIALIZE_STORES": False,
            "DLE_START_BACKGROUND_WORKERS": False,
        },
    )
    app.config["DLE_DATA_PLANE_DRIVER"] = "podman"
    app.config["DLE_MANAGED_DATA_SERVICES"] = ()
    runtime = app.extensions["dle_runtime"]

    try:
        with pytest.raises(RuntimeError, match="startup_failed:migrations"):
            runtime.start()
        assert runtime.failure_reason == "startup_failed:migrations"
        assert runtime.failure_detail == "migration_gate_failed"
        assert "dle_migration_ledger" not in app.extensions
    finally:
        runtime.shutdown()


def test_supported_retained_installation_version_advances_only_after_migration(
    monkeypatch,
    tmp_path,
):
    runtime_root = tmp_path / "retained-runtime"
    identity_path = runtime_root / "installation.json"
    original = InstallationIdentity.load_or_create(identity_path, version="0.1.1")
    monkeypatch.setattr(
        runtime_migrations,
        "run_managed_data_plane_migrations",
        lambda *_args: {"status": "ready", "stores": {}},
    )
    app = create_app(
        "testing",
        config_overrides={
            "APP_VERSION": "0.1.2",
            "DLE_RUNTIME_ROOT": str(runtime_root),
            "DLE_CONFIGURE_LOGGING": False,
            "DLE_START_MANAGED_SERVICES": False,
            "DLE_INITIALIZE_STORES": False,
            "DLE_START_BACKGROUND_WORKERS": False,
        },
    )
    app.config["DLE_DATA_PLANE_DRIVER"] = "podman"
    app.config["DLE_MANAGED_DATA_SERVICES"] = ()
    runtime = app.extensions["dle_runtime"]

    runtime.start()
    try:
        upgraded = InstallationIdentity.load_or_create(
            identity_path,
            version="0.1.2",
        )
        assert upgraded.installation_id == original.installation_id
        assert upgraded.version == "0.1.2"
        assert runtime.ownership.identity.version == "0.1.2"
    finally:
        runtime.shutdown()
