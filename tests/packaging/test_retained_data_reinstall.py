"""Retained AppData reinstall and explicit uninstall disposition contracts."""

from __future__ import annotations

import json

import pytest

from backend.runtime.ownership import InstallationIdentity
from backend.storage.store_migration_adapters import LocalJsonMemoryMigrationAdapter
from backend.storage.uninstall_retention import (
    UninstallRetentionError,
    apply_uninstall_data_choice,
)


def _retained_runtime(tmp_path, name="runtime"):
    root = tmp_path / name
    identity = InstallationIdentity.load_or_create(
        root / "installation.json",
        version="0.1.1",
    )
    memory_path = root / "databases" / "memory" / "memory_graph.json"
    memory_path.parent.mkdir(parents=True)
    memory_path.write_text(
        json.dumps(
            {
                "version": 1,
                "vertices": [{"vertex_id": "retained-node", "metadata": {}}],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    return root, identity, memory_path


def test_keep_data_reinstall_preserves_identity_and_versioned_memory(tmp_path):
    root, original, memory_path = _retained_runtime(tmp_path)

    outcome = apply_uninstall_data_choice(root, "keep")
    reinstalled = InstallationIdentity.load_or_create(
        root / "installation.json",
        version="0.1.1",
    )
    adapter = LocalJsonMemoryMigrationAdapter(memory_path)

    assert outcome["data_retained"] is True
    assert reinstalled.installation_id == original.installation_id
    assert adapter.probe_version() == "unified-memory.v1"
    assert json.loads(memory_path.read_text(encoding="utf-8"))["vertices"][0][
        "vertex_id"
    ] == "retained-node"


def test_export_then_delete_requires_verified_portable_backup(tmp_path):
    root, _identity, _memory_path = _retained_runtime(tmp_path)
    archive = tmp_path / "recovery.dlebackup"
    archive.write_bytes(b"encrypted-recovery-set")

    with pytest.raises(UninstallRetentionError, match="verified_uninstall_backup_required"):
        apply_uninstall_data_choice(root, "export_then_delete", backup_path=archive)

    outcome = apply_uninstall_data_choice(
        root,
        "export_then_delete",
        backup_path=archive,
        backup_verifier=lambda path: path.read_bytes() == b"encrypted-recovery-set",
    )

    assert outcome["data_retained"] is False
    assert outcome["secure_delete_guaranteed"] is False
    assert not root.exists()


def test_delete_choice_is_bounded_and_discloses_residual_storage_risk(tmp_path):
    root, _identity, _memory_path = _retained_runtime(tmp_path, "delete-runtime")

    outcome = apply_uninstall_data_choice(root, "delete")

    assert not root.exists()
    assert outcome["residual_risk"] == "ssd_snapshot_or_backup_remnants_may_persist"
    assert outcome["secure_delete_guaranteed"] is False


def test_uninstall_refuses_unowned_directory(tmp_path):
    unowned = tmp_path / "unowned"
    unowned.mkdir()

    with pytest.raises(UninstallRetentionError, match="uninstall_runtime_identity_invalid"):
        apply_uninstall_data_choice(unowned, "delete")
