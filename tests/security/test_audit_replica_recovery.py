"""Audit replica continuity under restarts, rotation and concurrent writers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from threading import Thread

import pytest

from backend.security.audit_logger import AuditLogger, AuditReplicaError


def _logger(tmp_path: Path) -> AuditLogger:
    return AuditLogger(
        {
            "log_dir": str(tmp_path / "ordinary"),
            "immutable_replica_dir": str(tmp_path / "replica"),
            "immutable_replica_enabled": True,
            "immutable_hmac_secret": "test-only-key",
        },
        auto_start=False,
    )


def test_restart_and_independent_writers_continue_chain(tmp_path):
    first = _logger(tmp_path)
    second = _logger(tmp_path)
    first._append_immutable_replica({"id": "first"})
    second._append_immutable_replica({"id": "second"})
    first._append_immutable_replica({"id": "third"})
    restarted = _logger(tmp_path)
    restarted._append_immutable_replica({"id": "fourth"})
    result = restarted.verify_immutable_replica_integrity()
    assert result["verified"] is True
    assert result["total_entries"] == 4


def test_new_daily_file_starts_its_own_valid_chain(tmp_path):
    logger = _logger(tmp_path)
    logger._append_immutable_replica({"id": "one"})
    old_path = Path(logger._immutable_log_file_path())
    logger.current_date = "20990101"
    logger._append_immutable_replica({"id": "two"})
    assert logger.verify_immutable_replica_integrity(str(old_path))["verified"] is True
    assert logger.verify_immutable_replica_integrity()["verified"] is True


def test_corrupt_chain_is_not_extended(tmp_path):
    logger = _logger(tmp_path)
    logger._append_immutable_replica({"id": "one"})
    path = Path(logger._immutable_log_file_path())
    entry = json.loads(path.read_text(encoding="utf-8"))
    entry["event"]["id"] = "tampered"
    path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(AuditReplicaError, match="integrity_failure"):
        logger._append_immutable_replica({"id": "two"})
    assert path.read_bytes() == before


def test_same_size_tampering_with_restored_mtime_is_detected(tmp_path):
    logger = _logger(tmp_path)
    logger._append_immutable_replica({"id": "one"})
    path = Path(logger._immutable_log_file_path())
    before = path.stat()
    original = path.read_bytes()
    changed = original.replace(b'"id": "one"', b'"id": "two"')
    assert changed != original and len(changed) == len(original)
    path.write_bytes(changed)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    with pytest.raises(AuditReplicaError, match="integrity_failure"):
        logger._append_immutable_replica({"id": "three"})
    assert path.read_bytes() == changed


def test_replica_sync_error_is_visible_to_the_caller(tmp_path, monkeypatch):
    logger = _logger(tmp_path)

    def fail_sync(_fd):
        raise OSError("test sync failure")

    monkeypatch.setattr(os, "fsync", fail_sync)
    with pytest.raises(AuditReplicaError, match="write_failed"):
        logger._append_immutable_replica({"id": "one"})


def test_incomplete_chain_record_is_not_extended(tmp_path):
    logger = _logger(tmp_path)
    path = Path(logger._immutable_log_file_path())
    path.write_text('{"event":', encoding="utf-8")
    with pytest.raises(AuditReplicaError, match="incomplete_record"):
        logger._append_immutable_replica({"id": "one"})
    assert path.read_text(encoding="utf-8") == '{"event":'


def test_threads_do_not_fork_chain(tmp_path):
    loggers = [_logger(tmp_path) for _ in range(4)]
    errors = []

    def write(index):
        try:
            for number in range(10):
                loggers[index]._append_immutable_replica({"id": f"{index}-{number}"})
        except (AuditReplicaError, OSError) as exc:
            errors.append(exc)

    threads = [Thread(target=write, args=(index,)) for index in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    assert not errors
    assert not any(thread.is_alive() for thread in threads)
    result = loggers[0].verify_immutable_replica_integrity()
    assert result["verified"] is True
    assert result["total_entries"] == 40


def test_processes_do_not_fork_chain(tmp_path):
    logger = _logger(tmp_path)
    script = (
        "import sys\n"
        "from backend.security.audit_logger import AuditLogger\n"
        "logger = AuditLogger({'log_dir': sys.argv[1], 'immutable_replica_dir': sys.argv[2], "
        "'immutable_replica_enabled': True, 'immutable_hmac_secret': 'test-only-key'}, auto_start=False)\n"
        "for i in range(6): logger._append_immutable_replica({'id': sys.argv[3] + '-' + str(i)})\n"
    )
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                script,
                str(tmp_path / "ordinary"),
                str(tmp_path / "replica"),
                str(index),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(3)
    ]
    try:
        for process in processes:
            _stdout, stderr = process.communicate(timeout=30)
            assert process.returncode == 0, stderr
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
    result = logger.verify_immutable_replica_integrity()
    assert result["verified"] is True
    assert result["total_entries"] == 18
