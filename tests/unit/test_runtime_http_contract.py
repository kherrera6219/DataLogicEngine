"""HTTP contracts for Phase 2 readiness, capabilities, and lifecycle state."""

from pathlib import Path

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


def test_diagnostics_summary_rejects_anonymous_client(client):
    assert client.get("/api/v1/system/diagnostics/summary").status_code == 401


def test_diagnostics_summary_is_content_free(authenticated_client):
    response = authenticated_client.get("/api/v1/system/diagnostics/summary")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["schema_version"] == "dle.diagnostics.v1"
    assert payload["support_bundle"]["user_content_included"] is False
    assert payload["support_bundle"]["generic_reports_included"] is False
    assert payload["external_telemetry"]["opted_in"] is False
    assert payload["correlation_id"]


def test_support_bundle_requires_preview_and_explicit_confirmation(
    app,
    authenticated_client,
):
    preview_response = authenticated_client.post(
        "/api/v1/system/diagnostics/support/preview"
    )
    assert preview_response.status_code == 200
    preview = preview_response.get_json()
    assert preview["archive_created"] is False
    assert preview["user_content_included"] is False
    assert len(preview["preview_fingerprint"]) == 64

    no_confirmation = authenticated_client.post(
        "/api/v1/system/diagnostics/support/export",
        json={"preview_fingerprint": preview["preview_fingerprint"]},
    )
    assert no_confirmation.status_code == 400
    assert no_confirmation.get_json()["code"] == "SUPPORT_BUNDLE_CONFIRMATION_REQUIRED"

    stale = authenticated_client.post(
        "/api/v1/system/diagnostics/support/export",
        json={"confirm": True, "preview_fingerprint": "0" * 64},
    )
    assert stale.status_code == 409
    assert stale.get_json()["code"] == "SUPPORT_BUNDLE_PREVIEW_STALE"

    exported = authenticated_client.post(
        "/api/v1/system/diagnostics/support/export",
        json={"confirm": True, "preview_fingerprint": preview["preview_fingerprint"]},
    )
    assert exported.status_code == 201
    artifact = exported.get_json()
    assert artifact["success"] is True
    assert len(artifact["sha256"]) == 64
    assert artifact["location"] == "application_support_bundles_directory"

    support_root = app.extensions["dle_runtime"].runtime_root / "support-bundles"
    archive_path = support_root / artifact["artifact_name"]
    sidecar_path = support_root / artifact["sidecar_name"]
    assert archive_path.is_file()
    assert sidecar_path.is_file()
    assert Path(archive_path).stat().st_size == artifact["size_bytes"]
