import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.storage.database_manager import DatabaseLifecycleManager


def _executable_name(base: str) -> str:
    return f"{base}.exe" if os.name == "nt" else base


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("stub", encoding="utf-8")


def _build_manager(tmp_path: Path) -> DatabaseLifecycleManager:
    manager = DatabaseLifecycleManager(base_dir=str(tmp_path))
    manager.pg_bin = str(tmp_path / "postgresql" / "bin")
    manager.pg_data = str(tmp_path / "postgresql" / "data")
    manager.redis_bin = str(tmp_path / "redis")
    manager.redis_data = str(tmp_path / "redis" / "data")
    manager.neo4j_bin = str(tmp_path / "neo4j" / "bin")
    manager.neo4j_data = str(tmp_path / "neo4j" / "data")
    return manager


def test_resolve_executable_rejects_paths_outside_base(tmp_path):
    manager = _build_manager(tmp_path)

    with pytest.raises(ValueError, match="outside managed database root"):
        manager._resolve_executable(str(tmp_path.parent / "bad.exe"))


def test_start_postgres_initializes_and_starts(tmp_path):
    manager = _build_manager(tmp_path)
    initdb = Path(manager.pg_bin) / _executable_name("initdb")
    postgres = Path(manager.pg_bin) / _executable_name("postgres")
    Path(manager.pg_data).mkdir(parents=True, exist_ok=True)
    _touch(initdb)
    _touch(postgres)

    fake_proc = Mock()
    with patch.object(manager, "is_port_in_use", return_value=False):
        with patch("backend.storage.database_manager.subprocess.run") as mock_run:
            with patch("backend.storage.database_manager.subprocess.Popen", return_value=fake_proc) as mock_popen:
                manager.start_postgres()

    assert mock_run.called
    assert mock_popen.called
    assert manager.pg_process is fake_proc


def test_start_postgres_skips_when_port_in_use(tmp_path):
    manager = _build_manager(tmp_path)

    with patch.object(manager, "is_port_in_use", return_value=True):
        with patch("backend.storage.database_manager.subprocess.Popen") as mock_popen:
            result = manager.start_postgres()

    mock_popen.assert_not_called()
    assert result is False
    assert manager.last_failure_reasons["postgresql"] == "foreign_listener_on_configured_port"


def test_start_redis_creates_data_dir_and_starts(tmp_path):
    manager = _build_manager(tmp_path)
    redis_server = Path(manager.redis_bin) / _executable_name("redis-server")
    _touch(redis_server)

    fake_proc = Mock()
    with patch.object(manager, "is_port_in_use", return_value=False):
        with patch("backend.storage.database_manager.subprocess.Popen", return_value=fake_proc) as mock_popen:
            manager.start_redis()

    assert Path(manager.redis_data).exists()
    assert mock_popen.called
    assert manager.redis_process is fake_proc


def test_start_neo4j_sets_neo4j_home(tmp_path):
    manager = _build_manager(tmp_path)
    neo4j_exe = Path(manager.neo4j_bin) / ("neo4j.bat" if os.name == "nt" else "neo4j")
    _touch(neo4j_exe)

    with patch.object(manager, "is_port_in_use", return_value=False):
        with patch("backend.storage.database_manager.subprocess.Popen", return_value=Mock()) as mock_popen:
            manager.start_neo4j()

    kwargs = mock_popen.call_args.kwargs
    assert kwargs["env"]["NEO4J_HOME"] == os.path.dirname(manager.neo4j_bin)


def test_start_all_dispatches_existing_database_dirs(tmp_path):
    manager = _build_manager(tmp_path)
    for db_name in ["postgresql", "redis", "neo4j"]:
        (Path(manager.base_dir) / db_name).mkdir(parents=True, exist_ok=True)

    with patch.object(manager, "start_postgres") as mock_pg:
        with patch.object(manager, "start_redis") as mock_redis:
            with patch.object(manager, "start_neo4j") as mock_neo4j:
                manager.start_all()

    mock_pg.assert_called_once()
    mock_redis.assert_called_once()
    mock_neo4j.assert_called_once()


def test_stop_all_terminates_and_kills_on_timeout(tmp_path):
    manager = _build_manager(tmp_path)

    timed_out_proc = Mock()
    timed_out_proc.wait.side_effect = [subprocess.TimeoutExpired(cmd="x", timeout=10), None]
    quick_proc = Mock()
    quick_proc.wait.return_value = None

    manager.pg_process = timed_out_proc
    manager.redis_process = quick_proc
    manager.neo4j_process = None

    manager.stop_all()

    timed_out_proc.terminate.assert_called_once()
    timed_out_proc.kill.assert_called_once()
    quick_proc.terminate.assert_called_once()
