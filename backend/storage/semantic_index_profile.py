"""Versioned, vector-only semantic stores; activation is a separate operation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

from backend.services.model_text_chunking import CHUNKING_REVISION
from backend.storage.chroma_security import (
    safe_get_collection,
    validate_collection_configuration,
)
from backend.storage.vector_store import ChromaDBBackend, VectorDeleteError

LOGICAL_COLLECTIONS = (
    "documents",
    "knowledge_nodes",
    "chat_history",
    "persona_profiles",
    "citation_cache",
    "audit_evidence",
)


class SemanticProfileError(RuntimeError):
    """The store does not match the approved model/metric binding."""


@dataclass(frozen=True)
class SemanticIndexProfile:
    weights_sha256: str
    manifest_sha256: str
    dimensions: int = 384
    min_relevance_score: float = 0.25
    chunking_revision: str = CHUNKING_REVISION

    def __post_init__(self):
        for value in (self.weights_sha256, self.manifest_sha256):
            if (
                not isinstance(value, str)
                or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise SemanticProfileError("semantic_profile_fingerprint_invalid")
        if (
            not isinstance(self.dimensions, int)
            or self.dimensions != 384
            or isinstance(self.dimensions, bool)
            or self.chunking_revision != CHUNKING_REVISION
        ):
            raise SemanticProfileError("semantic_profile_model_invalid")
        if (
            isinstance(self.min_relevance_score, bool)
            or not isinstance(self.min_relevance_score, (int, float))
            or not math.isfinite(self.min_relevance_score)
            or not 0 <= self.min_relevance_score <= 1
        ):
            raise SemanticProfileError("semantic_profile_threshold_invalid")

    @property
    def record_metadata(self):
        return {
            "dle_embedding_manifest": self.manifest_sha256,
            "dle_embedding_weights": self.weights_sha256,
            "dle_embedding_dimensions": self.dimensions,
            "dle_chunking_revision": self.chunking_revision,
        }

    @property
    def profile_id(self):
        payload = {
            **self.record_metadata,
            "metric": "cosine",
            "threshold": self.min_relevance_score,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    @property
    def collection_metadata(self):
        return {
            **self.record_metadata,
            "dle_semantic_profile": self.profile_id,
            "dle_distance_metric": "cosine",
            "dle_min_relevance": self.min_relevance_score,
        }

    def collection_name(self, logical):
        if logical not in LOGICAL_COLLECTIONS:
            raise SemanticProfileError("semantic_logical_collection_invalid")
        return f"dle_sem_{self.profile_id[:16]}_{logical}"

    def validate_collection(self, logical, collection):
        validate_collection_configuration(collection)
        if collection.name != self.collection_name(logical):
            raise SemanticProfileError("semantic_collection_name_mismatch")
        metadata = collection.metadata
        if any(
            metadata.get(key) != value
            for key, value in self.collection_metadata.items()
        ):
            raise SemanticProfileError("semantic_collection_model_mismatch")
        configuration = collection._model.configuration_json
        if (
            not isinstance(configuration, dict)
            or not isinstance(configuration.get("hnsw"), dict)
            or configuration["hnsw"].get("space") != "cosine"
        ):
            raise SemanticProfileError("semantic_collection_metric_mismatch")
        return collection


def provision_profile_collections(client, profile: SemanticIndexProfile):
    """Explicitly create only new versioned names; never modify legacy collections."""
    existing = {}
    offset = 0
    while True:
        page = client.list_collections(limit=100, offset=offset)
        for collection in page:
            if collection.name in existing:
                raise SemanticProfileError("semantic_collection_inventory_unstable")
            existing[collection.name] = collection
        if len(page) < 100:
            break
        offset += 100
        if offset >= 10000:
            raise SemanticProfileError("semantic_collection_inventory_over_limit")
    for logical in LOGICAL_COLLECTIONS:
        name = profile.collection_name(logical)
        collection = existing.get(name)
        if collection is None:
            collection = client.create_collection(
                name=name,
                metadata=profile.collection_metadata,
                embedding_function=None,
                configuration={"hnsw": {"space": "cosine"}},
            )
        profile.validate_collection(logical, collection)


class ProfiledChromaBackend(ChromaDBBackend):
    """Use only preprovisioned, verified collections for this one model profile."""

    def __init__(self, client, profile: SemanticIndexProfile):
        super().__init__()
        self._client = client
        self.profile = profile

    def _get_collection(self, name):
        collection = safe_get_collection(
            self.client, name=self.profile.collection_name(name)
        )
        return self.profile.validate_collection(name, collection)

    def _validate_vectors(self, vectors):
        if not isinstance(vectors, list) or not vectors:
            raise SemanticProfileError("semantic_vectors_invalid")
        for vector in vectors:
            if (
                not isinstance(vector, list)
                or len(vector) != self.profile.dimensions
                or any(
                    isinstance(x, bool)
                    or not isinstance(x, (int, float))
                    or not math.isfinite(x)
                    for x in vector
                )
            ):
                raise SemanticProfileError("semantic_vector_dimensions_invalid")
            if abs(sum(x * x for x in vector) - 1.0) > 0.001:
                raise SemanticProfileError("semantic_vector_normalization_invalid")

    def _validate_write(self, embeddings, metadata):
        self._validate_vectors(embeddings)
        if (
            not isinstance(metadata, list)
            or len(metadata) != len(embeddings)
            or any(
                not isinstance(meta, dict)
                or any(
                    meta.get(key) != value
                    for key, value in self.profile.record_metadata.items()
                )
                for meta in metadata
            )
        ):
            raise SemanticProfileError(
                "semantic_vector_provenance_missing_or_mismatched"
            )

    def add_embeddings(self, collection, ids, texts, embeddings, metadata=None):
        self._validate_write(embeddings, metadata)
        return super().add_embeddings(collection, ids, texts, embeddings, metadata)

    def replace_embeddings(
        self, collection, parent_id, *, ids, texts, embeddings, metadata
    ):
        self._validate_write(embeddings, metadata)
        return super().replace_embeddings(
            collection,
            parent_id,
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadata=metadata,
        )

    def search(self, collection, query_embedding, k=10, filters=None):
        self._validate_vectors([query_embedding])
        return [
            result
            for result in super().search(collection, query_embedding, k, filters)
            if result.score >= self.profile.min_relevance_score
        ]

    def delete_parent_embeddings(self, collection, parent_id):
        if not isinstance(parent_id, str) or not parent_id or len(parent_id) > 255:
            raise VectorDeleteError("vector_family_parent_invalid")
        self._delete_parent(self._get_collection(collection), parent_id)

    def delete_chat_session(self, session_id):
        if not isinstance(session_id, str) or not session_id or len(session_id) > 128:
            raise VectorDeleteError("chat_index_session_invalid")
        target = self._get_collection("chat_history")
        selector = {"session_id": {"$eq": session_id}}
        target.delete(where=selector)
        remaining = target.get(where=selector, limit=1, include=["metadatas"])
        if not isinstance(remaining, dict) or remaining.get("ids") != []:
            raise VectorDeleteError("chat_index_deletion_unverified")

    def create_collection(self, collection, dimension=384):
        if dimension != self.profile.dimensions:
            raise SemanticProfileError("semantic_vector_dimensions_invalid")
        self._get_collection(collection)
        return True

    def delete_collection(self, collection):
        raise SemanticProfileError(
            "semantic_collection_deletion_requires_migration_control"
        )
