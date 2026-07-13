"""Portable, vendor-neutral object-store snapshot and migration helpers.

The snapshot format is intentionally based on the ``ObjectBackend`` contract,
not a vendor data directory. This keeps backup/restore and replacement rollback
testable across the local staging backend and any qualified S3 implementation.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.storage.object_store import ObjectBackend


SNAPSHOT_SCHEMA_VERSION = "1.0.0"


class SnapshotIntegrityError(RuntimeError):
    """Raised when a snapshot or restored object fails integrity validation."""


@dataclass(frozen=True, slots=True)
class SnapshotSummary:
    bucket: str
    object_count: int
    total_bytes: int
    manifest_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "bucket": self.bucket,
            "object_count": self.object_count,
            "total_bytes": self.total_bytes,
            "manifest_sha256": self.manifest_sha256,
        }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _read_manifest(snapshot_root: Path) -> tuple[dict[str, Any], str]:
    manifest_path = snapshot_root / "manifest.json"
    digest_path = snapshot_root / "manifest.sha256"
    try:
        manifest_bytes = manifest_path.read_bytes()
        expected_digest = digest_path.read_text(encoding="ascii").strip().lower()
    except OSError as exc:
        raise SnapshotIntegrityError("snapshot_manifest_missing") from exc

    actual_digest = _sha256(manifest_bytes)
    if actual_digest != expected_digest:
        raise SnapshotIntegrityError("snapshot_manifest_hash_mismatch")

    try:
        manifest = json.loads(manifest_bytes)
    except (TypeError, ValueError) as exc:
        raise SnapshotIntegrityError("snapshot_manifest_invalid_json") from exc
    if not isinstance(manifest, dict):
        raise SnapshotIntegrityError("snapshot_manifest_invalid_type")
    if manifest.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotIntegrityError("snapshot_schema_unsupported")
    return manifest, actual_digest


def export_bucket(
    backend: ObjectBackend,
    bucket: str,
    snapshot_root: str | Path,
) -> SnapshotSummary:
    """Export one bucket to a content-addressed portable snapshot."""

    root = Path(snapshot_root).resolve()
    blobs_root = root / "blobs"
    blobs_root.mkdir(parents=True, exist_ok=True)

    objects: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    total_bytes = 0
    for listed in backend.list(bucket):
        if listed.key in seen_keys:
            raise SnapshotIntegrityError("source_contains_duplicate_key")
        seen_keys.add(listed.key)

        data = backend.get(bucket, listed.key)
        digest = _sha256(data)
        blob_path = blobs_root / digest[:2] / digest
        if blob_path.exists():
            if _sha256(blob_path.read_bytes()) != digest:
                raise SnapshotIntegrityError("snapshot_blob_collision")
        else:
            _atomic_write(blob_path, data)

        info = backend.get_info(bucket, listed.key) or listed
        last_modified = info.last_modified
        if last_modified.tzinfo is None:
            last_modified = last_modified.replace(tzinfo=UTC)
        objects.append(
            {
                "key": listed.key,
                "size": len(data),
                "sha256": digest,
                "content_type": info.content_type or "application/octet-stream",
                "metadata": {str(k): str(v) for k, v in sorted(info.metadata.items())},
                "last_modified": last_modified.astimezone(UTC).isoformat(),
            }
        )
        total_bytes += len(data)

    objects.sort(key=lambda item: item["key"])
    manifest = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "bucket": bucket,
        "object_count": len(objects),
        "total_bytes": total_bytes,
        "objects": objects,
    }
    manifest_bytes = _canonical_json(manifest)
    manifest_digest = _sha256(manifest_bytes)
    _atomic_write(root / "manifest.json", manifest_bytes)
    _atomic_write(root / "manifest.sha256", f"{manifest_digest}\n".encode("ascii"))
    return SnapshotSummary(bucket, len(objects), total_bytes, manifest_digest)


def verify_snapshot(snapshot_root: str | Path) -> SnapshotSummary:
    """Verify manifest identity, object uniqueness, blob hashes, and byte counts."""

    root = Path(snapshot_root).resolve()
    manifest, manifest_digest = _read_manifest(root)
    bucket = str(manifest.get("bucket") or "")
    objects = manifest.get("objects")
    if not bucket or not isinstance(objects, list):
        raise SnapshotIntegrityError("snapshot_manifest_contract_invalid")

    seen_keys: set[str] = set()
    total_bytes = 0
    for item in objects:
        if not isinstance(item, dict):
            raise SnapshotIntegrityError("snapshot_object_entry_invalid")
        key = str(item.get("key") or "")
        digest = str(item.get("sha256") or "").lower()
        expected_size = item.get("size")
        if not key or key in seen_keys:
            raise SnapshotIntegrityError("snapshot_object_key_invalid")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise SnapshotIntegrityError("snapshot_object_hash_invalid")
        if not isinstance(expected_size, int) or expected_size < 0:
            raise SnapshotIntegrityError("snapshot_object_size_invalid")
        seen_keys.add(key)

        blob_path = root / "blobs" / digest[:2] / digest
        try:
            data = blob_path.read_bytes()
        except OSError as exc:
            raise SnapshotIntegrityError("snapshot_blob_missing") from exc
        if len(data) != expected_size or _sha256(data) != digest:
            raise SnapshotIntegrityError("snapshot_blob_integrity_failure")
        total_bytes += len(data)

    if manifest.get("object_count") != len(objects):
        raise SnapshotIntegrityError("snapshot_object_count_mismatch")
    if manifest.get("total_bytes") != total_bytes:
        raise SnapshotIntegrityError("snapshot_total_bytes_mismatch")
    return SnapshotSummary(bucket, len(objects), total_bytes, manifest_digest)


def restore_bucket(
    backend: ObjectBackend,
    snapshot_root: str | Path,
    *,
    target_bucket: str | None = None,
) -> SnapshotSummary:
    """Restore and read back every object before reporting success."""

    root = Path(snapshot_root).resolve()
    summary = verify_snapshot(root)
    manifest, manifest_digest = _read_manifest(root)
    bucket = target_bucket or summary.bucket
    backend.create_bucket(bucket)

    for item in manifest["objects"]:
        digest = item["sha256"]
        data = (root / "blobs" / digest[:2] / digest).read_bytes()
        backend.put(
            bucket,
            item["key"],
            data,
            content_type=item["content_type"],
            metadata=dict(item["metadata"]),
        )
        restored = backend.get(bucket, item["key"])
        if _sha256(restored) != digest:
            raise SnapshotIntegrityError("restored_object_hash_mismatch")
        info = backend.get_info(bucket, item["key"])
        if info is None or info.size != item["size"]:
            raise SnapshotIntegrityError("restored_object_metadata_missing")
        if info.content_type != item["content_type"]:
            raise SnapshotIntegrityError("restored_object_content_type_mismatch")
        for key, value in item["metadata"].items():
            if info.metadata.get(key) != value:
                raise SnapshotIntegrityError("restored_object_metadata_mismatch")

    restored_keys = {item.key for item in backend.list(bucket)}
    expected_keys = {item["key"] for item in manifest["objects"]}
    if restored_keys != expected_keys:
        raise SnapshotIntegrityError("restored_bucket_key_mismatch")
    return SnapshotSummary(bucket, summary.object_count, summary.total_bytes, manifest_digest)


def migrate_bucket(
    source: ObjectBackend,
    target: ObjectBackend,
    bucket: str,
    working_root: str | Path,
) -> SnapshotSummary:
    """Migrate through the portable format so the same artifact enables rollback."""

    summary = export_bucket(source, bucket, working_root)
    restored = restore_bucket(target, working_root, target_bucket=bucket)
    if restored.object_count != summary.object_count or restored.total_bytes != summary.total_bytes:
        raise SnapshotIntegrityError("migration_summary_mismatch")
    return restored
