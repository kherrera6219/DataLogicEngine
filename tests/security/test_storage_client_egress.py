"""Redis and Neo4j client factories must reject remote destinations."""

from unittest.mock import MagicMock

import pytest
import redis
from flask import Flask

from backend.security.session_manager import SessionManager
from backend.services.rag_service import RAGService
from backend.storage import graph_store, runtime_endpoints
from backend.storage.graph_store import GraphStore
from backend.truth_engine.truth_link.bus import TruthLinkBus
from backend.truth_engine.truth_memory import cache as truth_cache
from core.security.egress_guard import EgressDenied, loopback_service_url


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "redis://user:p%40ss@localhost:6379/2",
            "redis://user:p%40ss@127.0.0.1:6379/2",
        ),
        ("redis://[::1]:6379/0", "redis://[::1]:6379/0"),
        ("bolt://127.0.0.1:7687", "bolt://127.0.0.1:7687"),
    ],
)
def test_local_service_url_preserves_authority_without_dns(url, expected):
    assert loopback_service_url(url, schemes=frozenset({"redis", "bolt"})) == expected


@pytest.mark.parametrize(
    "url",
    [
        "redis://outside.example:6379/0",
        "redis://127.0.0.1@outside.example:6379/0",
        "redis://192.0.2.1:6379/0",
        "redis://localhost:0/0",
        "neo4j://localhost:7687",
    ],
)
def test_remote_or_routing_urls_are_denied(url):
    with pytest.raises(EgressDenied):
        loopback_service_url(url, schemes=frozenset({"redis", "bolt"}))


@pytest.mark.parametrize(
    "client", ["session", "graph_cache", "embedding", "bus", "truth_cache"]
)
def test_redis_factories_reject_remote_url_before_driver(monkeypatch, client):
    def fail_if_called(*_args, **_kwargs):
        pytest.fail("remote Redis destination reached the driver")

    monkeypatch.setattr(redis, "from_url", fail_if_called)
    monkeypatch.setattr(redis.Redis, "from_url", fail_if_called)
    monkeypatch.setenv("USE_REDIS", "true")
    monkeypatch.setattr(
        runtime_endpoints, "runtime_redis_url", lambda: "redis://outside.example:6379/0"
    )
    monkeypatch.setattr(
        graph_store, "runtime_redis_url", lambda: "redis://outside.example:6379/0"
    )
    monkeypatch.setattr(
        truth_cache, "runtime_redis_url", lambda: "redis://outside.example:6379/0"
    )

    def connect():
        if client == "session":
            app = Flask(__name__)
            app.config["DLE_REDIS_URL"] = "redis://outside.example:6379/0"
            return SessionManager(app)
        if client == "graph_cache":
            return GraphStore._redis_client()
        if client == "embedding":
            return RAGService._redis_embedding_client()
        if client == "bus":
            return TruthLinkBus._create_redis_client(True)
        return truth_cache.TruthCache._build_redis_client()

    with pytest.raises(EgressDenied):
        connect()


def test_graph_cache_connects_using_normalized_loopback(monkeypatch):
    calls = []
    fake_client = MagicMock()
    fake_client.ping.return_value = True
    monkeypatch.setenv("USE_REDIS", "true")
    monkeypatch.setattr(
        graph_store, "runtime_redis_url", lambda: "redis://localhost:6379/0"
    )

    def connect(url, **_kwargs):
        calls.append(url)
        return fake_client

    monkeypatch.setattr(redis.Redis, "from_url", connect)
    assert GraphStore._redis_client() is fake_client
    assert calls == ["redis://127.0.0.1:6379/0"]


@pytest.mark.parametrize(
    "uri", ["bolt://outside.example:7687", "neo4j://127.0.0.1:7687"]
)
def test_graph_connection_rejects_remote_and_routing_urls(monkeypatch, uri):
    def fail_if_called(*_args, **_kwargs):
        pytest.fail("unapproved graph destination reached the driver")

    monkeypatch.setattr(
        graph_store, "runtime_neo4j_settings", lambda: (uri, "user", "secret")
    )
    monkeypatch.setattr(graph_store.GraphDatabase, "driver", fail_if_called)
    with pytest.raises(EgressDenied):
        GraphStore().connect()
