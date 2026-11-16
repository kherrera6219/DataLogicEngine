"""Crash diagnostics must not initialize external reporting."""

import sys
from unittest.mock import Mock

import pytest

from backend.observability.crash_reporting import (
    crash_reporting_state,
    initialize_crash_reporting,
)
from core.security.egress_guard import EgressDenied


def test_configured_external_crash_reporting_is_rejected(monkeypatch):
    sdk = Mock()
    monkeypatch.setitem(sys.modules, "sentry_sdk", sdk)
    with pytest.raises(EgressDenied, match="Disable DLE_EXTERNAL_TELEMETRY_ENABLED"):
        initialize_crash_reporting(
            enabled=True,
            dsn="https://public@outside.example/1",
            environment="test",
            release="test",
        )
    sdk.init.assert_not_called()
    assert crash_reporting_state()["enabled"] is False
