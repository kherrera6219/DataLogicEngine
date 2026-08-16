"""Phase 2 deterministic runtime lifecycle contracts."""

from pathlib import Path
import os
import subprocess
import sys

import pytest

from app import create_app
from backend.runtime import RuntimePhase, RuntimeOwnershipError
from backend.runtime.ownership import InstallationIdentity


def _runtime_app(runtime_root: Path, **overrides):
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(runtime_root / 'app.sqlite').as_posix()}",
        "DLE_RUNTIME_ROOT": str(runtime_root),
        "DLE_REQUIRED_SERVICES": "",
        "DLE_INITIALIZE_SCHEMA": False,
        "DLE_INITIALIZE_STORES": False,
        "DLE_START_MANAGED_SERVICES": False,
        "DLE_START_BACKGROUND_WORKERS": False,
        "DLE_CONFIGURE_LOGGING": False,
    }
    config.update(overrides)
    return create_app("testing", config)


@pytest.mark.parametrize("phase", [phase.value for phase in RuntimePhase if phase in {
    RuntimePhase.CONFIGURATION,
    RuntimePhase.PATHS_AND_ACL,
    RuntimePhase.RUNTIME_LOCK,
    RuntimePhase.SERVICE_SUPERVISOR,
    RuntimePhase.SERVICE_VERIFICATION,
    RuntimePhase.MIGRATIONS,
    RuntimePhase.STORES,
    RuntimePhase.ROUTES_AND_WORKERS,
    RuntimePhase.READINESS,
}])
def test_every_startup_phase_has_deterministic_failure_injection(tmp_path, phase):
    app = _runtime_app(tmp_path / phase, DLE_FAIL_STARTUP_PHASE=phase)
    runtime = app.extensions["dle_runtime"]

    with pytest.raises(RuntimeError, match=f"startup_failed:{phase}"):
        runtime.start()

    assert runtime.phase == RuntimePhase.FAILED
    assert runtime.failure_reason == f"startup_failed:{phase}"
    assert not runtime.ownership.lock or not runtime.ownership.lock.acquired


def test_repeated_start_status_stop_cycles_release_all_ownership(tmp_path):
    app = _runtime_app(tmp_path / "repeated")
    runtime = app.extensions["dle_runtime"]

    for _ in range(3):
        runtime.start()
        assert runtime.phase == RuntimePhase.READY
        assert runtime.readiness()[1] == 200
        assert runtime.ownership.lock and runtime.ownership.lock.acquired
        runtime.shutdown()
        assert runtime.phase == RuntimePhase.STOPPED
        assert runtime.started_threads == ()
        assert runtime.bound_ports == ()
        assert runtime.ownership.lock and not runtime.ownership.lock.acquired


@pytest.mark.parametrize("contending_role", ["renderer", "backend", "installer", "updater"])
def test_second_runtime_owner_is_rejected_then_can_recover(tmp_path, contending_role):
    root = tmp_path / "exclusive"
    first = _runtime_app(root)
    second = _runtime_app(root, DLE_RUNTIME_ROLE=contending_role)
    first_runtime = first.extensions["dle_runtime"]
    second_runtime = second.extensions["dle_runtime"]

    first_runtime.start()
    with pytest.raises(RuntimeError, match="startup_failed:runtime_lock"):
        second_runtime.start()
    assert first_runtime.phase == RuntimePhase.READY
    assert second_runtime.phase == RuntimePhase.FAILED

    first_runtime.shutdown()
    second_runtime.start()
    assert second_runtime.phase == RuntimePhase.READY
    second_runtime.shutdown()


def test_lifecycle_operation_drains_new_mutations(tmp_path):
    app = _runtime_app(tmp_path / "operation")
    runtime = app.extensions["dle_runtime"]
    runtime.start()

    with runtime.exclusive_operation("backup"):
        assert runtime.phase == RuntimePhase.DRAINING
        assert runtime.active_operation == "backup"
        assert runtime.admits_request("POST", "/api/v1/gateway/chat") is False
        with pytest.raises(RuntimeError, match="lifecycle_operation_busy:backup"):
            with runtime.exclusive_operation("update"):
                pass

    assert runtime.phase == RuntimePhase.READY
    assert runtime.active_operation is None
    runtime.shutdown()


def test_power_session_and_time_events_follow_runtime_contract(tmp_path):
    app = _runtime_app(tmp_path / "events")
    runtime = app.extensions["dle_runtime"]
    runtime.start()

    runtime.handle_system_event("time_changed")
    assert runtime.phase == RuntimePhase.READY
    runtime.handle_system_event("suspend")
    assert runtime.phase == RuntimePhase.DRAINING
    runtime.handle_system_event("resume")
    assert runtime.phase == RuntimePhase.READY
    runtime.handle_system_event("hibernate")
    assert runtime.phase == RuntimePhase.DRAINING
    runtime.handle_system_event("resume")
    assert runtime.phase == RuntimePhase.READY
    runtime.handle_system_event("logoff")
    assert runtime.phase == RuntimePhase.STOPPED
    assert runtime.system_events == [
        "time_changed",
        "suspend",
        "resume",
        "hibernate",
        "resume",
        "logoff",
    ]


@pytest.mark.parametrize("event", ["shutdown", "forced_termination"])
def test_terminal_windows_events_force_bounded_cleanup(tmp_path, event):
    app = _runtime_app(tmp_path / event, DLE_DRAIN_TIMEOUT_SECONDS=0.01)
    runtime = app.extensions["dle_runtime"]
    runtime.start()
    runtime.metrics.begin_request()

    runtime.handle_system_event(event)

    assert runtime.phase == RuntimePhase.STOPPED
    assert runtime.shutdown_forced is True
    assert runtime.ownership.lock and not runtime.ownership.lock.acquired


def test_corrupt_or_cross_user_installation_identity_fails_closed(tmp_path, monkeypatch):
    identity_path = tmp_path / "installation.json"
    identity_path.write_text("not-json", encoding="utf-8")
    with pytest.raises(RuntimeOwnershipError, match="installation_identity_invalid"):
        InstallationIdentity.load_or_create(identity_path, version="0.1.1")

    identity_path.unlink()
    identity = InstallationIdentity.load_or_create(identity_path, version="0.1.1")
    monkeypatch.setattr("backend.runtime.ownership.getpass.getuser", lambda: f"{identity.owner}-other")
    with pytest.raises(RuntimeOwnershipError, match="installation_identity_owner_mismatch"):
        InstallationIdentity.load_or_create(identity_path, version="0.1.1")


def test_low_or_read_only_runtime_path_fails_before_readiness(tmp_path, monkeypatch):
    app = _runtime_app(tmp_path / "disk-failure")
    runtime = app.extensions["dle_runtime"]

    def fail_identity(*_args, **_kwargs):
        raise OSError("simulated disk full")

    monkeypatch.setattr(InstallationIdentity, "persist", fail_identity)
    with pytest.raises(RuntimeError, match="startup_failed:runtime_lock"):
        runtime.start()
    assert runtime.phase == RuntimePhase.FAILED


def test_process_crash_releases_runtime_lock_for_stale_owner_recovery(tmp_path):
    root = tmp_path / "crash-recovery"
    script = (
        "import os; "
        "from pathlib import Path; "
        "from backend.runtime.ownership import InstallationIdentity, RuntimeLock; "
        f"root=Path({str(root)!r}); "
        "identity=InstallationIdentity.load_or_create(root/'installation.json', version='0.1.1'); "
        "lock=RuntimeLock(root/'runtime.lock', identity); lock.acquire(); "
        "os._exit(0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        env=os.environ.copy(),
        check=False,
        timeout=30,
    )
    assert result.returncode == 0

    identity = InstallationIdentity.load_or_create(root / "installation.json", version="0.1.1")
    from backend.runtime.ownership import RuntimeLock

    recovered_lock = RuntimeLock(root / "runtime.lock", identity)
    recovered_lock.acquire()
    assert recovered_lock.acquired is True
    recovered_lock.release()


def test_production_profile_refuses_sqlite_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SESSION_SECRET", "phase2-production-session-secret")
    monkeypatch.setenv("CORS_ORIGINS", "app://-")
    monkeypatch.setenv("ALLOW_PLAINTEXT_PROD_SECRETS", "true")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'fallback.sqlite').as_posix()}")

    with pytest.raises(RuntimeError, match="SQLite fallback is disabled"):
        create_app(
            config_overrides={
                "DLE_RUNTIME_ROOT": str(tmp_path / "production"),
                "DLE_CONFIGURE_LOGGING": False,
                "DLE_DATA_PLANE_DRIVER": "legacy",
            }
        )


def test_runtime_rejects_installation_version_mismatch(tmp_path):
    root = tmp_path / "version-mismatch"
    InstallationIdentity.load_or_create(root / "installation.json", version="0.1.0")
    app = _runtime_app(root, APP_VERSION="0.1.1")

    with pytest.raises(RuntimeError, match="startup_failed:runtime_lock"):
        app.extensions["dle_runtime"].start()
    assert app.extensions["dle_runtime"].failure_reason == "startup_failed:runtime_lock"
    assert app.extensions["dle_runtime"].failure_detail == "installation_version_mismatch"


def test_runtime_advances_supported_candidate_version_only_after_migration(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "supported-candidate-upgrade"
    installation_path = root / "installation.json"
    InstallationIdentity.load_or_create(installation_path, version="4.3.0")
    migration_calls = []

    def migration_passed(app, runtime):
        migration_calls.append((app.config["APP_VERSION"], runtime.runtime_root))
        return {"status": "ready"}

    monkeypatch.setattr(
        "backend.storage.runtime_migrations.run_managed_data_plane_migrations",
        migration_passed,
    )
    app = _runtime_app(
        root,
        APP_VERSION="4.4.0",
        DLE_DATA_PLANE_DRIVER="podman",
    )
    runtime = app.extensions["dle_runtime"]

    runtime.start()

    assert migration_calls == [("4.4.0", root)]
    assert InstallationIdentity.load(installation_path).version == "4.4.0"
    assert runtime.ownership.identity is not None
    assert runtime.ownership.identity.version == "4.4.0"
    runtime.shutdown()


def test_required_service_failure_stops_before_verification_and_migrations(tmp_path):
    app = _runtime_app(
        tmp_path / "required-service",
        DLE_REQUIRED_SERVICES="postgresql",
        DLE_START_MANAGED_SERVICES=True,
    )
    runtime = app.extensions["dle_runtime"]

    with pytest.raises(RuntimeError, match="startup_failed:service_supervisor"):
        runtime.start()

    assert runtime.phase == RuntimePhase.FAILED
    assert runtime.failure_detail == (
        "required_service_start_failed:postgresql:service_not_installed"
    )


@pytest.mark.parametrize(
    ("profile", "should_block"),
    [("qualification", False), ("production", True)],
)
def test_at_rest_gate_blocks_only_production_authorized_profile(
    tmp_path,
    monkeypatch,
    profile,
    should_block,
):
    app = _runtime_app(tmp_path / profile)
    app.config.update(
        TESTING=False,
        DLE_PRODUCTION_MODE=True,
        DLE_DATA_PLANE_PROFILE=profile,
    )
    runtime = app.extensions["dle_runtime"]

    monkeypatch.setattr(
        "backend.security.windows_acl.ensure_restricted_user_acl",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        "backend.security.windows_acl.verify_restricted_user_acl",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        "backend.storage.data_at_rest.build_at_rest_report",
        lambda *_args, **_kwargs: {"production_ready": False},
    )

    callback = runtime._callbacks[RuntimePhase.PATHS_AND_ACL][0]
    if should_block:
        with pytest.raises(RuntimeError, match="at_rest_protection_not_ready"):
            callback(runtime)
    else:
        callback(runtime)
        assert app.extensions["dle_at_rest_report"] == {"production_ready": False}
