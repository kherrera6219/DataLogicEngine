"""
Verify local data-plane wiring for DataLogicEngine.

Checks:
- ConnectionManager status report
- PostgreSQL connectivity (if DATABASE_URL is PostgreSQL)
- Redis ping (if REDIS_URL is configured)
- Neo4j connectivity (if NEO4J_URI is configured)
- Object store round-trip (local or S3/MinIO backend)
- Vector store round-trip (Chroma/Pinecone backend)
- RAG chat-memory search (current + prior-thread metadata path)
"""

from __future__ import annotations

import os
import sys
import uuid
from dataclasses import dataclass

from dotenv import load_dotenv

# Ensure project root import path.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv(".env")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _print(check: Check) -> None:
    status = "PASS" if check.ok else "FAIL"
    print(f"[{status}] {check.name}: {check.detail}")


def check_connection_manager() -> Check:
    try:
        from backend.storage import get_connection_manager

        status = get_connection_manager().get_status_report()
        mode = status.get("mode", "unknown")
        services = status.get("services", {})
        summary = ", ".join(f"{k}={'up' if v.get('healthy') else 'down'}" for k, v in services.items())
        return Check("ConnectionManager", True, f"mode={mode}; {summary}")
    except Exception as e:
        return Check("ConnectionManager", False, str(e))


def check_rag_orchestration_packages() -> Check:
    try:
        import importlib.util

        required = ["llama_index", "langchain", "langgraph", "httpx"]
        missing = [name for name in required if importlib.util.find_spec(name) is None]
        if missing:
            return Check("RAG/Orchestration Packages", False, f"Missing packages: {', '.join(missing)}")
        return Check("RAG/Orchestration Packages", True, "llama-index, langchain, langgraph, and the restricted HTTP transport are installed.")
    except Exception as e:
        return Check("RAG/Orchestration Packages", False, str(e))


def check_postgres() -> Check:
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url.startswith(("postgresql://", "postgres://")):
        return Check("PostgreSQL", True, "Skipped (DATABASE_URL is not PostgreSQL).")

    try:
        import psycopg2

        conn = psycopg2.connect(db_url, connect_timeout=5)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        finally:
            conn.close()
        return Check("PostgreSQL", True, "Connection + SELECT 1 succeeded.")
    except Exception as e:
        return Check("PostgreSQL", False, str(e))


def check_redis() -> Check:
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return Check("Redis", True, "Skipped (REDIS_URL not configured).")

    try:
        import redis

        client = redis.from_url(redis_url, socket_timeout=5, socket_connect_timeout=5, decode_responses=True)
        pong = client.ping()
        return Check("Redis", bool(pong), "PING succeeded." if pong else "PING returned false.")
    except Exception as e:
        return Check("Redis", False, str(e))


def check_neo4j() -> Check:
    neo4j_uri = os.getenv("NEO4J_URI")
    if not neo4j_uri:
        return Check("Neo4j", True, "Skipped (NEO4J_URI not configured).")

    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(neo4j_uri, auth=(user, password))
        try:
            driver.verify_connectivity()
        finally:
            driver.close()
        return Check("Neo4j", True, "Connectivity verified.")
    except Exception as e:
        return Check("Neo4j", False, str(e))


def check_object_store() -> Check:
    try:
        from backend.storage import get_object_store, get_connection_manager

        manager = get_connection_manager()
        bucket = manager.config.object_storage.bucket or "datalogic"
        store = get_object_store()

        key = f"health/{uuid.uuid4()}.txt"
        payload = b"stack-health-ok"
        try:
            store.create_bucket(bucket)
        except Exception:
            # Bucket may already exist in S3/MinIO mode.
            pass
        store.put(bucket=bucket, key=key, data=payload, content_type="text/plain")
        loaded = store.get(bucket=bucket, key=key)
        store.delete(bucket=bucket, key=key)
        if loaded != payload:
            return Check("Object Store", False, "Round-trip payload mismatch.")
        return Check("Object Store", True, f"Round-trip succeeded for bucket={bucket}.")
    except Exception as e:
        return Check("Object Store", False, str(e))


def check_vector_store() -> Check:
    try:
        from backend.storage import get_vector_store

        store = get_vector_store()
        collection = "healthcheck"
        vec_id = f"hc-{uuid.uuid4()}"
        vector = [0.01] * 64
        store.add_embeddings(
            collection=collection,
            ids=[vec_id],
            texts=["health check vector"],
            embeddings=[vector],
            metadata=[{"scope": "healthcheck"}],
        )
        results = store.search(collection=collection, query_embedding=vector, k=1, filters={"scope": "healthcheck"})
        store.delete(collection=collection, ids=[vec_id])
        if not results:
            return Check("Vector Store", False, "No results returned for self-similarity query.")
        return Check("Vector Store", True, "Add/search/delete round-trip succeeded.")
    except Exception as e:
        return Check("Vector Store", False, str(e))


def check_rag_chat_memory() -> Check:
    try:
        from backend.services.rag_service import RAGService

        # Use deterministic mock embeddings for test stability.
        rag = RAGService(embedding_provider=lambda _: [0.02] * 64)
        message_id = str(uuid.uuid4())
        rag.store_chat_message(
            session_id="session-a",
            message_id=message_id,
            role="user",
            content="hello from session A",
            user_id="user-1",
        )
        hits = rag.search_user_chat_history(
            user_id="user-1",
            query="hello",
            k=3,
            exclude_session_id="session-b",
        )
        if not hits:
            return Check("RAG Chat Memory", False, "No semantic results for user chat memory.")
        return Check("RAG Chat Memory", True, "Cross-thread semantic lookup path is active.")
    except Exception as e:
        return Check("RAG Chat Memory", False, str(e))


def main() -> int:
    checks = [
        check_connection_manager(),
        check_rag_orchestration_packages(),
        check_postgres(),
        check_redis(),
        check_neo4j(),
        check_object_store(),
        check_vector_store(),
        check_rag_chat_memory(),
    ]

    print("=== Local Data Stack Verification ===")
    for item in checks:
        _print(item)

    failures = [c for c in checks if not c.ok]
    print(f"\nSummary: {len(checks) - len(failures)}/{len(checks)} checks passed.")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
