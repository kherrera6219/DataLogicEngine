from __future__ import annotations

import base64

import pytest

from backend.runtime import data_plane_delivery as delivery
from backend.runtime.podman_data_plane import (
    APP_SERVICE_KEYS,
    PodmanDataPlaneError,
    PodmanDataPlaneManager,
    REQUIRED_OBJECT_BUCKETS,
)


LOCK_PATH = "deploy/internal-data-plane.candidate-lock.json"
INSTALLATION_ID = "89abcdef0123456789abcdef01234567"


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(
        delivery,
        "encrypt_data",
        lambda value: base64.b64encode(value.encode()).decode(),
    )
    monkeypatch.setattr(
        delivery,
        "decrypt_data",
        lambda value: base64.b64decode(value.encode()).decode(),
    )
    monkeypatch.setattr(delivery, "ensure_restricted_user_acl", lambda *_a, **_k: True)
    return PodmanDataPlaneManager(
        runtime_root=tmp_path,
        installation_id=INSTALLATION_ID,
        profile="qualification",
        lock_path=LOCK_PATH,
        require_dpapi=False,
    )


def test_manager_builds_one_stable_five_service_profile(manager):
    assert tuple(manager._specs) == APP_SERVICE_KEYS
    assert manager.network_name == "dle-89abcdef0123-internal"
    assert manager.plan.production_authorized is False

    endpoints = {manager.endpoint(service) for service in APP_SERVICE_KEYS}
    assert len(endpoints) == len(APP_SERVICE_KEYS)
    assert all(endpoint.startswith("127.0.0.1:") for endpoint in endpoints)


def test_every_container_is_digest_pinned_loopback_and_hardened(manager):
    for service in APP_SERVICE_KEYS:
        spec = manager._specs[service]
        arguments = manager._container_arguments(spec)
        assert "--read-only" in arguments
        assert ["--cap-drop", "all"] == arguments[
            arguments.index("--cap-drop") : arguments.index("--cap-drop") + 2
        ]
        assert "no-new-privileges" in arguments
        assert "--restart" in arguments and "no" in arguments
        assert "@sha256:" in manager.artifacts[spec.lock_key].image
        publications = [
            arguments[index + 1]
            for index, value in enumerate(arguments)
            if value == "--publish"
        ]
        assert publications
        assert all(value.startswith("127.0.0.1:") for value in publications)


def test_connection_settings_use_generated_credentials_and_internal_endpoints(manager):
    settings = manager.connection_settings()
    assert settings["database_url"].startswith("postgresql://dle_app:")
    assert settings["redis_url"].startswith("redis://dle_app:")
    assert settings["neo4j_uri"].startswith("bolt://127.0.0.1:")
    assert settings["object_endpoint"].startswith("http://127.0.0.1:")
    assert tuple(settings["object_buckets"]) == REQUIRED_OBJECT_BUCKETS
    assert len(settings["object_access_key"]) >= 32
    assert len(settings["object_secret_key"]) >= 32

    migration = manager.migration_connection_settings()
    assert migration["database_url"].startswith("postgresql://dle_migration:")
    assert migration["database_url"] != settings["database_url"]


def test_service_secrets_enforce_scoped_users_and_bucket_actions(manager):
    redis_config = manager._secret_payload("redis", "redis.conf")
    assert "user default off" in redis_config
    assert "user dle_app on" in redis_config
    assert "-@dangerous" in redis_config

    postgres_init = manager._secret_payload(
        "postgresql",
        "/docker-entrypoint-initdb.d/010-dle-roles.sql",
    )
    assert "CREATE ROLE dle_app LOGIN" in postgres_init
    assert "GRANT CONNECT ON DATABASE datalogic TO dle_app" in postgres_init

    object_config = manager._secret_payload("minio", "dle-s3.json")
    assert '"name":"dle-application"' in object_config
    assert "Admin" in object_config
    for bucket in REQUIRED_OBJECT_BUCKETS:
        assert f"Read:{bucket}" in object_config
        assert f"Write:{bucket}" in object_config


def test_manager_rejects_foreign_container_identity(manager):
    spec = manager._specs["redis"]
    inspected = {
        "Config": {
            "Image": manager.artifacts[spec.lock_key].image,
            "Labels": {
                "com.datalogicengine.installation": "foreign",
                "com.datalogicengine.identity": spec.identity,
            },
        }
    }
    with pytest.raises(PodmanDataPlaneError, match="foreign_service_container"):
        manager._assert_owned_container(spec, inspected)


def test_production_profile_remains_fail_closed(tmp_path):
    with pytest.raises(delivery.DataPlaneDeliveryError, match="production_data_plane_not_approved"):
        PodmanDataPlaneManager(
            runtime_root=tmp_path,
            installation_id=INSTALLATION_ID,
            profile="production",
            lock_path=LOCK_PATH,
            require_dpapi=False,
        )


def test_service_start_runs_full_preflight_before_any_mutation(manager, monkeypatch):
    calls = []
    monkeypatch.setattr(manager, "verify_runtime", lambda: calls.append("runtime"))
    monkeypatch.setattr(manager, "verify_artifacts", lambda: calls.append("artifacts"))
    monkeypatch.setattr(manager, "_ensure_network", lambda: calls.append("network"))
    monkeypatch.setattr(manager, "_ensure_volume", lambda *_args: None)
    monkeypatch.setattr(manager, "_ensure_secret", lambda *_args: None)
    monkeypatch.setattr(
        manager,
        "_inspect_container",
        lambda *_args: {"State": {"Running": True}},
    )
    monkeypatch.setattr(manager, "_assert_owned_container", lambda *_args: None)
    monkeypatch.setattr(manager, "_wait_until_ready", lambda *_args: True)

    assert manager.start_service("redis") is True
    assert calls[:3] == ["runtime", "artifacts", "network"]


def test_failed_preflight_does_not_mutate_service_state(manager, monkeypatch):
    mutations = []

    def fail_runtime():
        raise PodmanDataPlaneError("container_runtime_unavailable")

    monkeypatch.setattr(manager, "verify_runtime", fail_runtime)
    monkeypatch.setattr(manager, "_ensure_network", lambda: mutations.append("network"))

    assert manager.start_service("postgresql") is False
    assert mutations == []
    assert manager.last_failure_reasons["postgresql"] == "container_runtime_unavailable"
