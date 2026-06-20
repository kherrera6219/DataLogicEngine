import importlib

import pytest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
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


def test_live_endpoint_reports_live_status(client):
    response = client.get("/live")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "live"


def test_ready_endpoint_reports_ready_status(client):
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ready"
    assert payload["checks"]["database"] == "ok"


def test_metrics_endpoint_exposes_prometheus_text(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "datalogicengine_process_uptime_seconds" in body
    assert "datalogicengine_http_requests_total" in body
    assert "datalogicengine_latency_slo_ai_p95_ms_target" in body
    assert "datalogicengine_dmrf_router_tier_total" in body


def test_metrics_endpoint_exposes_route_status_and_latency_labels(client):
    client.get("/health")

    response = client.get("/metrics")
    body = response.get_data(as_text=True)

    assert 'datalogicengine_http_requests_by_route_total{method="GET",route="/health",status="2xx"}' in body
    assert 'datalogicengine_http_request_latency_ms_avg{method="GET",route="/health"}' in body
    assert 'datalogicengine_http_request_latency_ms_max{method="GET",route="/health"}' in body


def test_metrics_endpoint_tracks_unmatched_routes(client):
    client.get("/does-not-exist")

    response = client.get("/metrics")
    body = response.get_data(as_text=True)

    assert 'datalogicengine_http_requests_by_route_total{method="GET",route="unmatched",status="4xx"}' in body
