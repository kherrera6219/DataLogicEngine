import json
from types import SimpleNamespace

from backend.services.rag_service import RAGService
from backend.storage.graph_store import GraphStore
from backend.truth_engine.truth_memory.cache import TruthCache
from backend.truth_engine.truth_memory.manager import TruthMemoryManager


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.expiry = {}

    def ping(self):
        return True

    def hset(self, key, mapping):
        self.data.setdefault(key, {}).update(mapping)
        return 1

    def hget(self, key, field):
        return self.data.get(key, {}).get(field)

    def expire(self, key, ttl):
        self.expiry[key] = ttl
        return True

    def delete(self, key):
        existed = key in self.data
        self.data.pop(key, None)
        return 1 if existed else 0

    def scan_iter(self, pattern="*"):
        if pattern == "*":
            yield from list(self.data.keys())
            return
        prefix = pattern.rstrip("*")
        for key in list(self.data.keys()):
            if key.startswith(prefix):
                yield key


def test_truth_cache_redis_persists_across_instances():
    redis_client = FakeRedis()
    first = TruthCache(backend="redis", redis_client=redis_client)
    second = TruthCache(backend="redis", redis_client=redis_client)

    assert first.cache_persona("regulatory", {"name": "Regulatory Expert"})
    assert second.get_persona("regulatory") == {"name": "Regulatory Expert"}
    assert redis_client.hget("persona:regulatory", "value") is not None


def test_truth_cache_redis_clear_is_limited_to_truth_cache_prefixes():
    redis_client = FakeRedis()
    cache = TruthCache(backend="redis", redis_client=redis_client)

    cache.cache_persona("regulatory", {"name": "Regulatory Expert"})
    redis_client.hset("unrelated:local-data", mapping={"value": "keep"})

    cache.clear()

    assert redis_client.hget("persona:regulatory", "value") is None
    assert redis_client.hget("unrelated:local-data", "value") == "keep"
    assert cache.get_stats()["size"] == 0


def test_truth_memory_manager_selects_redis_when_enabled(monkeypatch):
    monkeypatch.setenv("USE_REDIS", "true")
    monkeypatch.setattr(
        "backend.truth_engine.truth_memory.cache.TruthCache._build_redis_client",
        staticmethod(lambda: FakeRedis()),
    )

    manager = TruthMemoryManager(db_session=None)

    assert manager.cache.backend == "redis"


def test_graph_store_subgraph_cache_uses_redis(monkeypatch):
    redis_client = FakeRedis()
    monkeypatch.setenv("USE_REDIS", "true")
    monkeypatch.setattr(GraphStore, "_redis_client", classmethod(lambda cls: redis_client))
    store = GraphStore()
    calls = {"count": 0}

    def fake_run_query(query, parameters):
        calls["count"] += 1
        return [{"props": {"uid": parameters["uid"]}}]

    store.run_query = fake_run_query

    first = store.get_subgraph("PL01")
    second = store.get_subgraph("PL01")

    assert first == second
    assert calls["count"] == 1
    assert any(key.startswith("subgraph:") for key in redis_client.data)


def test_rag_embedding_cache_uses_redis(monkeypatch):
    redis_client = FakeRedis()
    monkeypatch.setenv("USE_REDIS", "true")
    monkeypatch.setattr(RAGService, "_redis_embedding_client", classmethod(lambda cls: redis_client))

    key = RAGService._embedding_cache_key("hello")
    RAGService._set_cached_embedding(key, [0.1, 0.2])

    service = RAGService()
    assert service._default_embedding("hello") == [0.1, 0.2]
    assert redis_client.hget(key, "value") == json.dumps([0.1, 0.2])


def test_database_status_shape_supports_redis_ping_type():
    status = SimpleNamespace(status="managed", chroma_collections={}, redis_ping_ms=None)
    assert status.redis_ping_ms is None
