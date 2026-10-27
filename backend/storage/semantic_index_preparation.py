"""Prepare a separate disposable-test semantic collection without activating data.

The caller must provide a quiescent disposable-test source and an explicitly
provisioned disposable-test target whose metadata pins the embedding revision. This utility never
changes which collection the app reads. Activation still requires coordinated
writes/deletes, full model qualification, and installed verification.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Callable


class SemanticIndexPreparationError(RuntimeError):
    """Separate index preparation failed and must not be activated."""


def _snapshot(
    collection: Any, *, batch_size: int, max_records: int
) -> list[dict[str, Any]]:
    count = collection.count()
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or not 0 <= count <= max_records
    ):
        raise SemanticIndexPreparationError(
            "semantic_source_count_invalid_or_over_limit"
        )
    records: list[dict[str, Any]] = []
    for offset in range(0, count, batch_size):
        page = collection.get(
            limit=min(batch_size, count - offset),
            offset=offset,
            include=["documents", "metadatas"],
        )
        ids = page.get("ids")
        texts = page.get("documents")
        metadata = page.get("metadatas")
        if (
            not isinstance(ids, list)
            or not isinstance(texts, list)
            or not isinstance(metadata, list)
        ):
            raise SemanticIndexPreparationError("semantic_source_page_invalid")
        if len(ids) != len(texts) or len(ids) != len(metadata):
            raise SemanticIndexPreparationError("semantic_source_columns_mismatch")
        for item_id, text, meta in zip(ids, texts, metadata):
            if (
                not isinstance(item_id, str)
                or not item_id
                or not isinstance(text, str)
                or not text.strip()
                or not isinstance(meta, dict)
            ):
                raise SemanticIndexPreparationError("semantic_source_record_invalid")
            records.append({"id": item_id, "text": text, "metadata": meta})
    if len(records) != count or len({item["id"] for item in records}) != count:
        raise SemanticIndexPreparationError("semantic_source_changed_or_duplicate")
    return sorted(records, key=lambda item: item["id"])


def _digest(records: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        records,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepare_semantic_index(
    source: Any,
    target: Any,
    embed: Callable[[str], list[float]],
    *,
    embedding_revision: str,
    batch_size: int = 100,
    max_records: int = 10_000,
) -> dict[str, Any]:
    """Copy into a distinct revision-pinned target and verify both snapshots.

    Idempotent upserts allow a partial attempt to resume. Unexpected target
    records, changed source data, and mismatched metadata all fail validation;
    no records are deleted or activated by this function.
    """
    if not 1 <= batch_size <= 500 or max_records < 1:
        raise SemanticIndexPreparationError("semantic_preparation_bounds_invalid")
    if not embedding_revision or source.id == target.id:
        raise SemanticIndexPreparationError("semantic_target_not_distinct")
    if (
        source.metadata.get("dle_disposable_test_data") is not True
        or target.metadata.get("dle_disposable_test_data") is not True
    ):
        raise SemanticIndexPreparationError("semantic_disposable_test_data_required")
    if target.metadata.get("dle_embedding_revision") != embedding_revision:
        raise SemanticIndexPreparationError("semantic_target_revision_mismatch")
    before = _snapshot(source, batch_size=batch_size, max_records=max_records)
    source_digest = _digest(before)
    expected_vectors: dict[str, list[float]] = {}
    for offset in range(0, len(before), batch_size):
        batch = before[offset : offset + batch_size]
        vectors = [embed(record["text"]) for record in batch]
        for record, vector in zip(batch, vectors):
            if not vector or not all(
                isinstance(value, (int, float)) and math.isfinite(value)
                for value in vector
            ):
                raise SemanticIndexPreparationError("semantic_embedding_invalid")
            expected_vectors[record["id"]] = [float(value) for value in vector]
        target.upsert(
            ids=[record["id"] for record in batch],
            documents=[record["text"] for record in batch],
            metadatas=[record["metadata"] for record in batch],
            embeddings=vectors,
        )
    after = _snapshot(source, batch_size=batch_size, max_records=max_records)
    if _digest(after) != source_digest:
        raise SemanticIndexPreparationError(
            "semantic_source_changed_during_preparation"
        )
    copied = _snapshot(target, batch_size=batch_size, max_records=max_records)
    if _digest(copied) != source_digest:
        raise SemanticIndexPreparationError("semantic_target_verification_failed")
    for offset in range(0, len(before), batch_size):
        batch_ids = [record["id"] for record in before[offset : offset + batch_size]]
        page = target.get(ids=batch_ids, include=["embeddings"])
        ids, vectors = page.get("ids"), page.get("embeddings")
        if (
            not isinstance(ids, list)
            or not isinstance(vectors, list)
            or len(ids) != len(vectors)
            or len(ids) != len(batch_ids)
            or set(ids) != set(batch_ids)
        ):
            raise SemanticIndexPreparationError("semantic_target_vectors_invalid")
        for item_id, vector in zip(ids, vectors):
            expected = expected_vectors[item_id]
            if (
                not isinstance(vector, list)
                or len(vector) != len(expected)
                or any(
                    not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or abs(value - wanted) > 1e-5
                    for value, wanted in zip(vector, expected)
                )
            ):
                raise SemanticIndexPreparationError("semantic_target_vector_mismatch")
    return {
        "status": "prepared_not_activated",
        "embedding_revision": embedding_revision,
        "source_collection_id": source.id,
        "target_collection_id": target.id,
        "record_count": len(before),
        "source_digest": source_digest,
    }
