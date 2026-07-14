"""One durable persistence boundary for object artifacts."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
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
    body: bytes | dict[str, Any] | list[Any] | None = None,
    body_path: str | Path | None = None,
    schema_version: str,
    content_type: str,
    metadata: dict[str, Any] | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    """Queue required object writes transactionally; keep dev/test writes synchronous."""
    if (body is None) == (body_path is None):
        raise ValueError("object_artifact_requires_exactly_one_body_source")
    if body_path is not None:
        spool_path = Path(body_path).expanduser().resolve()
        digest = hashlib.sha256()
        size_bytes = 0
        with spool_path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                size_bytes += len(chunk)
                digest.update(chunk)
        encoded_body = None
        body_hash = digest.hexdigest()
        payload_body = {"body_path": str(spool_path)}
    elif isinstance(body, bytes):
        encoded_body = body
        payload_body: dict[str, Any] = {
            "body_base64": base64.b64encode(body).decode("ascii")
        }
        body_hash = hashlib.sha256(encoded_body).hexdigest()
        size_bytes = len(encoded_body)
    else:
        encoded_body = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
        payload_body = {"body": body}
        body_hash = hashlib.sha256(encoded_body).hexdigest()
        size_bytes = len(encoded_body)
    object_metadata = {str(name): str(value) for name, value in (metadata or {}).items()}
    reference = {
        "bucket": str(bucket),
        "key": str(key),
        "size_bytes": size_bytes,
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
            if commit:
                db.session.commit()
            else:
                db.session.flush()
        except Exception as exc:
            db.session.rollback()
            raise RuntimeError("required_object_materialization_enqueue_failed") from exc
        return {**reference, "status": "pending"}

    if encoded_body is None:
        encoded_body = Path(str(body_path)).read_bytes()

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
