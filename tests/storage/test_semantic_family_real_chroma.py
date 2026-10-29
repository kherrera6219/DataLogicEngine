"""Exercise semantic family verification against disposable embedded Chroma."""

import socket
from hashlib import sha256
from uuid import uuid4

import pytest

from backend.storage.semantic_family_verification import (
    SemanticFamilyVerificationError,
    verify_semantic_family,
)


def test_synthetic_family_verification_with_embedded_chroma(monkeypatch):
    def block_socket(*_args, **_kwargs):
        raise RuntimeError("socket blocked during disposable semantic probe")

    monkeypatch.setattr(socket.socket, "connect", block_socket)
    monkeypatch.setattr(socket, "create_connection", block_socket)
    import chromadb
    from chromadb.config import Settings

    client = chromadb.EphemeralClient(
        settings=Settings(anonymized_telemetry=False, allow_reset=True)
    )
    name = f"semantic-verifier-{uuid4().hex}"
    collection = client.create_collection(
        name, embedding_function=None, configuration={"hnsw": {"space": "cosine"}}
    )
    try:
        source = "alpha beta gamma"
        spans = [("alpha beta", 0, 10), ("beta gamma", 6, 16)]
        common = {"user_id": "synthetic-owner", "source_revision": "synthetic-revision"}
        vectors = [[0.6, 0.8], [0.8, 0.6]]
        ids = ["synthetic-parent", "synthetic-parent:chunk:1"]
        metadata = [
            {
                **common,
                "vector_parent_id": "synthetic-parent",
                "vector_chunk_index": i,
                "vector_chunk_count": len(spans),
                "source_span_start": start,
                "source_span_end": end,
                "source_span_sha256": sha256(text.encode()).hexdigest(),
                "source_parent_sha256": sha256(source.encode()).hexdigest(),
            }
            for i, (text, start, end) in enumerate(spans)
        ]
        collection.add(
            ids=ids,
            documents=[text for text, _, _ in spans],
            embeddings=vectors,
            metadatas=metadata,
        )

        def verify():
            return verify_semantic_family(
                collection,
                parent_id="synthetic-parent",
                source_text=source,
                spans=spans,
                expected_metadata=common,
                dimensions=2,
                expected_vectors=vectors,
            )

        assert verify() == 2
        collection.update(ids=[ids[0]], metadatas=[{**metadata[0], "user_id": "other"}])
        with pytest.raises(SemanticFamilyVerificationError, match="content_mismatch"):
            verify()
        collection.update(ids=[ids[0]], metadatas=[metadata[0]])
        collection.update(ids=[ids[0]], embeddings=[[0.8, 0.6]])
        with pytest.raises(SemanticFamilyVerificationError, match="vector_invalid"):
            verify()
        collection.update(ids=[ids[0]], embeddings=[vectors[0]])
        collection.delete(ids=[ids[1]])
        with pytest.raises(
            SemanticFamilyVerificationError, match="membership_mismatch"
        ):
            verify()
        collection.add(
            ids=[ids[1]],
            documents=[spans[1][0]],
            embeddings=[vectors[1]],
            metadatas=[metadata[1]],
        )
        collection.add(
            ids=["synthetic-parent:chunk:2"],
            documents=["alpha"],
            embeddings=[vectors[0]],
            metadatas=[metadata[0]],
        )
        with pytest.raises(
            SemanticFamilyVerificationError, match="membership_mismatch"
        ):
            verify()
        collection.update(
            ids=["synthetic-parent:chunk:2"],
            metadatas=[{**metadata[0], "vector_parent_id": "other"}],
        )
        with pytest.raises(
            SemanticFamilyVerificationError, match="membership_mismatch"
        ):
            verify()
    finally:
        client.delete_collection(name)
    assert name not in {item.name for item in client.list_collections()}
