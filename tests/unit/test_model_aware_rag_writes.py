"""Long local-model items need complete, replaceable vector families."""

from hashlib import sha256
import re
from types import SimpleNamespace

import pytest

from backend.services.local_sentence_embedding import LocalSentenceEmbedding, model_manifest_sha256
from backend.services.rag_service import RAGService


class Tokenizer:
    def num_special_tokens_to_add(self, pair=False):
        return 2

    def __call__(self, text, *, add_special_tokens, truncation, return_offsets_mapping=False, verbose=True):
        spans = [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]
        return {"input_ids": list(range(len(spans)+(2 if add_special_tokens else 0))), "offset_mapping":spans}


class Store:
    def __init__(self):
        self.rows = {}
        self.acknowledge = True

    def replace_embeddings(self, collection, parent_id, *, ids, texts, embeddings, metadata):
        self.delete_parent_embeddings(collection, parent_id)
        for item_id, text, vector, meta in zip(ids, texts, embeddings, metadata):
            self.rows[(collection,item_id)] = (text,vector,meta)
        return ids if self.acknowledge else []

    def delete_parent_embeddings(self, collection, parent_id):
        self.rows = {key:value for key,value in self.rows.items()
                     if not (key[0] == collection and value[2]["vector_parent_id"] == parent_id)}


def _service(tmp_path):
    (tmp_path / "model.safetensors").write_bytes(b"weights")
    tokenizer = Tokenizer()
    def encode(text, **kwargs):
        assert len(tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"]) <= 10
        return [0.6,0.8]
    embed = LocalSentenceEmbedding(tmp_path, dimensions=2,
        expected_weights_sha256=sha256(b"weights").hexdigest(),
        expected_manifest_sha256=model_manifest_sha256(tmp_path),
        loader=lambda *a,**k:SimpleNamespace(max_seq_length=10, tokenizer=tokenizer, encode=encode))
    store = Store()
    return RAGService(vector_store=store, embedding_provider=embed), store


@pytest.mark.parametrize("kind", ["chat", "knowledge", "text"])
def test_local_items_preserve_all_text_and_replace_obsolete_chunks(tmp_path, kind):
    service, store = _service(tmp_path)
    def write(text):
        if kind == "chat":
            return service.store_chat_message("session", "parent", "user", text, user_id="owner")
        if kind == "knowledge":
            return service.ingest_knowledge_node("parent", text, "test", {"user_id":"owner"})
        return service.ingest_text("persona_profiles", "parent", text, {"user_id":"owner"})
    text = " ".join(f"unique{i}" for i in range(40))
    assert write(text) is True
    assert len(store.rows) > 1
    assert all(any(token in value[0] for value in store.rows.values()) for token in text.split())
    assert all(value[2]["user_id"] == "owner" for value in store.rows.values())
    assert all(value[2]["embedding_revision"] == service.embedding_revision for value in store.rows.values())
    assert service._embedding_provider.expected_manifest_sha256 in service.embedding_revision
    assert write("short replacement") is True
    assert len(store.rows) == 1
    assert next(iter(store.rows.values()))[0] == "short replacement"
    store.acknowledge = False
    assert write("unacknowledged") is False


def test_local_knowledge_deletion_removes_the_complete_family(tmp_path):
    service, store = _service(tmp_path)
    assert service.ingest_knowledge_node("parent", " ".join(f"term{i}" for i in range(40)), "test")
    assert service.ingest_knowledge_node("retained", "other source", "test")
    assert service.delete_knowledge_node("parent") is True
    assert len(store.rows) == 1
    assert next(iter(store.rows))[1] == "retained"


def test_generic_text_write_requires_actual_acknowledgment():
    service = RAGService(vector_store=SimpleNamespace(add_embeddings=lambda **kwargs: []))
    assert service.ingest_text("persona_profiles", "parent", "synthetic text") is False
