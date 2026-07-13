"""HTTP contracts for Phase 2 readiness, capabilities, and lifecycle state."""

from backend.runtime import RuntimePhase


def test_capabilities_reject_anonymous_client(client):
    anonymous = client.get("/api/v1/system/capabilities")
    assert anonymous.status_code == 401


def test_capabilities_are_machine_readable(authenticated_client):
    response = authenticated_client.get("/api/v1/system/capabilities")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["capabilities"]["phase"] == "ready"
    assert "postgresql" in payload["capabilities"]["services"]
    assert payload["correlation_id"]


def test_signed_lifecycle_suspend_and_resume_change_readiness(
    app,
    authenticated_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "backend.auth.api_decorators.check_desktop_request_auth",
        lambda: (True, object()),
    )
    runtime = app.extensions["dle_runtime"]

    suspended = authenticated_client.post(
        "/api/v1/system/lifecycle/event",
        json={"event": "suspend"},
    )
    assert suspended.status_code == 202
    assert runtime.phase == RuntimePhase.DRAINING
    assert authenticated_client.get("/ready").status_code == 503

    resumed = authenticated_client.post(
        "/api/v1/system/lifecycle/event",
        json={"event": "resume"},
    )
    assert resumed.status_code == 202
    assert runtime.phase == RuntimePhase.READY
    assert authenticated_client.get("/ready").status_code == 200


def test_lifecycle_endpoint_rejects_non_desktop_session(authenticated_client, monkeypatch):
    monkeypatch.setattr(
        "backend.auth.api_decorators.check_desktop_request_auth",
        lambda: (False, None),
    )
    response = authenticated_client.post(
        "/api/v1/system/lifecycle/event",
        json={"event": "suspend"},
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "DESKTOP_LIFECYCLE_AUTH_REQUIRED"


def test_runtime_drain_rejects_new_mutation(app, authenticated_client):
    runtime = app.extensions["dle_runtime"]
    with runtime.exclusive_operation("backup"):
        response = authenticated_client.post(
            "/api/v1/gateway/chat",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
    assert response.status_code == 503
    assert response.get_json()["code"] == "RUNTIME_NOT_ACCEPTING_WORK"
