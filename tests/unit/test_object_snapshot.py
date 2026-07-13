from __future__ import annotations

import json

import pytest

from backend.storage.object_snapshot import (
    SnapshotIntegrityError,
    export_bucket,
    migrate_bucket,
    restore_bucket,
    verify_snapshot,
)
from backend.storage.object_store import LocalFileBackend


def _seed(backend: LocalFileBackend, bucket: str = "qualification") -> None:
    assert backend.create_bucket(bucket) is True
    backend.put(
        bucket,
        "traces/run-1.json",
        b'{"status":"complete"}',
        content_type="application/json",
        metadata={"sha256": "caller-hash", "owner": "trace-1"},
    )
    backend.put(
        bucket,
        "artifacts/result.bin",
        bytes(range(256)) * 4,
        content_type="application/octet-stream",
        metadata={"retention": "qualification"},
    )


def test_portable_snapshot_round_trip_preserves_contract(tmp_path):
    source = LocalFileBackend(str(tmp_path / "source"))
    target = LocalFileBackend(str(tmp_path / "target"))
    _seed(source)

    snapshot = tmp_path / "snapshot"
    exported = export_bucket(source, "qualification", snapshot)
    verified = verify_snapshot(snapshot)
    restored = restore_bucket(target, snapshot)

    assert exported.object_count == verified.object_count == restored.object_count == 2
    assert exported.total_bytes == verified.total_bytes == restored.total_bytes
    assert target.get("qualification", "traces/run-1.json") == b'{"status":"complete"}'
    info = target.get_info("qualification", "traces/run-1.json")
    assert info is not None
    assert info.content_type == "application/json"
    assert info.metadata == {"owner": "trace-1", "sha256": "caller-hash"}


def test_snapshot_rejects_manifest_and_blob_tampering(tmp_path):
    source = LocalFileBackend(str(tmp_path / "source"))
    _seed(source)
    snapshot = tmp_path / "snapshot"
    export_bucket(source, "qualification", snapshot)

    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    digest = manifest["objects"][0]["sha256"]
    (snapshot / "blobs" / digest[:2] / digest).write_bytes(b"tampered")

    with pytest.raises(SnapshotIntegrityError, match="snapshot_blob_integrity_failure"):
        verify_snapshot(snapshot)


def test_migration_artifact_supports_verified_rollback(tmp_path):
    original = LocalFileBackend(str(tmp_path / "original"))
    candidate = LocalFileBackend(str(tmp_path / "candidate"))
    rollback = LocalFileBackend(str(tmp_path / "rollback"))
    _seed(original)

    migration_snapshot = tmp_path / "migration"
    migrated = migrate_bucket(original, candidate, "qualification", migration_snapshot)
    rollback_snapshot = tmp_path / "rollback-snapshot"
    rolled_back = migrate_bucket(candidate, rollback, "qualification", rollback_snapshot)

    assert migrated.object_count == rolled_back.object_count == 2
    assert rollback.get("qualification", "artifacts/result.bin") == bytes(range(256)) * 4
