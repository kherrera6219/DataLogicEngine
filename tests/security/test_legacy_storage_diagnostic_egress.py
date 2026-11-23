"""Legacy connection diagnostics cannot contact external storage services."""

import socket
from unittest.mock import MagicMock

import pytest

from backend.routes.storage_routes import (
    _test_neo4j,
    _test_object,
    _test_postgres,
    _test_redis,
    _test_vector,
)


@pytest.mark.parametrize("check", [_test_postgres, _test_redis, _test_neo4j])
@pytest.mark.parametrize(
    "host", ["outside.example", "192.0.2.1", "127.0.0.1@outside.example"]
)
def test_remote_database_diagnostic_denied_before_socket(monkeypatch, check, host):
    def fail_if_called(*_args, **_kwargs):
        pytest.fail("remote diagnostic created a socket")

    monkeypatch.setattr(socket, "socket", fail_if_called)
    result = check({"host": host})
    assert result["connected"] is False
    assert "blocked" in result["message"]


@pytest.mark.parametrize("check", [_test_postgres, _test_redis, _test_neo4j])
def test_local_database_diagnostic_uses_literal_loopback(monkeypatch, check):
    connection = MagicMock()
    connection.connect_ex.return_value = 0
    monkeypatch.setattr(socket, "socket", lambda *_args, **_kwargs: connection)
    result = check({"host": "localhost"})
    assert result["connected"] is True
    assert connection.connect_ex.call_args.args[0][0] == "127.0.0.1"
    connection.close.assert_called_once()


def test_external_vector_diagnostic_reports_policy_denial():
    result = _test_vector({"provider": "pinecone", "api_key": "test-key"})
    assert result["connected"] is False
    assert "blocked" in result["message"]


def test_external_object_diagnostic_reports_policy_denial():
    result = _test_object(
        {
            "provider": "s3",
            "endpoint_url": "https://outside.example",
            "access_key": "local-key",
            "secret_key": "local-secret",
        }
    )
    assert result["connected"] is False
    assert "blocked" in result["message"]
