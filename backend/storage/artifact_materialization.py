"""One durable persistence boundary for object artifacts."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from flask import has_app_context

from backend.storage.object_store import object_store_is_required
from backend.storage.outbox import CrossStoreOutbox


def persist_object_artifact(
    *,
    entity_type: str,
    entity_id: str,
    bucket: str,
    key: str,
    body: bytes | dict[str, Any] | list[Any],
    schema_version: str,
    content_type: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Queue required object writes transactionally; keep dev/test writes synchronous."""
    if isinstance(body, bytes):
        encoded_body = body
        payload_body: dict[str, Any] = {
            "body_base64": base64.b64encode(body).decode("ascii")
        }
    else:
        encoded_body = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
        payload_body = {"body": body}
    body_hash = hashlib.sha256(encoded_body).hexdigest()
    object_metadata = {str(name): str(value) for name, value in (metadata or {}).items()}
    reference = {
        "bucket": str(bucket),
        "key": str(key),
        "size_bytes": len(encoded_body),
        "body_sha256": body_hash,
    }

    if object_store_is_required():
        if not has_app_context():
            raise RuntimeError("required_object_materialization_context_missing")
        from extensions import db

        try:
            CrossStoreOutbox(db.session).enqueue(
                entity_type=entity_type,
                entity_id=str(entity_id),
                destination="minio",
                operation="put_object",
                schema_version=schema_version,
                source_revision=f"sha256:{body_hash}",
                payload={
                    "bucket": str(bucket),
                    "key": str(key),
                    **payload_body,
                    "body_sha256": body_hash,
                    "content_type": content_type,
                    "metadata": object_metadata,
                },
                correlation_id=str(entity_id),
            )
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError("required_object_materialization_enqueue_failed") from exc
        return {**reference, "status": "pending"}

    from backend.storage import get_object_store

    store = get_object_store()
    if not store.create_bucket(bucket):
        raise RuntimeError("object_artifact_bucket_unavailable")
    stored_key = store.put(
        bucket,
        key,
        encoded_body,
        content_type=content_type,
        metadata=object_metadata,
    )
    if str(stored_key) != str(key) or not store.exists(bucket, key):
        raise RuntimeError("object_artifact_write_verification_failed")
    if hashlib.sha256(store.get(bucket, key)).hexdigest() != body_hash:
        raise RuntimeError("object_artifact_hash_verification_failed")
    return {**reference, "status": "ready"}
