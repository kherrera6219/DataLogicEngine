import time

from backend.security.desktop_local_auth import build_desktop_request_signature
from models import User, UserAIPreferences
from tests.conftest import seed_login_session


def _signed_desktop_headers(path: str, *, method: str = "GET", secret: str = "test-install-secret"):
    timestamp = str(int(time.time()))
    signature = build_desktop_request_signature(
        method=method,
        full_path=path,
        timestamp=timestamp,
        install_secret=secret,
    )
    return {
        "X-DataLogic-Desktop": "true",
        "X-Desktop-Auth-Timestamp": timestamp,
        "X-Desktop-Auth-Request-Signature": signature,
    }


def test_ai_settings_returns_json_401_without_session(client):
    response = client.get("/api/v1/settings/ai")

    assert response.status_code == 401
    payload = response.get_json()
    assert payload["code"] == "UNAUTHORIZED"
    assert payload["success"] is False


def test_ai_settings_session_read_write_uses_authenticated_user(app, client):
    user_id = seed_login_session(client, app, username="settings_user")

    response = client.post(
        "/api/v1/settings/ai",
        json={
            "preferred_provider": " Google ",
            "preferred_model": "gemini-3.7-flash",
            "ai_processing_enabled": False,
            "store_chat_history": False,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["settings"]["preferred_provider"] == "google"
    assert payload["settings"]["preferred_model"] == "gemini-3.7-flash"
    assert payload["settings"]["ai_processing_enabled"] is False
    assert payload["settings"]["store_chat_history"] is False

    get_response = client.get("/api/v1/settings/ai")
    assert get_response.status_code == 200
    assert get_response.get_json()["preferred_provider"] == "google"

    with app.app_context():
        prefs = UserAIPreferences.query.filter_by(user_id=user_id).first()
        assert prefs is not None
        assert prefs.preferred_provider == "google"


def test_ai_settings_rejects_unsupported_provider_and_model(app, client):
    seed_login_session(client, app, username="settings_reject")

    provider_response = client.post(
        "/api/v1/settings/ai",
        json={"preferred_provider": "anthropic", "preferred_model": "claude-opus-4-7"},
    )
    assert provider_response.status_code == 400
    assert provider_response.get_json()["error"] == "Invalid provider selection"

    model_response = client.post(
        "/api/v1/settings/ai",
        json={"preferred_provider": "google", "preferred_model": "gemini-3.5-flash"},
    )
    assert model_response.status_code == 400
    assert model_response.get_json()["error"] == "Invalid model selection"


def test_ai_settings_accepts_signed_desktop_request_without_session(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        lambda: {
            "username": "desktop-settings",
            "sid": "S-1-5-21-DESKTOP-SETTINGS",
            "domain": "LOCAL",
            "is_fallback": False,
        },
    )

    response = client.post(
        "/api/v1/settings/ai",
        headers=_signed_desktop_headers("/api/v1/settings/ai", method="POST"),
        json={
            "preferred_provider": "openai",
            "preferred_model": "gpt-5.6-sol",
            "ai_processing_enabled": True,
            "store_chat_history": False,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["settings"]["preferred_provider"] == "openai"
    assert payload["settings"]["store_chat_history"] is False

    with app.app_context():
        user = User.query.filter_by(sid="S-1-5-21-DESKTOP-SETTINGS").first()
        assert user is not None
        prefs = UserAIPreferences.query.filter_by(user_id=user.id).first()
        assert prefs is not None
        assert prefs.preferred_provider == "openai"
        assert prefs.preferred_model == "gpt-5.6-sol"
