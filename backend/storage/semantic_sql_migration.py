"""Bounded, inactive semantic staging from managed PostgreSQL authority.

Staging is disabled until deletion reaches inactive collections, the Chroma
endpoint is bound to the managed runtime, lock-held work is bounded, and orphan
reconciliation and coordinated cutover have been qualified. This module never
changes routing or legacy collections.
"""

from __future__ import annotations

from hashlib import sha256
import hashlib
import hmac
import json
from uuid import UUID

from sqlalchemy.orm import Session

from backend.storage.chat_index_coordination import chat_index_guard
from backend.storage.knowledge_ownership import ownership_ids
from backend.storage.semantic_family_verification import verify_semantic_family
from backend.storage.semantic_index_profile import ProfiledChromaBackend


class SemanticMigrationError(RuntimeError):
    """Migration cannot safely stage or verify a source record."""


def _require_staging_prerequisites():
    """Refuse all staging until the missing lifecycle protections exist."""
    raise SemanticMigrationError("semantic_migration_staging_disabled")


def _require_managed_runtime(engine, runtime):
    from flask import current_app, has_app_context
    from extensions import db

    if (
        not has_app_context()
        or current_app.extensions.get("dle_runtime") is not runtime
        or db.engine is not engine
    ):
        raise SemanticMigrationError("semantic_migration_authority_invalid")


def _identity_tombstoned(session, key, kind, value):
    from models import DataDeletionTombstone

    digest = hmac.new(
        key.encode("utf-8"), f"{kind}:{value}".encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return (
        session.query(DataDeletionTombstone.deletion_id)
        .filter_by(subject_type=kind, subject_digest=digest)
        .first()
        is not None
    )


def _source(session, kind, record_id, deletion_key):
    """Read the current canonical row and fail on ambiguity or deletion."""
    from models import (
        ChatMessage,
        ChatSession,
        IngestionChunk,
        IngestionFile,
        IngestionJob,
        KnowledgeGraphNode,
    )

    if kind == "chat":
        row = (
            session.query(ChatMessage, ChatSession)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .filter(ChatMessage.id == record_id)
            .populate_existing()
            .one_or_none()
        )
        if row is None:
            raise SemanticMigrationError("semantic_source_missing")
        message, owner = row
        if (
            message.role not in {"user", "assistant"}
            or not message.content.strip()
            or owner.user_id is None
        ):
            raise SemanticMigrationError("semantic_chat_source_invalid")
        if _identity_tombstoned(session, deletion_key, "user", owner.user_id):
            raise SemanticMigrationError("semantic_source_owner_deleted")
        return {
            "kind": kind,
            "id": str(message.id),
            "text": message.content,
            "session_id": str(owner.id),
            "user_id": str(owner.user_id),
            "role": message.role,
        }
    rows = (
        session.query(IngestionChunk, IngestionFile, IngestionJob, KnowledgeGraphNode)
        .join(IngestionFile, IngestionChunk.file_id == IngestionFile.id)
        .join(IngestionJob, IngestionChunk.job_id == IngestionJob.id)
        .join(KnowledgeGraphNode, KnowledgeGraphNode.uid == IngestionChunk.node_uid)
        .filter(IngestionChunk.id == record_id)
        .populate_existing()
        .all()
    )
    if len(rows) != 1:
        raise SemanticMigrationError("semantic_source_missing_or_ambiguous")
    chunk, source_file, job, node = rows[0]
    metadata = node.node_metadata
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    if not isinstance(metadata, dict):
        raise SemanticMigrationError("semantic_source_metadata_invalid")
    defense = source_file.defense_result
    if isinstance(defense, str):
        defense = json.loads(defense)
    owners, tenants = ownership_ids(
        {"node_metadata": metadata, "tenant_id": node.tenant_id}
    )
    expected_owners = {str(job.user_id)} if job.user_id is not None else set()
    expected_tenants = {str(job.tenant_id)} if job.tenant_id else set()
    if (
        owners != expected_owners
        or tenants != expected_tenants
        or job.status != "completed"
        or source_file.job_id != chunk.job_id
        or not isinstance(node.uid, str)
        or not node.uid.startswith("ki_")
        or source_file.status not in {"ready", "duplicate"}
        or source_file.object_status != "ready"
        or source_file.normalized_object_status != "ready"
        or chunk.materialization_state != "ready"
        or not isinstance(defense, dict)
        or defense.get("policy_version") != "content-defense.v1"
        or defense.get("safe_for_retrieval") is not True
        or metadata.get("source_revision") != chunk.source_revision
        or not isinstance(node.content, str)
        or not node.content.strip()
        or sha256(node.content.encode("utf-8")).hexdigest() != chunk.chunk_sha256
    ):
        raise SemanticMigrationError("semantic_knowledge_source_ineligible")
    for identity_kind, values in (("user", owners), ("tenant", tenants)):
        for identity in values:
            if _identity_tombstoned(session, deletion_key, identity_kind, identity):
                raise SemanticMigrationError("semantic_source_owner_deleted")
    return {
        "kind": kind,
        "id": node.uid,
        "text": node.content,
        "node_type": node.node_type,
        "metadata": {
            **metadata,
            "node_id": node.node_id,
            "title": node.title or node.label,
            "user_id": job.user_id,
            "tenant_id": job.tenant_id,
            "source_revision": chunk.source_revision,
            "chunk_index": chunk.chunk_index,
            "chunk_count": chunk.chunk_count,
        },
    }


def stage_semantic_sql_batch(*, engine, runtime, rag, kind, cursor=None, limit=25):
    """Stage one bounded, retryable batch; return the last committed cursor.

    A failed batch returns no cursor: retry the previous one, replacing each
    family idempotently. Cursor is an opaque SQL UUID, not evidence of parity.
    """
    _require_staging_prerequisites()

    from models import ChatMessage, IngestionChunk

    if (
        engine.dialect.name != "postgresql"
        or kind not in {"chat", "knowledge"}
        or not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 100
        or not rag._uses_local_model()
        or not isinstance(rag._get_vector_store(), ProfiledChromaBackend)
    ):
        raise SemanticMigrationError("semantic_migration_configuration_invalid")
    _require_managed_runtime(engine, runtime)
    identity = runtime.ownership.identity
    identity_value = (
        identity.installation_id if identity is not None else runtime.instance_id
    )
    if not identity_value:
        raise SemanticMigrationError("semantic_migration_identity_missing")
    deletion_key = str(identity_value)
    try:
        after = UUID(cursor) if cursor else None
    except (TypeError, ValueError, AttributeError) as exc:
        raise SemanticMigrationError("semantic_migration_cursor_invalid") from exc
    entity = ChatMessage if kind == "chat" else IngestionChunk
    store = rag._get_vector_store()
    logical = (
        rag.COLLECTION_CHAT_HISTORY if kind == "chat" else rag.COLLECTION_KNOWLEDGE
    )
    with chat_index_guard(runtime.runtime_root):
        with Session(engine) as session:
            if session.connection().get_isolation_level() != "READ COMMITTED":
                raise SemanticMigrationError("semantic_migration_isolation_invalid")
            query = session.query(entity.id).order_by(entity.id)
            if after is not None:
                query = query.filter(entity.id > after)
            ids = [row[0] for row in query.limit(limit + 1).all()]
            has_more = len(ids) > limit
            ids = ids[:limit]
            for record_id in ids:
                before = _source(session, kind, record_id, deletion_key)
                if kind == "chat":
                    acknowledged = rag.store_chat_message(
                        before["session_id"],
                        before["id"],
                        before["role"],
                        before["text"],
                        user_id=before["user_id"],
                    )
                    expected = {
                        "session_id": before["session_id"],
                        "user_id": before["user_id"],
                        "role": before["role"],
                    }
                else:
                    acknowledged = rag.ingest_knowledge_node(
                        before["id"],
                        before["text"],
                        before["node_type"],
                        before["metadata"],
                    )
                    expected = rag._metadata_for_chroma(
                        {**before["metadata"], "node_type": before["node_type"]}
                    )
                if not acknowledged:
                    raise SemanticMigrationError("semantic_staging_unacknowledged")
                expected.update(store.profile.record_metadata)
                expected["embedding_revision"] = rag.embedding_revision
                spans = rag._embedding_provider.chunk_spans(
                    before["text"], max_tokens=512
                )
                verify_semantic_family(
                    store._get_collection(logical),
                    parent_id=before["id"],
                    source_text=before["text"],
                    spans=spans,
                    expected_metadata=expected,
                    dimensions=store.profile.dimensions,
                    expected_vectors=[
                        rag._embedding_provider(text) for text, _, _ in spans
                    ],
                )
                session.expire_all()
                if _source(session, kind, record_id, deletion_key) != before:
                    raise SemanticMigrationError("semantic_source_changed")
            return {
                "status": "staged_not_activated",
                "kind": kind,
                "processed": len(ids),
                "cursor": str(ids[-1]) if ids else cursor,
                "has_more": has_more,
                "profile_id": store.profile.profile_id,
            }
