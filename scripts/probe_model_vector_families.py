"""Exercise semantic vector families on an explicitly disposable empty store."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from backend.services.local_sentence_embedding import LocalSentenceEmbedding
from backend.services.rag_service import RAGService
from backend.storage.chroma_security import safe_create_collection, safe_get_collection
from backend.storage.vector_store import ChromaDBBackend, VectorStore
from backend.storage.semantic_index_profile import (
    SemanticIndexProfile,
    ProfiledChromaBackend,
    provision_profile_collections,
)
from scripts.probe_offline_embedding_bundle import MANIFEST, WEIGHTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--disposable-empty-store", action="store_true", required=True)
    parser.add_argument("--profiled", action="store_true")
    args = parser.parse_args()
    backend = ChromaDBBackend(host="127.0.0.1", port=args.port)
    if backend.client.list_collections(limit=1):
        raise RuntimeError("disposable_empty_store_required")
    for name in ("documents", "knowledge_nodes", "chat_history", "persona_profiles"):
        safe_create_collection(
            backend.client, name=name, metadata={"dle_disposable_test_data": True}
        )
    profile = None
    if args.profiled:
        profile = SemanticIndexProfile(weights_sha256=WEIGHTS, manifest_sha256=MANIFEST)
        provision_profile_collections(backend.client, profile)
        backend = ProfiledChromaBackend(backend.client, profile)

    def collection(logical):
        name = profile.collection_name(logical) if profile is not None else logical
        return safe_get_collection(backend.client, name=name)

    embed = LocalSentenceEmbedding(
        args.model_path,
        expected_weights_sha256=WEIGHTS,
        expected_manifest_sha256=MANIFEST,
    )
    rag = RAGService(
        vector_store=VectorStore(backend=backend), embedding_provider=embed
    )
    text = (
        "This fictional handbook includes introductory notes and additional background. "
    ) * 100
    text += "The synthetic archive policy keeps backup copies for ninety days."
    count = rag.ingest_document("synthetic-doc", text, {"user_id": "one"})
    assert count > 1
    assert (
        rag.ingest_document("synthetic-doc", "short replacement", {"user_id": "one"})
        == 1
    )
    assert collection("documents").count() == 1
    assert rag.ingest_knowledge_node("synthetic-node", text, "test", {"user_id": "one"})
    assert rag.ingest_knowledge_node(
        "retained-node", "another owner source", "test", {"user_id": "two"}
    )
    assert rag.delete_knowledge_node("synthetic-node")
    assert collection("knowledge_nodes").get(include=["metadatas"])["ids"] == [
        "retained-node"
    ]
    session = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    other_session = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    assert rag.store_chat_message(
        session, "synthetic-message", "user", text, user_id="one"
    )
    chats = collection("chat_history")
    initial_count = chats.count()
    assert initial_count > 1
    assert rag.store_chat_message(
        session, "synthetic-message", "user", text, user_id="one"
    )
    assert chats.count() == initial_count
    assert rag.store_chat_message(
        other_session, "retained-message", "user", "other owner", user_id="two"
    )
    rag.delete_chat_session(session)
    assert chats.get(include=["metadatas"])["ids"] == ["retained-message"]
    assert rag.search_user_chat_history("one", "other owner", k=5) == []
    owner_recall = rag.search_user_chat_history("two", "other owner", k=5)
    assert owner_recall and all(
        row["metadata"]["user_id"] == "two" for row in owner_recall
    )
    assert (
        rag.search_user_chat_history(
            "two", "other owner", k=5, exclude_session_id=other_session
        )
        == []
    )
    assert rag.ingest_text(
        "persona_profiles", "synthetic-persona", text, {"user_id": "one"}
    )
    if profile is not None:
        assert all(
            safe_get_collection(backend.client, name=name).count() == 0
            for name in (
                "documents",
                "knowledge_nodes",
                "chat_history",
                "persona_profiles",
            )
        )
        query = embed("short replacement")
        rows = collection("knowledge_nodes").query(
            query_embeddings=[query], n_results=1, include=["embeddings", "distances"]
        )
        distance = rows["distances"][0][0]
        expected = 1.0 - sum(a * b for a, b in zip(query, rows["embeddings"][0][0]))
        assert abs(distance - expected) < 0.0001
    print(
        json.dumps(
            {
                "status": "pass",
                "disposable_only": True,
                "long_document_chunks": count,
                "long_chat_chunks": initial_count,
                "obsolete_chunks_removed": True,
                "knowledge_family_removed": True,
                "other_owner_preserved": True,
                "retry_idempotent": True,
                "chat_session_removed": True,
                "owner_filtered_recall_verified": True,
                "active_session_exclusion_verified": True,
                "active_index_changed": False,
                "profiled": profile is not None,
                "cosine_metric_verified": profile is not None,
                "model_manifest_sha256": MANIFEST,
                "source_sha256": {
                    path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                    for path in (
                        "scripts/probe_model_vector_families.py",
                        "backend/services/rag_service.py",
                        "backend/storage/vector_store.py",
                        "backend/services/local_sentence_embedding.py",
                        "backend/services/model_text_chunking.py",
                    )
                },
            }
        )
    )


if __name__ == "__main__":
    main()
