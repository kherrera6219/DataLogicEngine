import importlib

import pytest
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture
def app_module(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    app_module = importlib.import_module("app")
    app_module = importlib.reload(app_module)

    ctx = app_module.app.app_context()
    ctx.push()

    try:
        yield app_module
    finally:
        ctx.pop()


def test_password_policy_requires_complexity(app_module):
    password_meets_policy = app_module.password_meets_policy

    assert password_meets_policy("ValidPass123!") is True
    assert password_meets_policy("short1!") is False
    assert password_meets_policy("nouppercase123!") is False
    assert password_meets_policy("NOLOWERCASE123!") is False
    assert password_meets_policy("NoSymbols123") is False


def test_config_health_reports_environment_and_secret(app_module, monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    health = app_module._config_health()

    assert health["environment"] == "testing"
    assert health["secret_key"] == "set"


def test_database_health_success_path(monkeypatch, app_module):
    class DummyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, stmt):
            return None

    monkeypatch.setattr(app_module.db.engine, "connect", lambda: DummyConnection())

    status = app_module._database_health()
    assert status == {"status": "ok"}


def test_database_health_failure_path(monkeypatch, app_module):
    def failing_connect():
        raise SQLAlchemyError("boom")

    monkeypatch.setattr(app_module.db.engine, "connect", failing_connect)

    status = app_module._database_health()
    assert status["status"] == "error"
    assert "boom" in status["detail"]
