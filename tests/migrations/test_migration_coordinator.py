"""Fail-closed multi-store migration coordinator tests."""

from __future__ import annotations

import json

import pytest

from backend.storage.migration_coordinator import (
    MigrationCoordinator,
    MigrationCoordinatorError,
)


class FakeAdapter:
    def __init__(self, version=None, *, empty=True):
        self.version = version
        self.empty = empty
        self.actions = []

    def probe_version(self):
        return self.version

    def is_empty(self):
        return self.empty

    def bootstrap(self, target_version):
        self.actions.append(("bootstrap", target_version))
        self.version = target_version
        self.empty = False

    def migrate(self, current_version, target_version):
        self.actions.append(("migrate", current_version, target_version))
        self.version = target_version


def test_fresh_stores_bootstrap_without_claiming_a_backup(tmp_path):
    adapters = {name: FakeAdapter() for name in ("postgresql", "redis", "neo4j")}
    backup_calls = []
    coordinator = MigrationCoordinator(
        adapters=adapters,
        target_versions={name: f"{name}.v1" for name in adapters},
        ledger_path=tmp_path / "migration-ledger.json",
        product_version="0.1.1",
        backup_verifier=lambda: backup_calls.append(True) or True,
    )

    result = coordinator.run()

    assert result["status"] == "ready"
    assert backup_calls == []
    assert all(adapter.actions == [("bootstrap", f"{name}.v1")] for name, adapter in adapters.items())
    persisted = json.loads((tmp_path / "migration-ledger.json").read_text(encoding="utf-8"))
    assert persisted["status"] == "ready"
    assert "password" not in json.dumps(persisted).lower()


def test_populated_unversioned_store_fails_without_mutation(tmp_path):
    adapter = FakeAdapter(version=None, empty=False)
    coordinator = MigrationCoordinator(
        adapters={"redis": adapter},
        target_versions={"redis": "redis.v1"},
        ledger_path=tmp_path / "ledger.json",
        product_version="0.1.1",
    )

    with pytest.raises(MigrationCoordinatorError, match="unversioned_data:redis"):
        coordinator.run()

    assert adapter.actions == []
    assert not (tmp_path / "ledger.json").exists()


def test_destructive_upgrade_requires_verified_coordinated_backup(tmp_path):
    adapter = FakeAdapter(version="redis.v0", empty=False)
    coordinator = MigrationCoordinator(
        adapters={"redis": adapter},
        target_versions={"redis": "redis.v1"},
        supported_paths={("redis", "redis.v0", "redis.v1")},
        ledger_path=tmp_path / "ledger.json",
        product_version="0.1.1",
        backup_verifier=lambda: False,
    )

    with pytest.raises(MigrationCoordinatorError, match="coordinated_backup_required"):
        coordinator.run()

    assert adapter.actions == []


def test_verified_upgrade_runs_once_and_rechecks_target(tmp_path):
    adapter = FakeAdapter(version="neo4j.v0", empty=False)
    calls = []
    coordinator = MigrationCoordinator(
        adapters={"neo4j": adapter},
        target_versions={"neo4j": "neo4j.v1"},
        supported_paths={("neo4j", "neo4j.v0", "neo4j.v1")},
        ledger_path=tmp_path / "ledger.json",
        product_version="0.1.1",
        backup_verifier=lambda: calls.append("verified") or True,
    )

    result = coordinator.run()

    assert calls == ["verified"]
    assert adapter.actions == [("migrate", "neo4j.v0", "neo4j.v1")]
    assert result["stores"]["neo4j"]["observed_version"] == "neo4j.v1"


def test_unknown_or_newer_version_is_not_downgraded(tmp_path):
    adapter = FakeAdapter(version="chroma.v99", empty=False)
    coordinator = MigrationCoordinator(
        adapters={"chroma": adapter},
        target_versions={"chroma": "chroma.v1"},
        ledger_path=tmp_path / "ledger.json",
        product_version="0.1.1",
    )

    with pytest.raises(MigrationCoordinatorError, match="unsupported_data_version:chroma"):
        coordinator.run()

    assert adapter.actions == []
