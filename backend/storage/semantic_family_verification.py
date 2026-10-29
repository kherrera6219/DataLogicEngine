"""Verify one complete staged semantic family against authoritative source text.

This helper does not migrate data, activate a collection, or establish that a
source is authorized. The caller must hold the shared index lock, read source
content from the current authoritative SQL transaction, and check ownership,
deletion receipts and ingestion eligibility before and after staging.
"""

from __future__ import annotations

from hashlib import sha256
import math


class SemanticFamilyVerificationError(RuntimeError):
    """A staged family cannot safely be treated as complete."""


_INVENTORY_PAGE_SIZE = 500
_INVENTORY_LIMIT = 100_000


def verify_semantic_family(
    collection,
    *,
    parent_id,
    source_text,
    spans,
    expected_metadata,
    dimensions,
    expected_vectors,
):
    """Verify membership, source/provenance and recomputed stored embeddings.

    ``spans`` must be generated from the authoritative text with the bound
    tokenizer. Extra, missing, stale, or malformed records fail closed.
    """
    if (
        not isinstance(parent_id, str)
        or not parent_id
        or not isinstance(source_text, str)
        or not source_text.strip()
        or not isinstance(spans, list)
        or not spans
        or len(spans) > 10000
        or not isinstance(expected_vectors, list)
        or len(expected_vectors) != len(spans)
        or not isinstance(expected_metadata, dict)
        or not isinstance(dimensions, int)
        or isinstance(dimensions, bool)
        or dimensions <= 0
    ):
        raise SemanticFamilyVerificationError("semantic_family_input_invalid")
    expected = {}
    parent_hash = sha256(source_text.encode("utf-8")).hexdigest()
    for index, span in enumerate(spans):
        if not isinstance(span, (tuple, list)) or len(span) != 3:
            raise SemanticFamilyVerificationError("semantic_family_span_invalid")
        text, start, end = span
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or not 0 <= start < end <= len(source_text)
            or text != source_text[start:end]
        ):
            raise SemanticFamilyVerificationError("semantic_family_span_invalid")
        item_id = parent_id if index == 0 else f"{parent_id}:chunk:{index}"
        metadata = {
            **expected_metadata,
            "vector_parent_id": parent_id,
            "vector_chunk_index": index,
            "vector_chunk_count": len(spans),
            "source_span_start": start,
            "source_span_end": end,
            "source_span_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "source_parent_sha256": parent_hash,
        }
        expected[item_id] = (text, metadata, expected_vectors[index])
    # Metadata cannot identify an orphaned family member after corruption. Scan
    # IDs independently while the caller holds the shared mutation lock.
    # Refuse an over-limit or unstable inventory rather than claiming parity.
    offset = 0
    seen_ids = set()
    family_ids = set()
    while True:
        count = min(_INVENTORY_PAGE_SIZE, _INVENTORY_LIMIT + 1 - offset)
        inventory = collection.get(limit=count, offset=offset, include=[])
        batch = inventory.get("ids") if isinstance(inventory, dict) else None
        if (
            not isinstance(batch, list)
            or len(batch) > count
            or any(not isinstance(value, str) for value in batch)
            or len(set(batch)) != len(batch)
            or seen_ids.intersection(batch)
        ):
            raise SemanticFamilyVerificationError("semantic_inventory_invalid")
        seen_ids.update(batch)
        if len(seen_ids) > _INVENTORY_LIMIT:
            raise SemanticFamilyVerificationError("semantic_inventory_over_limit")
        family_ids.update(
            value
            for value in batch
            if value == parent_id or value.startswith(f"{parent_id}:chunk:")
        )
        if len(batch) < count:
            break
        offset += len(batch)
    if family_ids != set(expected):
        raise SemanticFamilyVerificationError("semantic_family_membership_mismatch")
    page = collection.get(
        where={"vector_parent_id": {"$eq": parent_id}},
        limit=len(spans) + 1,
        include=["documents", "metadatas", "embeddings"],
    )
    if not isinstance(page, dict):
        raise SemanticFamilyVerificationError("semantic_family_result_invalid")
    ids = page.get("ids")
    texts = page.get("documents")
    metas = page.get("metadatas")
    vectors = page.get("embeddings")
    if (
        not isinstance(ids, list)
        or any(not isinstance(item_id, str) for item_id in ids)
        or not isinstance(texts, list)
        or not isinstance(metas, list)
        or vectors is None
        or len(ids) != len(expected)
        or len(texts) != len(ids)
        or len(metas) != len(ids)
        or len(vectors) != len(ids)
        or len(set(ids)) != len(ids)
        or set(ids) != set(expected)
    ):
        raise SemanticFamilyVerificationError("semantic_family_membership_mismatch")
    for item_id, text, metadata, vector in zip(ids, texts, metas, vectors):
        wanted_text, wanted_metadata, wanted_vector = expected[item_id]
        if (
            text != wanted_text
            or not isinstance(metadata, dict)
            or any(metadata.get(key) != value for key, value in wanted_metadata.items())
        ):
            raise SemanticFamilyVerificationError("semantic_family_content_mismatch")
        try:
            valid_vector = (
                len(vector) == dimensions
                and all(math.isfinite(float(value)) for value in vector)
                and abs(sum(float(value) ** 2 for value in vector) - 1.0) <= 0.001
                and len(wanted_vector) == dimensions
                and all(math.isfinite(float(value)) for value in wanted_vector)
                and all(
                    abs(float(value) - float(wanted)) <= 1e-5
                    for value, wanted in zip(vector, wanted_vector)
                )
            )
        except (TypeError, ValueError, OverflowError):
            valid_vector = False
        if not valid_vector:
            raise SemanticFamilyVerificationError("semantic_family_vector_invalid")
    return len(expected)
