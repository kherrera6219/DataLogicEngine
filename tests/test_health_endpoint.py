import importlib

import pytest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    app_module = importlib.import_module("app")
    importlib.reload(app_module)
    app = app_module.app
    app.testing = True
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint_reports_ok_status(client):
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["status"] in {"ok", "degraded"}
    assert payload["config"]["environment"] == "testing"
    assert payload["database"]["status"] == "ok"


def test_health_endpoint_has_timestamp(client):
    response = client.get("/health")
    payload = response.get_json()
    timestamp = payload["timestamp"]
    assert timestamp.endswith("Z") or timestamp.endswith("+00:00")
