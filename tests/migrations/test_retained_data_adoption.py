"""Retained desktop data discovery, backup, and adoption regressions."""

from __future__ import annotations

import json
import sqlite3

import pytest
from sqlalchemy import Column, Integer, JSON, MetaData, String, Table, create_engine, select

from backend.runtime.data_plane_delivery import DataPlaneCredentialVault
from backend.runtime.ownership import RuntimeOwnership
from backend.storage.legacy_sqlite_adoption import (
    LegacyAdoptionError,
    build_sqlite_adoption_plan,
    create_verified_sqlite_recovery_copy,
    import_legacy_objects,
    import_sqlite_rows,
    synchronize_postgresql_sequences,
)
from backend.storage.retained_data import discover_retained_data
from app import _runtime_encryption_key_root


def _legacy_sqlite(path):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL)")
    connection.execute("INSERT INTO users (id, username) VALUES (1, 'owner')")
    connection.commit()
    connection.close()


def test_retained_app_owned_keyring_remains_authoritative(tmp_path):
    retained = tmp_path / "data" / "security" / "keys"
    retained.mkdir(parents=True)
    (retained / "kek.salt").write_bytes(b"s" * 32)
    (retained / "dek_registry.json").write_text("{}", encoding="utf-8")

    assert _runtime_encryption_key_root(tmp_path) == retained


def test_new_install_uses_canonical_keyring_location(tmp_path):
    assert _runtime_encryption_key_root(tmp_path) == tmp_path / "security" / "keys"


def test_discovery_classifies_retained_sqlite_before_identity_mutation(tmp_path):
    source = tmp_path / "ukg_database.db"
    _legacy_sqlite(source)
    (tmp_path / "installation.json").write_text(
        json.dumps(
            {
                "installation_id": "a" * 32,
                "owner": __import__("getpass").getuser(),
                "platform": "Windows-test",
                "product": "DataLogicEngine",
                "version": "4.3.0",
            }
        ),
        encoding="utf-8",
    )

    result = discover_retained_data(tmp_path)

    assert result["legacy_retained_data_present"] is True
    assert result["requires_adoption"] is True
    assert result["source_version"] == "0.1.1"
    assert result["surfaces"]["sqlite"]["meaningful_record_count"] == 1


def test_verified_recovery_copy_keeps_adoption_receipt_valid_after_wal_drift(tmp_path):
    source = tmp_path / "ukg_database.db"
    _legacy_sqlite(source)
    source_sha = __import__("hashlib").sha256(source.name.encode() + source.read_bytes()).hexdigest()
    backup = tmp_path / "recovery" / "retained-data" / f"ukg-database-{source_sha[:16]}.sqlite3"
    backup.parent.mkdir(parents=True)
    backup.write_bytes(source.read_bytes())
    backup_sha = __import__("hashlib").sha256(backup.read_bytes()).hexdigest()
    receipt = tmp_path / "migrations" / "retained-data-adoption.json"
    receipt.parent.mkdir()
    receipt.write_text(
        json.dumps(
            {
                "schema_version": "dle.retained-data-adoption.v1",
                "status": "verified",
                "source_sha256": source_sha,
                "backup_sha256": backup_sha,
                "graph": {},
            }
        ),
        encoding="utf-8",
    )
    # Add a WAL-shaped sidecar so the live byte digest no longer equals the
    # receipt while the immutable verified recovery copy remains unchanged.
    (tmp_path / "ukg_database.db-wal").write_bytes(b"post-adoption-wal-drift")

    result = discover_retained_data(tmp_path)

    assert result["adoption_receipt_valid"] is True
    assert result["requires_adoption"] is False


def test_runtime_identity_is_prepared_in_memory_and_persisted_only_after_lock(tmp_path):
    ownership = RuntimeOwnership(tmp_path, version="4.3.0")

    prepared = ownership.prepare(initial_version="0.1.1")

    assert prepared.version == "0.1.1"
    assert not ownership.identity_path.exists()
    ownership.acquire()
    try:
        assert ownership.identity_path.is_file()
        assert json.loads(ownership.identity_path.read_text(encoding="utf-8"))["version"] == "0.1.1"
    finally:
        ownership.release()


def test_credential_vault_can_prepare_without_writing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "backend.runtime.data_plane_delivery.encrypt_data",
        lambda value: f"protected-{value}",
    )
    monkeypatch.setattr(
        "backend.runtime.data_plane_delivery.decrypt_data",
        lambda value: value.removeprefix("protected-"),
    )
    monkeypatch.setattr(
        "backend.runtime.data_plane_delivery.ensure_restricted_user_acl",
        lambda *_args, **_kwargs: True,
    )
    path = tmp_path / "security" / "credentials.json"
    vault = DataPlaneCredentialVault(path, require_dpapi=True)

    prepared = vault.load_or_prepare("b" * 32)

    assert prepared
    assert not path.exists()
    persisted = vault.persist_prepared("b" * 32)
    assert persisted == prepared
    assert path.is_file()


def test_sqlite_adoption_requires_backup_and_preserves_source(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "backend.storage.legacy_sqlite_adoption.ensure_restricted_user_acl",
        lambda *_args, **_kwargs: True,
    )
    source = tmp_path / "ukg_database.db"
    _legacy_sqlite(source)
    source_before = source.read_bytes()
    target = create_engine(f"sqlite:///{tmp_path / 'target.sqlite3'}")
    metadata = MetaData()
    users = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("username", String, nullable=False),
        Column("optional_current_field", String, nullable=True),
    )
    metadata.create_all(target)

    plan = build_sqlite_adoption_plan(source, target)
    backup = create_verified_sqlite_recovery_copy(source, tmp_path / "recovery.sqlite3")
    imported = import_sqlite_rows(source, target, plan=plan)
    repeated = import_sqlite_rows(source, target, plan=plan)

    assert plan["ready"] is True
    assert backup["integrity"] == "ok"
    assert imported == {"users": 1}
    assert repeated == imported
    with target.connect() as connection:
        assert connection.execute(select(users.c.id, users.c.username)).one() == (1, "owner")
    assert source.read_bytes() == source_before


def test_sequence_synchronization_is_a_postgresql_only_operation(tmp_path):
    target = create_engine(f"sqlite:///{tmp_path / 'target.sqlite3'}")

    assert synchronize_postgresql_sequences(target) == {}


def test_adoption_disables_legacy_provider_ciphertext_and_adds_usage_contract(tmp_path):
    source = tmp_path / "ukg_database.db"
    connection = sqlite3.connect(source)
    connection.execute(
        "CREATE TABLE llm_providers ("
        "id UUID PRIMARY KEY, name TEXT NOT NULL, provider_type TEXT NOT NULL, "
        "api_key_encrypted BLOB, is_active BOOLEAN, is_default BOOLEAN)"
    )
    connection.execute(
        "CREATE TABLE llm_provider_usage ("
        "id UUID PRIMARY KEY, provider_id UUID NOT NULL, success BOOLEAN)"
    )
    provider_id = "611300354a7e43c8b257856d748f72bc"
    usage_id = "711300354a7e43c8b257856d748f72bc"
    connection.execute(
        "INSERT INTO llm_providers VALUES (?, 'OpenAI', 'openai', ?, 1, 1)",
        (provider_id, b"legacy-ciphertext"),
    )
    connection.execute(
        "INSERT INTO llm_provider_usage VALUES (?, ?, 0)",
        (usage_id, provider_id),
    )
    connection.commit()
    connection.close()

    target = create_engine(f"sqlite:///{tmp_path / 'target.sqlite3'}")
    metadata = MetaData()
    providers = Table(
        "llm_providers",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String, nullable=False),
        Column("provider_type", String, nullable=False),
        Column("api_key_encrypted", String),
        Column("is_active", Integer),
        Column("is_default", Integer),
    )
    usage = Table(
        "llm_provider_usage",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("provider_id", String(36), nullable=False),
        Column("success", Integer),
        Column("provider_type", String, nullable=False),
        Column("purpose", String, nullable=False),
        Column("request_stage", String, nullable=False),
        Column("attempt_number", Integer, nullable=False),
        Column("retry_index", Integer, nullable=False),
        Column("pricing_status", String, nullable=False),
        Column("status", String, nullable=False),
        Column("disclosed_categories", JSON, nullable=False),
    )
    metadata.create_all(target)

    plan = build_sqlite_adoption_plan(source, target)
    imported = import_sqlite_rows(source, target, plan=plan)

    assert imported == {"llm_providers": 1, "llm_provider_usage": 1}
    with target.connect() as db_connection:
        provider = db_connection.execute(select(providers)).mappings().one()
        record = db_connection.execute(select(usage)).mappings().one()
    assert provider["api_key_encrypted"] is None
    assert provider["is_active"] == 0
    assert provider["is_default"] == 0
    assert record["provider_type"] == "legacy"
    assert record["status"] == "failed"


def test_sqlite_adoption_blocks_unknown_populated_table(tmp_path):
    source = tmp_path / "ukg_database.db"
    _legacy_sqlite(source)
    target = create_engine(f"sqlite:///{tmp_path / 'target.sqlite3'}")

    plan = build_sqlite_adoption_plan(source, target)

    assert plan["ready"] is False
    assert "target_table_missing:users" in plan["blockers"]
    with pytest.raises(LegacyAdoptionError, match="retained_sqlite_plan_blocked"):
        import_sqlite_rows(source, target, plan=plan)


def test_legacy_object_import_verifies_hash_and_skips_metadata_sidecars(tmp_path):
    root = tmp_path / "objects"
    source = root / "deliverables" / "result.json"
    source.parent.mkdir(parents=True)
    source.write_bytes(b'{"status":"complete"}')
    source.with_suffix(".json.meta").write_text("{}", encoding="utf-8")

    class Store:
        def __init__(self):
            self.values = {}

        def put(self, bucket, key, data, **_kwargs):
            self.values[(bucket, key)] = data

        def get(self, bucket, key):
            return self.values[(bucket, key)]

    store = Store()
    result = import_legacy_objects(root, store)

    assert result["object_count"] == 1
    assert ("deliverables", "result.json") in store.values
