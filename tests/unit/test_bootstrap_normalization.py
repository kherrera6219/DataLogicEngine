import importlib

import pytest


def test_auto_create_schema_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AUTO_CREATE_SCHEMA", raising=False)
    app_module = importlib.import_module("app")
    importlib.reload(app_module)

    assert app_module._should_auto_create_schema() is False


def test_auto_create_schema_enabled_when_opted_in(monkeypatch):
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "true")
    app_module = importlib.import_module("app")
    importlib.reload(app_module)

    assert app_module._should_auto_create_schema() is True


def test_production_startup_rejects_auto_create_schema(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "true")
    monkeypatch.setenv("SESSION_SECRET", "prod-session-secret")
    monkeypatch.setenv("ALLOW_PLAINTEXT_PROD_SECRETS", "true")
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com")

    with pytest.raises(RuntimeError, match="AUTO_CREATE_SCHEMA=true is not allowed in production"):
        app_module = importlib.import_module("app")
        importlib.reload(app_module)
