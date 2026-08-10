from flask import Flask

from backend.storage.runtime_endpoints import runtime_neo4j_settings, runtime_redis_url


def test_session_manager_prefers_managed_app_endpoint(monkeypatch):
    from flask import Flask

    from backend.security.session_manager import SessionManager

    monkeypatch.setenv("REDIS_URL", "redis://legacy.invalid:6379/0")
    app = Flask(__name__)
    app.secret_key = "test-only"
    app.config["DLE_REDIS_URL"] = "redis://dle_app:secret@127.0.0.1:46379/0"

    manager = SessionManager(app)

    assert manager.redis_client.connection_pool.connection_kwargs["host"] == "127.0.0.1"
    assert manager.redis_client.connection_pool.connection_kwargs["port"] == 46379


def test_managed_runtime_endpoints_override_legacy_environment(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.setenv("NEO4J_URI", "bolt://127.0.0.1:7690")
    monkeypatch.setenv("NEO4J_USER", "legacy")
    monkeypatch.setenv("NEO4J_PASSWORD", "legacy-password")
    app = Flask(__name__)
    app.config.update(
        DLE_REDIS_URL="redis://dle_app:secret@127.0.0.1:46379/0",
        DLE_NEO4J_URI="bolt://127.0.0.1:47687",
        DLE_NEO4J_USER="dle_app",
        DLE_NEO4J_PASSWORD="managed-secret",
    )

    with app.app_context():
        assert runtime_redis_url() == "redis://dle_app:secret@127.0.0.1:46379/0"
        assert runtime_neo4j_settings() == (
            "bolt://127.0.0.1:47687",
            "dle_app",
            "managed-secret",
        )


def test_endpoint_helpers_retain_development_environment_compatibility(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:16379/0")
    monkeypatch.setenv("NEO4J_URI", "bolt://127.0.0.1:17687")
    monkeypatch.setenv("NEO4J_USER", "developer")
    monkeypatch.setenv("NEO4J_PASSWORD", "development-only")

    assert runtime_redis_url() == "redis://127.0.0.1:16379/0"
    assert runtime_neo4j_settings() == (
        "bolt://127.0.0.1:17687",
        "developer",
        "development-only",
    )
