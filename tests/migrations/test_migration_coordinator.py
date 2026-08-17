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


def test_explicit_lossless_upgrade_does_not_claim_or_require_backup(tmp_path):
    adapter = FakeAdapter(version="postgresql.v1", empty=False)
    path = ("postgresql", "postgresql.v1", "postgresql.v2")
    coordinator = MigrationCoordinator(
        adapters={"postgresql": adapter},
        target_versions={"postgresql": "postgresql.v2"},
        supported_paths={path},
        backup_required_paths=set(),
        ledger_path=tmp_path / "ledger.json",
        product_version="4.4.0",
    )

    result = coordinator.run()

    assert adapter.actions == [("migrate", "postgresql.v1", "postgresql.v2")]
    assert result["coordinated_backup_verified"] is False
    assert result["backup_required_stores"] == []


def test_backup_required_path_must_also_be_supported(tmp_path):
    with pytest.raises(ValueError, match="migration_backup_path_not_supported"):
        MigrationCoordinator(
            adapters={"postgresql": FakeAdapter()},
            target_versions={"postgresql": "postgresql.v2"},
            supported_paths=set(),
            backup_required_paths={
                ("postgresql", "postgresql.v1", "postgresql.v2")
            },
            ledger_path=tmp_path / "ledger.json",
            product_version="4.4.0",
        )


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
