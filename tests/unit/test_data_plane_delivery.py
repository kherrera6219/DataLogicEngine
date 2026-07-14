from __future__ import annotations

import base64
import json

import pytest

from backend.runtime import data_plane_delivery as delivery


LOCK_PATH = "deploy/internal-data-plane.candidate-lock.json"
INSTALLATION_ID = "0123456789abcdef0123456789abcdef"


def test_candidate_lock_is_immutable_and_not_self_approved():
    payload, artifacts = delivery.load_candidate_lock(LOCK_PATH)

    assert payload["production_provisioning_authorized"] is False
    assert payload["architecture_change_authorized"] is False
    assert set(artifacts) == set(delivery.REQUIRED_SERVICES)
    assert all("@sha256:" in artifact.image for artifact in artifacts.values())
    assert all(artifact.production_approved is False for artifact in artifacts.values())


def test_qualification_plan_has_stable_isolated_names_ports_and_limits():
    first = delivery.build_delivery_plan(
        LOCK_PATH,
        INSTALLATION_ID,
        profile="qualification",
    )
    second = delivery.build_delivery_plan(
        LOCK_PATH,
        INSTALLATION_ID,
        profile="qualification",
    )

    assert first == second
    assert first.production_authorized is False
    assert first.network_name == "dle-0123456789ab-internal"
    ports = [port for service in first.services for port in service.host_ports]
    assert len(ports) == len(set(ports))
    assert all(20000 <= port <= 29999 for port in ports)
    assert all(service.host == "127.0.0.1" for service in first.services)
    assert all(service.memory_bytes > 0 for service in first.services)
    assert all(service.pids_limit > 0 for service in first.services)


def test_production_plan_fails_closed_until_every_artifact_is_approved():
    with pytest.raises(
        delivery.DataPlaneDeliveryError,
        match="production_data_plane_not_approved",
    ):
        delivery.build_delivery_plan(
            LOCK_PATH,
            INSTALLATION_ID,
            profile="production",
        )


def test_generated_credentials_are_unique_and_reject_known_defaults():
    credentials = delivery.generate_service_credentials()
    values = [
        value
        for credential in credentials.values()
        for value in credential.secret_values()
    ]

    assert len(values) == len(set(values))
    assert all(len(value) >= 32 for value in values)
    assert not {value.lower() for value in values} & delivery.KNOWN_DEFAULT_SECRETS
    assert credentials["object_store_app"].access_key.startswith("DLEAPP")
    assert credentials["object_store_bootstrap"].access_key.startswith("DLEBOOT")
    assert credentials["redis_recovery"].username == "dle_recovery"
    assert credentials["redis_recovery"].password != credentials["redis"].password


def test_credential_vault_is_encrypted_installation_bound_and_atomic(tmp_path, monkeypatch):
    def encrypt(value: str) -> str:
        return base64.b64encode(value.encode()).decode()

    def decrypt(value: str) -> str:
        return base64.b64decode(value.encode()).decode()

    monkeypatch.setattr(delivery, "encrypt_data", encrypt)
    monkeypatch.setattr(delivery, "decrypt_data", decrypt)
    monkeypatch.setattr(delivery, "ensure_restricted_user_acl", lambda *_a, **_k: True)

    path = tmp_path / "credentials.json"
    vault = delivery.DataPlaneCredentialVault(path)
    created = vault.load_or_create(INSTALLATION_ID)
    persisted = path.read_text(encoding="utf-8")
    loaded = vault.load_or_create(INSTALLATION_ID)

    assert created == loaded
    assert "dpapi:v1:" in persisted
    assert all(
        secret not in persisted
        for credential in created.values()
        for secret in credential.secret_values()
    )
    assert not list(tmp_path.glob("*.tmp"))

    payload = json.loads(persisted)
    payload["installation_id"] = "f" * 32
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(
        delivery.DataPlaneDeliveryError,
        match="credential_vault_installation_mismatch",
    ):
        vault.load_or_create(INSTALLATION_ID)


def test_legacy_vault_adds_recovery_identity_without_rotating_existing_secrets(
    tmp_path,
    monkeypatch,
):
    def encrypt(value: str) -> str:
        return base64.b64encode(value.encode()).decode()

    def decrypt(value: str) -> str:
        return base64.b64decode(value.encode()).decode()

    monkeypatch.setattr(delivery, "encrypt_data", encrypt)
    monkeypatch.setattr(delivery, "decrypt_data", decrypt)
    monkeypatch.setattr(delivery, "ensure_restricted_user_acl", lambda *_a, **_k: True)
    path = tmp_path / "legacy-credentials.json"
    vault = delivery.DataPlaneCredentialVault(path)
    original = vault.load_or_create(INSTALLATION_ID)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["schema_version"] = delivery.LEGACY_CREDENTIAL_SCHEMA_VERSION
    payload["services"].pop("redis_recovery")
    path.write_text(json.dumps(payload), encoding="utf-8")

    migrated = vault.load_or_create(INSTALLATION_ID)
    persisted = json.loads(path.read_text(encoding="utf-8"))

    assert migrated["redis"] == original["redis"]
    assert migrated["redis_recovery"].username == "dle_recovery"
    assert persisted["schema_version"] == delivery.CREDENTIAL_SCHEMA_VERSION
