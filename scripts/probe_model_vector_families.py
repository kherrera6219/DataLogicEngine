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
from scripts.probe_offline_embedding_bundle import MANIFEST, WEIGHTS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_path", type=Path)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--disposable-empty-store", action="store_true", required=True)
    args = parser.parse_args()
    backend = ChromaDBBackend(host="127.0.0.1", port=args.port)
    if backend.client.list_collections(limit=1):
        raise RuntimeError("disposable_empty_store_required")
    for name in ("documents", "knowledge_nodes", "chat_history", "persona_profiles"):
        safe_create_collection(
            backend.client, name=name, metadata={"dle_disposable_test_data": True}
        )
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
    assert safe_get_collection(backend.client, name="documents").count() == 1
    assert rag.ingest_knowledge_node("synthetic-node", text, "test", {"user_id": "one"})
    assert rag.ingest_knowledge_node(
        "retained-node", "another owner source", "test", {"user_id": "two"}
    )
    assert rag.delete_knowledge_node("synthetic-node")
    assert safe_get_collection(backend.client, name="knowledge_nodes").get(
        include=["metadatas"]
    )["ids"] == ["retained-node"]
    session = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    other_session = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    assert rag.store_chat_message(
        session, "synthetic-message", "user", text, user_id="one"
    )
    chats = safe_get_collection(backend.client, name="chat_history")
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
    assert rag.ingest_text(
        "persona_profiles", "synthetic-persona", text, {"user_id": "one"}
    )
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
                "active_index_changed": False,
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
