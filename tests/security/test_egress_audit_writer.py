"""Strict metadata-only audit records; transport integration is separate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.security.audit_logger import AuditLogger, AuditReplicaError


def _logger(tmp_path: Path, *, enabled: bool = True) -> AuditLogger:
    return AuditLogger(
        {
            "log_dir": str(tmp_path / "ordinary"),
            "immutable_replica_dir": str(tmp_path / "replica"),
            "immutable_replica_enabled": enabled,
            "immutable_hmac_secret": "test-only-key",
        },
        auto_start=False,
    )


@pytest.mark.parametrize("decision", ["allow", "deny"])
def test_egress_event_contains_only_expected_metadata(tmp_path, decision):
    logger = _logger(tmp_path)
    event_id = logger.log_egress_event(
        destination_host="127.0.0.1",
        bytes_out=12,
        bytes_in=34,
        result=decision,
        request_id="request-123",
    )
    path = Path(logger._immutable_log_file_path())
    entries = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 1
    event = entries[0]["event"]
    assert event["id"] == event_id
    assert event["status"] == decision
    assert event["request_id"] == "request-123"
    assert event["details"] == {
        "destination_host": "127.0.0.1",
        "bytes_out": 12,
        "bytes_in": 34,
    }
    assert set(event) == {
        "id",
        "timestamp",
        "event_type",
        "status",
        "request_id",
        "details",
        "hash",
    }
    assert logger.verify_immutable_replica_integrity()["verified"] is True


def test_disabled_replica_is_an_explicit_failure(tmp_path):
    logger = _logger(tmp_path, enabled=False)
    with pytest.raises(AuditReplicaError, match="replica_disabled"):
        logger.log_egress_event(
            destination_host="127.0.0.1",
            bytes_out=0,
            bytes_in=0,
            result="deny",
            request_id="request-123",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("destination_host", "https://user:password@example.com/path"),
        ("request_id", "private prompt content"),
        ("bytes_out", -1),
        ("bytes_in", True),
        ("result", "unknown"),
        ("result", ["allow"]),
    ],
)
def test_invalid_egress_metadata_is_rejected_before_writing(tmp_path, field, value):
    logger = _logger(tmp_path)
    metadata = {
        "destination_host": "127.0.0.1",
        "bytes_out": 0,
        "bytes_in": 0,
        "result": "deny",
        "request_id": "request-123",
    }
    metadata[field] = value
    with pytest.raises(AuditReplicaError):
        logger.log_egress_event(**metadata)
    assert not Path(logger._immutable_log_file_path()).exists()


def test_replica_disabled_during_append_is_not_reported_as_success(
    tmp_path, monkeypatch
):
    logger = _logger(tmp_path)
    append = logger._append_immutable_replica

    def disable_before_append(event, *, required=False):
        logger.immutable_replica_enabled = False
        return append(event, required=required)

    monkeypatch.setattr(logger, "_append_immutable_replica", disable_before_append)
    with pytest.raises(AuditReplicaError, match="replica_disabled"):
        logger.log_egress_event(
            destination_host="127.0.0.1",
            bytes_out=0,
            bytes_in=0,
            result="deny",
            request_id="request-123",
        )
