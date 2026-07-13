"""Phase 2 application-factory isolation contracts."""

from pathlib import Path
import threading

from app import create_app
from backend.storage import get_connection_manager, get_object_store, get_uskd_memory_graph


def _test_config(database_path: Path, runtime_root: Path, marker: str) -> dict:
    return {
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path.as_posix()}",
        "DLE_RUNTIME_ROOT": str(runtime_root),
        "DLE_INSTANCE_MARKER": marker,
        "DLE_START_RUNTIME": False,
        "DLE_INITIALIZE_STORES": False,
        "DLE_INITIALIZE_SCHEMA": False,
    }


def test_create_app_builds_two_isolated_instances(tmp_path):
    """Configuration, extension, metrics, and runtime state must not leak."""
    threads_before = {thread.ident for thread in threading.enumerate()}
    first = create_app(config_overrides=_test_config(
        tmp_path / "first.sqlite",
        tmp_path / "first-runtime",
        "first",
    ))
    second = create_app(config_overrides=_test_config(
        tmp_path / "second.sqlite",
        tmp_path / "second-runtime",
        "second",
    ))

    assert first is not second
    assert first.config["DLE_INSTANCE_MARKER"] == "first"
    assert second.config["DLE_INSTANCE_MARKER"] == "second"
    assert first.config["SQLALCHEMY_DATABASE_URI"] != second.config["SQLALCHEMY_DATABASE_URI"]

    first_runtime = first.extensions["dle_runtime"]
    second_runtime = second.extensions["dle_runtime"]
    assert first_runtime is not second_runtime
    assert first_runtime.runtime_root != second_runtime.runtime_root
    assert first_runtime.metrics is not second_runtime.metrics
    assert first_runtime.supervisor is not second_runtime.supervisor
    assert first.extensions["dle_socketio"] is not second.extensions["dle_socketio"]
    assert first_runtime.started_threads == ()
    assert second_runtime.started_threads == ()
    assert first_runtime.bound_ports == ()
    assert second_runtime.bound_ports == ()
    assert {thread.ident for thread in threading.enumerate()} == threads_before

    first_runtime.metrics.begin_request()
    first_runtime.metrics.record_request("GET", "/factory-test", 200, 1.0)
    assert first_runtime.metrics.total_requests == 1
    assert second_runtime.metrics.total_requests == 0

    with first.app_context():
        first_engine = first.extensions["sqlalchemy"].engine
        first_connections = get_connection_manager()
        first_objects = get_object_store()
        first_graph = get_uskd_memory_graph()
    with second.app_context():
        second_engine = second.extensions["sqlalchemy"].engine
        second_connections = get_connection_manager()
        second_objects = get_object_store()
        second_graph = get_uskd_memory_graph()
    assert first_engine is not second_engine
    assert first_connections is not second_connections
    assert first_objects is not second_objects
    assert first_graph is not second_graph
    assert first_connections.config.object_storage.local_path != second_connections.config.object_storage.local_path


def test_importing_app_module_does_not_construct_default_application(tmp_path):
    """The compatibility proxy must stay dormant until explicitly accessed."""
    import os
    import subprocess
    import sys

    runtime_root = tmp_path / "import-only"
    environment = {
        **os.environ,
        "DLE_RUNTIME_ROOT": str(runtime_root),
        "FLASK_ENV": "testing",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import app; assert app._default_app is None; print('import-safe')",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("import-safe")
    assert not runtime_root.exists()
