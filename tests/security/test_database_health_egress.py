"""Local database health probes must not contact remote hosts."""

from unittest.mock import MagicMock

import neo4j
import psycopg2
import pytest
import redis

from backend.storage.connection_manager import ConnectionManager, StorageConfig
from core.security.egress_guard import EgressDenied, require_loopback_host


def _manager(service, host):
    manager = object.__new__(ConnectionManager)
    manager.config = StorageConfig()
    getattr(manager.config, service).host = host
    return manager


@pytest.mark.parametrize("service", ["postgres", "redis", "neo4j"])
@pytest.mark.parametrize(
    "host", ["outside.example", "192.0.2.1", "127.0.0.1@outside.example"]
)
def test_remote_database_health_targets_are_denied_before_driver(
    monkeypatch, service, host
):
    def fail_if_called(*_args, **_kwargs):
        pytest.fail("remote database health check reached a driver")

    monkeypatch.setattr(psycopg2, "connect", fail_if_called)
    monkeypatch.setattr(redis.Redis, "from_url", fail_if_called)
    monkeypatch.setattr(neo4j.GraphDatabase, "driver", fail_if_called)
    with pytest.raises(EgressDenied, match="loopback"):
        _manager(service, host).check_health(service)


@pytest.mark.parametrize(
    "host,expected",
    [
        ("localhost", "127.0.0.1"),
        ("LOCALHOST", "127.0.0.1"),
        ("127.0.0.1", "127.0.0.1"),
        ("::1", "::1"),
    ],
)
def test_local_hosts_are_normalized_without_dns(host, expected):
    assert require_loopback_host(host) == expected


@pytest.mark.parametrize("service", ["postgres", "redis", "neo4j"])
def test_localhost_is_replaced_with_literal_before_database_driver(
    monkeypatch, service
):
    calls = []

    def postgres_connect(url, **_kwargs):
        calls.append(url)
        connection = MagicMock()
        cursor = (
            connection.__enter__.return_value.cursor.return_value.__enter__.return_value
        )
        cursor.fetchone.return_value = ("datalogic", "postgres")
        return connection

    def redis_connect(url, **_kwargs):
        calls.append(url)
        client = MagicMock()
        client.ping.return_value = True
        return client

    def neo4j_connect(url, **_kwargs):
        calls.append(url)
        return MagicMock()

    monkeypatch.setattr(psycopg2, "connect", postgres_connect)
    monkeypatch.setattr(redis.Redis, "from_url", redis_connect)
    monkeypatch.setattr(neo4j.GraphDatabase, "driver", neo4j_connect)
    assert _manager(service, "localhost").check_health(service) is True
    assert len(calls) == 1
    assert "127.0.0.1" in calls[0]
    assert "localhost" not in calls[0]
