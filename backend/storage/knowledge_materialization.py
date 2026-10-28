"""Recheck canonical knowledge and deletion receipts before queued delivery."""

from __future__ import annotations

import hashlib
import hmac
import json

from sqlalchemy import select
from sqlalchemy.orm import Session, object_session

from backend.storage.chat_index_coordination import chat_index_guard
from backend.storage.knowledge_ownership import ownership_ids


def deliver_owned_knowledge(event, destination):
    from flask import current_app
    from backend.storage.materialization_dispatcher import MaterializationDeliveryError
    from models import DataDeletionTombstone, KnowledgeGraphNode

    event_session = object_session(event)
    if event_session is None:
        raise MaterializationDeliveryError("knowledge_authority_session_missing")
    runtime = current_app.extensions["dle_runtime"]
    with chat_index_guard(runtime.runtime_root):
        # A fresh transaction starts after acquisition, so a previously cached
        # outbox object cannot supply a stale view of the authority record.
        with Session(event_session.get_bind()) as authority:
            source = (
                authority.query(KnowledgeGraphNode)
                .filter_by(uid=str(event.entity_id))
                .one_or_none()
            )
            if source is None:
                return event.source_revision
            owners, tenants = ownership_ids(
                {"node_metadata": source.node_metadata, "tenant_id": source.tenant_id}
            )
            if len(owners) > 1 or len(tenants) > 1:
                raise MaterializationDeliveryError("knowledge_ownership_conflict")
            identity = runtime.ownership.identity
            key = (
                identity.installation_id
                if identity is not None
                else runtime.instance_id
            )
            for kind, identities in (("user", owners), ("tenant", tenants)):
                for value in identities:
                    digest = hmac.new(
                        str(key).encode(), f"{kind}:{value}".encode(), hashlib.sha256
                    ).hexdigest()
                    if (
                        authority.scalar(
                            select(DataDeletionTombstone.deletion_id)
                            .where(
                                DataDeletionTombstone.subject_type == kind,
                                DataDeletionTombstone.subject_digest == digest,
                            )
                            .limit(1)
                        )
                        is not None
                    ):
                        raise MaterializationDeliveryError(
                            "knowledge_owner_deletion_requested"
                        )
            metadata = (
                json.loads(source.node_metadata)
                if isinstance(source.node_metadata, str)
                else dict(source.node_metadata or {})
            )
            revision = metadata.get("source_revision")
            if revision is not None and revision != event.source_revision:
                raise MaterializationDeliveryError("knowledge_source_revision_changed")
            if not isinstance(source.content, str) or not source.content.strip():
                raise MaterializationDeliveryError("knowledge_source_content_missing")
            owner = next(iter(owners)) if owners else None
            tenant = next(iter(tenants)) if tenants else None
            if destination == "chroma":
                from backend.services.rag_service import get_rag_service

                metadata.update(
                    {
                        "node_id": source.node_id,
                        "title": source.title or source.label,
                        "tenant_id": tenant,
                        "user_id": owner,
                        "schema_version": event.schema_version,
                        "source_revision": event.source_revision,
                    }
                )
                if not get_rag_service().ingest_knowledge_node(
                    source.uid, source.content, source.node_type, metadata
                ):
                    raise MaterializationDeliveryError("chroma_upsert_failed")
            elif destination == "neo4j":
                from backend.storage import get_graph_store

                store = get_graph_store()
                store.connect()
                properties = {
                    "uid": source.uid,
                    "node_id": source.node_id,
                    "node_type": source.node_type,
                    "label": source.label,
                    "title": source.title,
                    "description": source.description,
                    "content": source.content,
                    "content_type": source.content_type,
                    "tenant_id": tenant,
                    "user_id": owner,
                    "schema_version": event.schema_version,
                    "source_revision": event.source_revision,
                }
                if not store.merge_knowledge_node(properties):
                    raise MaterializationDeliveryError("neo4j_merge_failed")
            else:
                raise MaterializationDeliveryError("knowledge_destination_invalid")
            return event.source_revision
