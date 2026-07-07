import time

from backend.security.desktop_local_auth import build_desktop_request_signature
from models import LLMProvider
from tests.conftest import seed_login_session


def _signed_desktop_headers(path: str, *, method: str = "POST", secret: str = "test-install-secret"):
    timestamp = str(int(time.time()))
    signature = build_desktop_request_signature(
        method=method,
        full_path=path,
        timestamp=timestamp,
        install_secret=secret,
    )
    return {
        "Origin": "app://-",
        "X-DataLogic-Desktop": "true",
        "X-Desktop-Auth-Timestamp": timestamp,
        "X-Desktop-Auth-Request-Signature": signature,
    }


def _desktop_identity():
    return {
        "username": "desktop-gateway",
        "sid": "S-1-5-21-DESKTOP-GATEWAY",
        "domain": "LOCAL",
        "is_fallback": False,
    }


def test_gateway_keys_accepts_signed_desktop_request_without_session(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setenv("ENFORCE_API_CSRF_TOKENS", "true")
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        _desktop_identity,
    )

    response = client.post(
        "/api/v1/gateway/keys",
        headers=_signed_desktop_headers("/api/v1/gateway/keys"),
        json={
            "provider": "google",
            "key": "test-google-key",
            "model": "gemini-3.1-pro-preview",
        },
    )

    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["provider"]["provider_type"] == "google"

    with app.app_context():
        provider = LLMProvider.query.filter_by(provider_type="google").first()
        assert provider is not None
        assert provider.model_id == "gemini-3.1-pro-preview"
        assert provider.get_api_key() == "test-google-key"


def test_gateway_keys_signed_desktop_request_ignores_stale_session_csrf(app, client, monkeypatch):
    seed_login_session(client, app, username="stale_gateway_session")
    monkeypatch.setitem(app.config, "TESTING", False)
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setenv("ENFORCE_API_CSRF_TOKENS", "true")
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        _desktop_identity,
    )

    response = client.post(
        "/api/v1/gateway/keys",
        headers=_signed_desktop_headers("/api/v1/gateway/keys"),
        json={
            "provider": "openai",
            "key": "test-openai-key",
            "model": "gpt-5.5",
        },
    )

    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["provider"]["provider_type"] == "openai"
