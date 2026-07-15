import importlib

import pytest

from core.system.frost_service import FROSTService
from core.simulation.trace_system import create_tracing_system


def test_frost_snapshot_hmac_integrity(monkeypatch):
    monkeypatch.setenv("FROST_SNAPSHOT_HMAC_SECRET", "phase3-test-secret")
    frost = FROSTService()

    snapshot_id = frost.snapshot({"alpha": 1, "beta": {"nested": True}})
    assert frost.verify_snapshot(snapshot_id) is True

    metadata = frost.snapshot_metadata[snapshot_id]
    assert metadata["algorithm"] == "sha256+hmac-sha256"
    assert metadata["hmac_signature"]


def test_frost_snapshot_tamper_detection(monkeypatch):
    monkeypatch.setenv("FROST_SNAPSHOT_HMAC_SECRET", "phase3-test-secret")
    frost = FROSTService()
    snapshot_id = frost.snapshot({"alpha": 1})

    # Simulate in-memory tampering
    frost.snapshots[snapshot_id]["alpha"] = 999

    assert frost.verify_snapshot(snapshot_id) is False
    with pytest.raises(ValueError):
        frost.get_snapshot(snapshot_id, verify_integrity=True)


def test_trace_bundle_hmac_integrity(monkeypatch):
    monkeypatch.setenv("TRACE_BUNDLE_HMAC_SECRET", "trace-phase3-secret")
    tracing = create_tracing_system()

    tracing.start_trace("query-phase3", tier=3)
    tracing.trace_tier_decision({"selected_tier": 3})
    bundle = tracing.seal_bundle("query-phase3", final_answer_hash="answer-hash")

    assert bundle.bundle_hash
    assert bundle.bundle_signature
    assert tracing.verify_bundle("query-phase3") is True


def test_trace_bundle_tamper_detection(monkeypatch):
    monkeypatch.setenv("TRACE_BUNDLE_HMAC_SECRET", "trace-phase3-secret")
    tracing = create_tracing_system()

    tracing.start_trace("query-tamper", tier=2)
    tracing.trace_tier_decision({"selected_tier": 2})
    bundle = tracing.seal_bundle("query-tamper", final_answer_hash="answer-hash")
    assert tracing.verify_bundle("query-tamper") is True

    # Tamper with sealed data after signature/hash were computed
    bundle.entries[0].data["selected_tier"] = 9
    assert tracing.verify_bundle("query-tamper") is False


@pytest.fixture
def crash_client(monkeypatch, tmp_path):
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("DLE_RUNTIME_ROOT", str(tmp_path / "crash-runtime"))
    monkeypatch.delenv("SENTRY_DSN", raising=False)

    app_module = importlib.import_module("app")
    importlib.reload(app_module)
    app = app_module.app
    app.config["TESTING"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = False

    if "__phase3_crash_probe" not in app.view_functions:
        @app.route("/__phase3/crash-probe")
        def __phase3_crash_probe():  # pragma: no cover - exercised via test client
            raise RuntimeError("phase3 crash probe")

    with app.test_client() as test_client:
        yield test_client


def test_crash_handler_returns_fallback_crash_id(crash_client):
    response = crash_client.get("/__phase3/crash-probe")
    assert response.status_code == 500
    payload = response.get_json()
    crash_id = payload["error"]["crash_id"]
    assert crash_id.startswith("crash_")
    assert response.headers.get("X-Crash-ID") == crash_id
