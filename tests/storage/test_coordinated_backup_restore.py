"""Encrypted coordinated backup, clean-root restore, and rollback tests."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from backend.storage.coordinated_backup import (
    BackupComponent,
    CoordinatedBackupCoordinator,
    CoordinatedBackupError,
)


RECOVERY_SECRET = "owner-controlled-recovery-secret"


class JsonStoreAdapter:
    def __init__(self, name: str, records: dict[str, str], *, fail_export: bool = False):
        self.name = name
        self.records = records
        self.fail_export = fail_export

    def export(self, destination: Path) -> BackupComponent:
        if self.fail_export:
            raise RuntimeError("provider detail must be redacted")
        payload = json.dumps(self.records, sort_keys=True)
        (destination / "records.json").write_text(payload, encoding="utf-8")
        return BackupComponent(
            name=self.name,
            schema_version=f"{self.name}.v1",
            service_version="test-1",
            source_revision="source-7",
            item_count=len(self.records),
            logical_size_bytes=len(payload.encode()),
        )

    def restore(self, source: Path, isolated_root: Path) -> None:
        destination = isolated_root / self.name
        destination.mkdir(parents=True, exist_ok=False)
        shutil.copy2(source / "records.json", destination / "records.json")

    def verify_restore(self, isolated_root: Path, component: BackupComponent):
        payload = json.loads(
            (isolated_root / self.name / "records.json").read_text(encoding="utf-8")
        )
        return {
            "status": "pass" if len(payload) == component.item_count else "fail",
            "item_count": len(payload),
        }


def _coordinator(*, fail_component: str | None = None):
    records = {
        "postgresql": {"entity-1": "sensitive postgres value"},
        "neo4j": {"entity-1": "node-1"},
        "chroma": {"entity-1": "vector-source-1"},
        "redis": {"job-1": "pending"},
        "minio": {"object-1": "sensitive object value"},
        "retained": {"memory-1": "structured memory"},
    }
    adapters = {
        name: JsonStoreAdapter(name, payload, fail_export=name == fail_component)
        for name, payload in records.items()
    }

    def cross_store(root: Path, _manifest):
        restored = {
            name: json.loads((root / name / "records.json").read_text(encoding="utf-8"))
            for name in adapters
        }
        shared = {
            restored[name].get("entity-1") is not None
            for name in ("postgresql", "neo4j", "chroma")
        }
        return {"status": "pass" if shared == {True} else "fail"}

    return CoordinatedBackupCoordinator(
        adapters=adapters,
        product_version="0.1.1",
        migration_versions={name: f"{name}.v1" for name in adapters},
        required_components=tuple(adapters),
        compatibility_check=lambda manifest: manifest["product_version"] == "0.1.1",
        cross_store_verifier=cross_store,
    )


def test_backup_is_encrypted_signed_complete_and_restorable(tmp_path):
    coordinator = _coordinator()
    result = coordinator.create_backup(tmp_path / "backups", recovery_secret=RECOVERY_SECRET)
    archive = Path(result["artifact_path"])

    payload = archive.read_bytes()
    assert b"sensitive postgres value" not in payload
    assert b"sensitive object value" not in payload
    assert result["component_count"] == 6
    assert result["integrity_verified"] is True

    manifest = coordinator.inspect_archive(archive, recovery_secret=RECOVERY_SECRET)
    assert set(manifest["components"]) == set(coordinator.required_components)
    assert len(manifest["signature"]) == 64

    target = tmp_path / "restored-data"
    restored = coordinator.restore_to_clean_root(
        archive,
        target,
        recovery_secret=RECOVERY_SECRET,
    )
    assert restored["status"] == "restored"
    assert restored["cross_store"]["status"] == "pass"
    assert json.loads(
        (target / "postgresql" / "records.json").read_text(encoding="utf-8")
    )["entity-1"] == "sensitive postgres value"


def test_wrong_recovery_secret_and_corruption_fail_closed(tmp_path):
    coordinator = _coordinator()
    result = coordinator.create_backup(tmp_path, recovery_secret=RECOVERY_SECRET)
    archive = Path(result["artifact_path"])

    with pytest.raises(CoordinatedBackupError, match="authentication_failed"):
        coordinator.inspect_archive(archive, recovery_secret="different-owner-secret")

    corrupted = tmp_path / "corrupted.dlebackup"
    data = bytearray(archive.read_bytes())
    data[len(data) // 2] ^= 0x01
    corrupted.write_bytes(data)
    with pytest.raises(CoordinatedBackupError, match="authentication_failed"):
        coordinator.inspect_archive(corrupted, recovery_secret=RECOVERY_SECRET)


def test_partial_export_leaves_no_claimed_backup(tmp_path):
    coordinator = _coordinator(fail_component="neo4j")

    with pytest.raises(CoordinatedBackupError, match="coordinated_backup_failed"):
        coordinator.create_backup(tmp_path, recovery_secret=RECOVERY_SECRET)

    assert not list(tmp_path.glob("*.dlebackup"))
    assert not list(tmp_path.glob(".dle-backup-*"))


def test_failed_post_swap_validation_rolls_back_prior_root(tmp_path):
    coordinator = _coordinator()
    result = coordinator.create_backup(tmp_path / "backups", recovery_secret=RECOVERY_SECRET)
    target = tmp_path / "active-data"
    target.mkdir()
    (target / "prior.txt").write_text("preserve me", encoding="utf-8")

    with pytest.raises(CoordinatedBackupError, match="post_restore_validation_failed"):
        coordinator.restore_to_clean_root(
            result["artifact_path"],
            target,
            recovery_secret=RECOVERY_SECRET,
            post_swap_validator=lambda _root: False,
        )

    assert (target / "prior.txt").read_text(encoding="utf-8") == "preserve me"
    assert not (target / "postgresql").exists()


def test_short_recovery_secret_is_rejected_before_export(tmp_path):
    with pytest.raises(CoordinatedBackupError, match="recovery_secret_too_short"):
        _coordinator().create_backup(tmp_path, recovery_secret="too-short")
