"""Configured syslog destinations are restricted to local listeners."""

import logging
from unittest.mock import patch

import pytest

from backend.logging_config import _configure_root_handlers
from backend.security.audit_logger import AuditLogger
from core.security.egress_guard import EgressDenied


@pytest.mark.parametrize(
    "host", ["outside.example", "192.0.2.1", "127.0.0.1@outside.example"]
)
def test_application_syslog_rejects_nonlocal_destination_before_handler(
    monkeypatch, tmp_path, host
):
    monkeypatch.setenv("LOG_AGGREGATION_HOST", host)
    root = logging.getLogger()
    existing_handlers = list(root.handlers)
    with patch("backend.logging_config.logging.handlers.SysLogHandler") as handler:
        with pytest.raises(EgressDenied):
            _configure_root_handlers(
                log_level=logging.INFO,
                log_format="json",
                log_file=str(tmp_path / "app.log"),
            )
        handler.assert_not_called()
    assert root.handlers == existing_handlers


@pytest.mark.parametrize(
    "host", ["outside.example", "192.0.2.1", "127.0.0.1@outside.example"]
)
def test_audit_syslog_rejects_nonlocal_destination_before_handler(tmp_path, host):
    audit = AuditLogger({"log_dir": str(tmp_path)}, auto_start=False)
    with patch(
        "backend.security.audit_logger.logging.handlers.SysLogHandler"
    ) as handler:
        with pytest.raises(EgressDenied):
            audit.enable_syslog_forwarding(host)
        handler.assert_not_called()
    audit.stop_log_rotation()
