from types import SimpleNamespace

import pytest

import backend.storage.vector_store as vector_store_module
from backend.storage.vector_store import (
    ChromaDBBackend,
    PineconeBackend,
    SearchResult,
    VectorStore,
    get_vector_store,
)


class FakeChromaCollection:
    def __init__(self):
        self.add_calls = []
        self.delete_calls = []

    def add(self, **kwargs):
        self.add_calls.append(kwargs)

    def query(self, **_kwargs):
        return {
            "ids": [["a1"]],
            "distances": [[0.2]],
            "documents": [["hello"]],
            "metadatas": [[{"source": "unit"}]],
        }

    def delete(self, ids):
        self.delete_calls.append(ids)

    def count(self):
        return 4


class FakeChromaClient:
    def __init__(self, collection):
        self.collection = collection
        self.deleted = []

    def get_or_create_collection(self, name, **_kwargs):
        return self.collection

    def delete_collection(self, name):
        self.deleted.append(name)


class FakePineconeIndex:
    def __init__(self):
        self.upserts = []
        self.deletes = []

    def upsert(self, vectors):
        self.upserts.append(vectors)

    def query(self, **kwargs):
        return {
            "matches": [
                {"id": "docs_id1", "score": 0.88, "metadata": {"text": "doc1", "collection": "docs", "tag": "x"}}
            ]
        }

    def delete(self, **kwargs):
        self.deletes.append(kwargs)

    def describe_index_stats(self):
        return {"total_vector_count": 12}


def test_chromadb_backend_happy_path(tmp_path):
    backend = ChromaDBBackend(persist_directory=str(tmp_path / "chroma"))
    collection = FakeChromaCollection()
    backend._client = FakeChromaClient(collection)

    ids = backend.add_embeddings(
        "docs",
        ids=["id1"],
        texts=["hello"],
        embeddings=[[0.1, 0.2]],
        metadata=[{"source": "unit"}],
    )
    assert ids == ["id1"]

    results = backend.search("docs", [0.1, 0.2], k=1)
    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].id == "a1"
    assert pytest.approx(results[0].score, rel=1e-6) == 0.8

    assert backend.delete("docs", ["id1"]) is True
    stats = backend.get_collection_stats("docs")
    assert stats["count"] == 4
    assert stats["backend"] == "chromadb"
    assert backend.create_collection("docs") is True
    assert backend.delete_collection("docs") is True


def test_chromadb_backend_error_paths(tmp_path):
    backend = ChromaDBBackend(persist_directory=str(tmp_path / "chroma"))

    def _raise(*_args, **_kwargs):
        raise RuntimeError("boom")

    backend._get_collection = _raise
    assert backend.add_embeddings("docs", ["id1"], ["t"], [[0.1]]) == []
    assert backend.search("docs", [0.1]) == []
    assert backend.delete("docs", ["id1"]) is False
    stats = backend.get_collection_stats("docs")
    assert stats["count"] == 0
    assert "error" in stats

    class ErrorClient:
        def get_or_create_collection(self, *_args, **_kwargs):
            raise RuntimeError("boom")

        def delete_collection(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    backend._client = ErrorClient()
    assert backend.create_collection("docs") is False
    assert backend.delete_collection("docs") is False


def test_pinecone_backend_happy_path():
    backend = PineconeBackend(api_key="k", environment="us-east-1", index_name="idx")
    backend._index = FakePineconeIndex()

    ids = backend.add_embeddings(
        "docs",
        ids=["id1"],
        texts=["text1"],
        embeddings=[[0.1, 0.2]],
        metadata=[{"tenant": "acme"}],
    )
    assert ids == ["id1"]
    assert backend._index.upserts[0][0]["id"] == "docs_id1"

    results = backend.search("docs", [0.1, 0.2], k=1, filters={"tenant": "acme"})
    assert len(results) == 1
    assert results[0].id == "id1"
    assert results[0].metadata == {"tag": "x"}

    assert backend.delete("docs", ["id1"]) is True
    assert backend.get_collection_stats("docs")["total_count"] == 12
    assert backend.create_collection("docs") is True
    assert backend.delete_collection("docs") is True


def test_pinecone_backend_error_paths():
    backend = PineconeBackend(api_key="k", environment="us-east-1", index_name="idx")

    class ErrorIndex:
        def upsert(self, **_kwargs):
            raise RuntimeError("boom")

        def query(self, **_kwargs):
            raise RuntimeError("boom")

        def delete(self, **_kwargs):
            raise RuntimeError("boom")

        def describe_index_stats(self):
            raise RuntimeError("boom")

    backend._index = ErrorIndex()

    assert backend.add_embeddings("docs", ["id1"], ["t"], [[0.1]]) == []
    assert backend.search("docs", [0.1]) == []
    assert backend.delete("docs", ["id1"]) is False
    stats = backend.get_collection_stats("docs")
    assert stats["count"] == 0
    assert backend.delete_collection("docs") is False


def test_vector_store_backend_selection(monkeypatch):
    import backend.storage.connection_manager as connection_manager_module

    stale_external_config = SimpleNamespace(
        vector=SimpleNamespace(
            is_cloud=True,
            provider="pinecone",
            api_key="k",
            environment="us-east-1",
            local_path="./db/chroma",
        )
    )

    monkeypatch.setattr(connection_manager_module, "get_connection_manager", lambda: SimpleNamespace(config=stale_external_config))
    store = VectorStore()
    assert isinstance(store._backend, ChromaDBBackend)


def test_vector_store_proxy_methods():
    class BackendStub:
        def add_embeddings(self, *_args, **_kwargs):
            return ["ok"]

        def search(self, *_args, **_kwargs):
            return [SearchResult(id="1", score=0.9)]

        def delete(self, *_args, **_kwargs):
            return True

        def get_collection_stats(self, *_args, **_kwargs):
            return {"count": 1}

        def create_collection(self, *_args, **_kwargs):
            return True

        def delete_collection(self, *_args, **_kwargs):
            return True

    store = VectorStore(backend=BackendStub())
    assert store.add_embeddings("c", ["1"], ["t"], [[0.1]]) == ["ok"]
    assert store.search("c", [0.1])[0].id == "1"
    assert store.delete("c", ["1"]) is True
    assert store.get_collection_stats("c")["count"] == 1
    assert store.create_collection("c", 2) is True
    assert store.delete_collection("c") is True


def test_get_vector_store_singleton(monkeypatch):
    sentinel = object()
    vector_store_module._vector_store = None
    monkeypatch.setattr(vector_store_module, "VectorStore", lambda: sentinel)

    first = get_vector_store()
    second = get_vector_store()
    assert first is sentinel
    assert second is sentinel
