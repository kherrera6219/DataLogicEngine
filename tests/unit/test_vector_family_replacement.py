from types import SimpleNamespace

import pytest

from backend.storage.vector_store import ChromaDBBackend, VectorStore


class Collection:
    def __init__(self):
        self.rows = {"old":{"vector_parent_id":"parent"}, "keep":{"vector_parent_id":"other"}}
        self.drop_write = False

    def delete(self, *, where):
        parent = where["vector_parent_id"]["$eq"]
        self.rows = {key:meta for key,meta in self.rows.items() if meta["vector_parent_id"] != parent}

    def upsert(self, *, ids, documents, embeddings, metadatas):
        if not self.drop_write:
            self.rows.update(zip(ids,metadatas))

    def get(self, *, ids=None, where=None, limit=None, include):
        if ids is not None:
            return {"ids":[key for key in ids if key in self.rows]}
        parent = where["vector_parent_id"]["$eq"]
        return {"ids":[key for key,meta in self.rows.items() if meta["vector_parent_id"] == parent][:limit]}


def _backend(monkeypatch):
    collection = Collection()
    backend = ChromaDBBackend()
    backend._client = object()
    monkeypatch.setattr("backend.storage.vector_store.safe_get_collection", lambda *a,**k:collection)
    monkeypatch.setattr(backend, "_get_collection", lambda name:collection)
    return backend, collection


def test_replacement_and_deletion_preserve_other_families(monkeypatch):
    backend, collection = _backend(monkeypatch)
    result = backend.replace_embeddings("knowledge_nodes", "parent", ids=["new"],
        texts=["synthetic"], embeddings=[[1.0,0.0]], metadata=[{"vector_parent_id":"parent"}])
    assert result == ["new"]
    assert set(collection.rows) == {"keep","new"}
    backend.delete_parent_embeddings("knowledge_nodes", "parent")
    assert set(collection.rows) == {"keep"}


def test_unacknowledged_replacement_and_unsupported_backend_fail_explicitly(monkeypatch):
    backend, collection = _backend(monkeypatch)
    collection.drop_write = True
    with pytest.raises(RuntimeError, match="vector_family_write_unverified"):
        backend.replace_embeddings("knowledge_nodes", "parent", ids=["new"],
            texts=["synthetic"], embeddings=[[1.0,0.0]], metadata=[{"vector_parent_id":"parent"}])
    with pytest.raises(RuntimeError, match="unsupported"):
        VectorStore(backend=SimpleNamespace()).delete_parent_embeddings("knowledge_nodes","parent")


def test_metadata_mismatch_is_rejected_before_deleting_existing_vectors(monkeypatch):
    backend, collection = _backend(monkeypatch)
    with pytest.raises(RuntimeError, match="vector_family_input_invalid"):
        backend.replace_embeddings("knowledge_nodes", "parent", ids=["new"],
            texts=["synthetic"], embeddings=[[1.0,0.0]], metadata=[{"vector_parent_id":"other"}])
    assert set(collection.rows) == {"old","keep"}
