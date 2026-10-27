from copy import deepcopy

import pytest

from backend.storage.semantic_index_preparation import (
    SemanticIndexPreparationError,
    prepare_semantic_index,
)


class MemoryCollection:
    def __init__(self, collection_id, records=(), revision=None):
        self.id = collection_id
        self.metadata = {"dle_embedding_revision": revision} if revision else {}
        self.records = {record["id"]: deepcopy(record) for record in records}
        self.vectors = {}

    def count(self):
        return len(self.records)

    def get(self, *, limit=None, offset=0, ids=None, include):
        if ids is not None:
            assert include == ["embeddings"]
            return {"ids": ids, "embeddings": [self.vectors[item_id] for item_id in ids]}
        assert include == ["documents", "metadatas"]
        items = sorted(self.records.values(), key=lambda item: item["id"])[offset : offset + limit]
        return {
            "ids": [item["id"] for item in items],
            "documents": [item["text"] for item in items],
            "metadatas": [deepcopy(item["metadata"]) for item in items],
        }

    def upsert(self, *, ids, documents, metadatas, embeddings):
        for item_id, text, metadata, vector in zip(ids, documents, metadatas, embeddings):
            assert vector == [0.6, 0.8]
            self.records[item_id] = {"id": item_id, "text": text, "metadata": deepcopy(metadata)}
            self.vectors[item_id] = list(vector)


def _sources():
    return [
        {"id": "a", "text": "first", "metadata": {"user_id": "1", "session_id": "a"}},
        {"id": "b", "text": "second", "metadata": {"user_id": "2", "session_id": "b"}},
    ]


def test_prepare_is_verified_resumable_and_preserves_source_and_permissions():
    source = MemoryCollection("old", _sources())
    target = MemoryCollection("new", [_sources()[0]], revision="semantic-v1")
    receipt = prepare_semantic_index(source, target, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1", batch_size=1)
    assert receipt["status"] == "prepared_not_activated"
    assert receipt["record_count"] == 2
    assert source.records == target.records
    assert prepare_semantic_index(source, target, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1")["source_digest"] == receipt["source_digest"]


def test_unexpected_target_records_are_not_deleted_or_accepted():
    source = MemoryCollection("old", _sources())
    extra = {"id": "extra", "text": "retained", "metadata": {}}
    target = MemoryCollection("new", [extra], revision="semantic-v1")
    with pytest.raises(SemanticIndexPreparationError, match="target_verification_failed"):
        prepare_semantic_index(source, target, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1")
    assert target.records["extra"] == extra


def test_changed_source_or_wrong_target_blocks_activation():
    source = MemoryCollection("old", _sources())
    target = MemoryCollection("new", revision="semantic-v1")
    original = target.upsert

    def change_source(**kwargs):
        original(**kwargs)
        source.records["a"]["text"] = "changed during preparation"

    target.upsert = change_source
    with pytest.raises(SemanticIndexPreparationError, match="source_changed"):
        prepare_semantic_index(source, target, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1")
    with pytest.raises(SemanticIndexPreparationError, match="target_not_distinct"):
        prepare_semantic_index(source, source, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1")
    with pytest.raises(SemanticIndexPreparationError, match="revision_mismatch"):
        prepare_semantic_index(source, MemoryCollection("other"), lambda _text: [0.6, 0.8], embedding_revision="semantic-v1")


def test_interrupted_preparation_can_resume_without_changing_source():
    source = MemoryCollection("old", _sources())
    target = MemoryCollection("new", revision="semantic-v1")

    def interrupted(text):
        if text == "second":
            raise RuntimeError("embedding unavailable")
        return [0.6, 0.8]

    with pytest.raises(RuntimeError, match="embedding unavailable"):
        prepare_semantic_index(source, target, interrupted, embedding_revision="semantic-v1", batch_size=1)
    assert source.records == {record["id"]: record for record in _sources()}
    assert list(target.records) == ["a"]
    receipt = prepare_semantic_index(source, target, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1", batch_size=1)
    assert receipt["status"] == "prepared_not_activated"
    assert source.records == target.records


def test_record_limit_refuses_preparation_before_writing():
    source = MemoryCollection("old", _sources())
    target = MemoryCollection("new", revision="semantic-v1")
    with pytest.raises(SemanticIndexPreparationError, match="over_limit"):
        prepare_semantic_index(source, target, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1", max_records=1)
    assert target.records == {}


def test_incorrect_stored_vectors_fail_verification():
    source = MemoryCollection("old", _sources())
    target = MemoryCollection("new", revision="semantic-v1")
    original = target.upsert

    def corrupt_vector(**kwargs):
        original(**kwargs)
        target.vectors["a"] = [0.0, 1.0]

    target.upsert = corrupt_vector
    with pytest.raises(SemanticIndexPreparationError, match="vector_mismatch"):
        prepare_semantic_index(source, target, lambda _text: [0.6, 0.8], embedding_revision="semantic-v1")
