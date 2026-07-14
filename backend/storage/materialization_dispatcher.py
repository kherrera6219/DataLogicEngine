"""Durable cross-store outbox delivery and reconciliation worker."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from threading import Event, Thread
from typing import Callable

from backend.storage.outbox import CrossStoreOutbox
from models import CrossStoreOutboxEvent


logger = logging.getLogger(__name__)


class MaterializationDeliveryError(RuntimeError):
    """Redaction-safe materialization failure."""


DeliveryHandler = Callable[[CrossStoreOutboxEvent], str]


def _chroma_handler(event: CrossStoreOutboxEvent) -> str:
    if event.operation != "upsert_knowledge_node":
        raise MaterializationDeliveryError("chroma_operation_unsupported")
    payload = event.payload or {}
    from backend.services.rag_service import get_rag_service

    metadata = dict(payload.get("metadata") or {})
    metadata.update(
        {
            "schema_version": event.schema_version,
            "source_revision": event.source_revision,
        }
    )
    delivered = get_rag_service().ingest_knowledge_node(
        str(payload.get("node_uid") or event.entity_id),
        str(payload.get("content") or ""),
        str(payload.get("node_type") or "knowledge_node"),
        metadata,
    )
    if not delivered:
        raise MaterializationDeliveryError("chroma_upsert_failed")
    return event.source_revision


def _neo4j_handler(event: CrossStoreOutboxEvent) -> str:
    if event.operation != "merge_knowledge_node":
        raise MaterializationDeliveryError("neo4j_operation_unsupported")
    payload = event.payload or {}
    from backend.storage import get_graph_store

    store = get_graph_store()
    store.connect()
    properties = dict(payload.get("properties") or {})
    properties.update(
        {
            "uid": str(payload.get("node_uid") or event.entity_id),
            "schema_version": event.schema_version,
            "source_revision": event.source_revision,
        }
    )
    if not store.merge_knowledge_node(properties):
        raise MaterializationDeliveryError("neo4j_merge_failed")
    return event.source_revision


def _minio_handler(event: CrossStoreOutboxEvent) -> str:
    if event.operation != "put_object":
        raise MaterializationDeliveryError("minio_operation_unsupported")
    payload = event.payload or {}
    bucket = str(payload.get("bucket") or "").strip()
    key = str(payload.get("key") or "").strip()
    if not bucket or not key:
        raise MaterializationDeliveryError("minio_object_location_invalid")
    if isinstance(payload.get("body"), (dict, list)):
        body = json.dumps(
            payload["body"],
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    else:
        try:
            body = base64.b64decode(str(payload.get("body_base64") or ""), validate=True)
        except ValueError as exc:
            raise MaterializationDeliveryError("minio_object_payload_invalid") from exc
    expected_body_hash = str(payload.get("body_sha256") or "").strip()
    if expected_body_hash and hashlib.sha256(body).hexdigest() != expected_body_hash:
        raise MaterializationDeliveryError("minio_object_hash_invalid")
    from backend.storage import get_object_store

    store = get_object_store()
    if not store.create_bucket(bucket):
        raise MaterializationDeliveryError("minio_bucket_unavailable")
    metadata = {
        str(name): str(value)
        for name, value in dict(payload.get("metadata") or {}).items()
    }
    metadata.update(
        {
            "schema_version": event.schema_version,
            "source_revision": event.source_revision,
            "payload_sha256": event.payload_sha256,
        }
    )
    stored_key = store.put(
        bucket,
        key,
        body,
        content_type=str(payload.get("content_type") or "application/octet-stream"),
        metadata=metadata,
    )
    if str(stored_key) != key or not store.exists(bucket, key):
        raise MaterializationDeliveryError("minio_object_verification_failed")
    stored_body = store.get(bucket, key)
    if hashlib.sha256(stored_body).hexdigest() != hashlib.sha256(body).hexdigest():
        raise MaterializationDeliveryError("minio_object_verification_failed")
    if event.entity_type == "truth_audit_event":
        from sqlalchemy.orm import object_session

        from models import TruthAuditEvent

        session = object_session(event)
        audit_event = (
            session.query(TruthAuditEvent).filter_by(event_id=event.entity_id).one_or_none()
            if session is not None
            else None
        )
        if audit_event is None:
            raise MaterializationDeliveryError("truth_audit_event_missing")
        audit_event.object_store_bucket = bucket
        audit_event.object_store_key = key
        event_data = dict(audit_event.event_data or {})
        event_data["object_store"] = {"bucket": bucket, "key": key, "status": "ready"}
        audit_event.event_data = event_data
        session.add(audit_event)
    return event.source_revision


def default_delivery_handlers() -> dict[str, DeliveryHandler]:
    return {
        "chroma": _chroma_handler,
        "minio": _minio_handler,
        "neo4j": _neo4j_handler,
    }


class CrossStoreMaterializationDispatcher:
    """Claim committed work, deliver idempotently, and persist each outcome."""

    def __init__(self, session, handlers: dict[str, DeliveryHandler] | None = None):
        self.session = session
        self.handlers = dict(handlers or default_delivery_handlers())

    def run_once(self, *, limit: int = 100) -> dict[str, int]:
        outbox = CrossStoreOutbox(self.session)
        claimed = outbox.claim_batch(limit=limit)
        event_ids = [event.id for event in claimed]
        self.session.commit()
        result = {"claimed": len(event_ids), "succeeded": 0, "failed": 0}
        for event_id in event_ids:
            event = self.session.get(CrossStoreOutboxEvent, event_id)
            if event is None or event.status != "processing":
                continue
            handler = self.handlers.get(event.destination)
            try:
                if handler is None:
                    raise MaterializationDeliveryError("destination_handler_missing")
                observed_revision = handler(event)
                CrossStoreOutbox(self.session).mark_succeeded(
                    event,
                    observed_revision=observed_revision,
                )
                self.session.commit()
                result["succeeded"] += 1
            except Exception:
                self.session.rollback()
                event = self.session.get(CrossStoreOutboxEvent, event_id)
                if event is not None:
                    CrossStoreOutbox(self.session).mark_failed(
                        event,
                        safe_reason=f"{event.destination}_delivery_failed",
                    )
                    self.session.commit()
                result["failed"] += 1
        return result


class CrossStoreMaterializationWorker:
    """Application-owned polling worker with deterministic shutdown."""

    def __init__(self, app, *, poll_seconds: float = 1.0, batch_size: int = 100):
        self.app = app
        self.poll_seconds = max(0.1, float(poll_seconds))
        self.batch_size = max(1, min(1000, int(batch_size)))
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self, runtime) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(
            target=self._run,
            name="dle-cross-store-materializer",
            daemon=True,
        )
        runtime.track_thread(self._thread)
        self._thread.start()

    def stop(self, timeout_seconds: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(0.1, float(timeout_seconds)))

    def _run(self) -> None:
        from extensions import db

        with self.app.app_context():
            while not self._stop.is_set():
                try:
                    outcome = CrossStoreMaterializationDispatcher(db.session).run_once(
                        limit=self.batch_size
                    )
                    if outcome["claimed"]:
                        logger.info("Cross-store materialization outcome: %s", outcome)
                except Exception:
                    db.session.rollback()
                    logger.exception("Cross-store materialization cycle failed")
                self._stop.wait(self.poll_seconds)
            db.session.remove()
