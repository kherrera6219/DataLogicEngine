"""Offline clean-root restore activation, rollback, and runtime-lock tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.runtime.ownership import InstallationIdentity, RuntimeLock
from backend.storage.coordinated_backup import CoordinatedBackupError
from backend.storage.managed_restore import restore_managed_backup_offline
from tests.storage.test_coordinated_backup_restore import (
    RECOVERY_SECRET,
    JsonStoreAdapter,
    _coordinator,
)


class FakeRestoreEnvironment:
    def __init__(self):
        self.adapters = {
            name: JsonStoreAdapter(name, {})
            for name in ("postgresql", "redis", "neo4j", "chroma", "minio", "retained")
        }
        self.root = None
        self.closed_with = None

    def adapter(self, name, isolated_root):
        if self.root is None:
            self.root = isolated_root
            InstallationIdentity.load_or_create(
                isolated_root / "installation.json",
                version="0.1.1",
            )
        return self.adapters[name]

    def verify_cross_store(self, isolated_root, manifest):
        return {
            "status": "pass",
            "verified_components": sorted(manifest["components"]),
            "root": str(isolated_root),
        }

    def close(self, *, success):
        self.closed_with = success


def _restore(archive, target, environment, **kwargs):
    return restore_managed_backup_offline(
        archive,
        target,
        recovery_secret=RECOVERY_SECRET,
        product_version="0.1.1",
        lock_path="unused-by-fake-environment.json",
        environment_factory=lambda: environment,
        **kwargs,
    )


def test_offline_restore_activates_new_identity_and_preserves_prior_root(tmp_path):
    backup = _coordinator().create_backup(
        tmp_path / "backups",
        recovery_secret=RECOVERY_SECRET,
    )
    target = tmp_path / "active-runtime"
    original = InstallationIdentity.load_or_create(
        target / "installation.json",
        version="0.1.1",
    )
    (target / "prior.txt").write_text("prior generation", encoding="utf-8")
    environment = FakeRestoreEnvironment()

    result = _restore(backup["artifact_path"], target, environment)

    restored_identity = json.loads(
        (target / "installation.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "restored"
    assert result["activation"] == "restart_application"
    assert result["cross_store"]["status"] == "pass"
    assert restored_identity["installation_id"] != original.installation_id
    assert result["prior_root"]
    assert (Path(result["prior_root"]) / "prior.txt").read_text(encoding="utf-8") == (
        "prior generation"
    )
    assert environment.closed_with is True


def test_offline_restore_refuses_target_held_by_running_application(tmp_path):
    backup = _coordinator().create_backup(
        tmp_path / "backups",
        recovery_secret=RECOVERY_SECRET,
    )
    target = tmp_path / "locked-runtime"
    identity = InstallationIdentity.load_or_create(
        target / "installation.json",
        version="0.1.1",
    )
    lock = RuntimeLock(target / "runtime.lock", identity)
    lock.acquire()
    try:
        with pytest.raises(CoordinatedBackupError, match="restore_target_application_running"):
            _restore(backup["artifact_path"], target, FakeRestoreEnvironment())
    finally:
        lock.release()


def test_offline_restore_rolls_back_prior_root_after_post_swap_failure(tmp_path):
    backup = _coordinator().create_backup(
        tmp_path / "backups",
        recovery_secret=RECOVERY_SECRET,
    )
    target = tmp_path / "rollback-runtime"
    InstallationIdentity.load_or_create(target / "installation.json", version="0.1.1")
    (target / "prior.txt").write_text("preserved", encoding="utf-8")
    environment = FakeRestoreEnvironment()

    with pytest.raises(CoordinatedBackupError, match="post_restore_validation_failed"):
        _restore(
            backup["artifact_path"],
            target,
            environment,
            post_swap_validator=lambda _root: False,
        )

    assert (target / "prior.txt").read_text(encoding="utf-8") == "preserved"
    assert environment.closed_with is False
