import base64
from types import SimpleNamespace

from tests.conftest import seed_login_session


def test_session_cookie_security_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("CORS_ORIGINS", "https://localhost:3000")
    monkeypatch.setenv("ALLOW_PLAINTEXT_PROD_SECRETS", "true")
    monkeypatch.setattr(
        "backend.runtime.data_plane_delivery.encrypt_data",
        lambda value: base64.b64encode(value.encode()).decode(),
    )
    monkeypatch.setattr(
        "backend.runtime.data_plane_delivery.decrypt_data",
        lambda value: base64.b64decode(value.encode()).decode(),
    )
    monkeypatch.setattr(
        "backend.runtime.data_plane_delivery.ensure_restricted_user_acl",
        lambda *_args, **_kwargs: True,
    )

    from app import create_app

    app = create_app(
        "production",
        {
            "SQLALCHEMY_DATABASE_URI": "postgresql://test:test@127.0.0.1:5432/test",
                "DLE_INITIALIZE_STORES": False,
                "DLE_START_MANAGED_SERVICES": False,
                "DLE_REQUIRED_SERVICES": "",
                "DLE_DATA_PLANE_PROFILE": "qualification",
                "DLE_RUNTIME_ROOT": str(tmp_path),
            },
        start_runtime=False,
    )

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] in {"Lax", "Strict", "None"}
    assert app.config["SESSION_COOKIE_SECURE"] is True


def test_api_session_mutation_blocks_untrusted_origin(app, client, monkeypatch):
    seed_login_session(client, app, username="csrf_origin_user")
    monkeypatch.setitem(app.config, "TESTING", False)

    response = client.post(
        "/api/v1/settings/ai",
        headers={"Origin": "https://attacker.example"},
        json={"ai_processing_enabled": False},
    )

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["code"] == "CSRF_ORIGIN_CHECK_FAILED"
    assert payload["success"] is False


def test_api_session_mutation_requires_csrf_token_when_enforced(app, client, monkeypatch):
    seed_login_session(client, app, username="csrf_token_user")
    monkeypatch.setitem(app.config, "TESTING", False)
    monkeypatch.setenv("ENFORCE_API_CSRF_TOKENS", "true")

    response = client.post(
        "/api/v1/settings/ai",
        headers={"Origin": "app://-"},
        json={"ai_processing_enabled": False},
    )

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["code"] == "CSRF_TOKEN_CHECK_FAILED"
    assert payload["error"] == "CSRF session token missing"


def test_api_session_mutation_accepts_valid_csrf_token_when_enforced(app, client, monkeypatch):
    seed_login_session(client, app, username="csrf_valid_user")
    monkeypatch.setitem(app.config, "TESTING", False)
    monkeypatch.setenv("ENFORCE_API_CSRF_TOKENS", "true")

    token_response = client.get("/api/v1/auth/csrf-token")
    assert token_response.status_code == 200
    token = token_response.get_json()["data"]["csrf_token"]

    response = client.post(
        "/api/v1/settings/ai",
        headers={
            "Origin": "app://-",
            "X-CSRF-Token": token,
        },
        json={"ai_processing_enabled": False},
    )

    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["settings"]["ai_processing_enabled"] is False


def test_signed_desktop_mutation_prefers_desktop_auth_over_stale_session(app, client, monkeypatch):
    user_id = seed_login_session(client, app, username="desktop_csrf_user")
    monkeypatch.setitem(app.config, "TESTING", False)
    monkeypatch.setenv("ENFORCE_API_CSRF_TOKENS", "true")
    monkeypatch.setattr(
        "backend.auth.api_decorators.check_desktop_request_auth",
        lambda: (True, SimpleNamespace(id=user_id)),
    )

    response = client.post(
        "/api/v1/settings/ai",
        headers={
            "Origin": "app://-",
            "X-DataLogic-Desktop": "true",
        },
        json={"ai_processing_enabled": False},
    )

    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["settings"]["ai_processing_enabled"] is False
