from copy import deepcopy
from hashlib import sha256

import pytest

from backend.storage.semantic_family_verification import (
    SemanticFamilyVerificationError,
    verify_semantic_family,
)


def _fixture():
    source = "alpha beta gamma"
    spans = [("alpha beta", 0, 10), ("beta gamma", 6, 16)]
    common = {"user_id": "owner", "source_revision": "revision"}
    parent_hash = sha256(source.encode()).hexdigest()
    metadata = [
        {
            **common,
            "vector_parent_id": "parent",
            "vector_chunk_index": i,
            "vector_chunk_count": 2,
            "source_span_start": start,
            "source_span_end": end,
            "source_span_sha256": sha256(text.encode()).hexdigest(),
            "source_parent_sha256": parent_hash,
        }
        for i, (text, start, end) in enumerate(spans)
    ]
    return (
        source,
        spans,
        common,
        {
            "ids": ["parent", "parent:chunk:1"],
            "documents": [item[0] for item in spans],
            "metadatas": metadata,
            "embeddings": [[0.6, 0.8], [0.8, 0.6]],
        },
    )


class Collection:
    def __init__(self, result, inventory=None):
        self.result = result
        self.inventory = inventory if inventory is not None else result["ids"]

    def get(self, *, limit, include, where=None, offset=0):
        if where is None:
            assert include == []
            return {"ids": self.inventory[offset : offset + limit]}
        assert where == {"vector_parent_id": {"$eq": "parent"}}
        assert limit == 3
        assert "embeddings" in include
        return self.result


def test_complete_family_passes():
    source, spans, common, result = _fixture()
    assert (
        verify_semantic_family(
            Collection(result),
            parent_id="parent",
            source_text=source,
            spans=spans,
            expected_metadata=common,
            dimensions=2,
            expected_vectors=[[0.6, 0.8], [0.8, 0.6]],
        )
        == 2
    )


def test_orphaned_child_is_found_without_parent_metadata():
    source, spans, common, result = _fixture()
    collection = Collection(result, inventory=[*result["ids"], "parent:chunk:2"])
    with pytest.raises(SemanticFamilyVerificationError, match="membership_mismatch"):
        verify_semantic_family(
            collection,
            parent_id="parent",
            source_text=source,
            spans=spans,
            expected_metadata=common,
            dimensions=2,
            expected_vectors=[[0.6, 0.8], [0.8, 0.6]],
        )


def test_inventory_cap_is_fail_closed(monkeypatch):
    from backend.storage import semantic_family_verification as module

    source, spans, common, result = _fixture()
    monkeypatch.setattr(module, "_INVENTORY_LIMIT", 1)
    with pytest.raises(SemanticFamilyVerificationError, match="inventory_over_limit"):
        verify_semantic_family(
            Collection(result),
            parent_id="parent",
            source_text=source,
            spans=spans,
            expected_metadata=common,
            dimensions=2,
            expected_vectors=[[0.6, 0.8], [0.8, 0.6]],
        )


@pytest.mark.parametrize(
    "damage",
    ["missing", "extra", "text", "owner", "offset", "nan", "vector", "wrong_vector"],
)
def test_incomplete_or_tampered_family_fails_closed(damage):
    source, spans, common, result = _fixture()
    result = deepcopy(result)
    if damage == "missing":
        for values in result.values():
            values.pop()
    elif damage == "extra":
        for values in result.values():
            values.append(values[-1])
        result["ids"][-1] = "parent:chunk:2"
    elif damage == "text":
        result["documents"][0] = "changed"
    elif damage == "owner":
        result["metadatas"][0]["user_id"] = "other"
    elif damage == "offset":
        result["metadatas"][0]["source_span_start"] = 1
    elif damage == "nan":
        result["embeddings"][0][0] = float("nan")
    elif damage == "wrong_vector":
        result["embeddings"][0] = [0.8, 0.6]
    else:
        result["embeddings"][0] = None
    with pytest.raises(SemanticFamilyVerificationError):
        verify_semantic_family(
            Collection(result),
            parent_id="parent",
            source_text=source,
            spans=spans,
            expected_metadata=common,
            dimensions=2,
            expected_vectors=[[0.6, 0.8], [0.8, 0.6]],
        )
