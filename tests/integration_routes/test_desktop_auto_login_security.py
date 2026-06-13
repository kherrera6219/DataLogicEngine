from backend.security.desktop_local_auth import build_desktop_auth_signature
from models import User


def _desktop_headers(nonce=None, signature=None):
    headers = {"X-DataLogic-Desktop": "true"}
    if nonce:
        headers["X-Desktop-Auth-Nonce"] = nonce
    if signature:
        headers["X-Desktop-Auth-Signature"] = signature
    return headers


def _issue_desktop_challenge(client):
    response = client.post("/api/v1/auth/desktop/challenge", headers=_desktop_headers())
    assert response.status_code == 200
    payload = response.get_json()
    return payload["data"]["nonce"]


def _desktop_auth_headers(client, install_secret: str):
    nonce = _issue_desktop_challenge(client)
    signature = build_desktop_auth_signature(nonce, install_secret)
    return _desktop_headers(nonce=nonce, signature=signature)


def test_desktop_auto_login_requires_desktop_header(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setattr("backend.routes.auth_routes.os.name", "nt", raising=False)

    response = client.post("/api/v1/auth/desktop/auto-login")
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False


def test_desktop_auto_login_rejects_fallback_identity(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setattr("backend.routes.auth_routes.os.name", "nt", raising=False)
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        lambda: {
            "username": "fallback-user",
            "sid": "S-1-5-local-fallback",
            "domain": "LOCAL",
            "is_fallback": True,
        },
    )

    response = client.post(
        "/api/v1/auth/desktop/auto-login",
        headers=_desktop_auth_headers(client, "test-install-secret"),
    )
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False


def test_desktop_auto_login_rejects_invalid_challenge_signature(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setattr("backend.routes.auth_routes.os.name", "nt", raising=False)

    nonce = _issue_desktop_challenge(client)
    response = client.post(
        "/api/v1/auth/desktop/auto-login",
        headers=_desktop_headers(nonce=nonce, signature="invalid-signature"),
    )

    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["code"] == "DESKTOP_AUTH_CHALLENGE_FAILED"


def test_desktop_auto_login_defaults_first_user_to_standard_role(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setenv("DESKTOP_AUTOLOGIN_BOOTSTRAP_OWNER", "false")
    monkeypatch.setattr("backend.routes.auth_routes.os.name", "nt", raising=False)
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        lambda: {
            "username": "owner",
            "sid": "S-1-5-21-1000-1000-1000-1001",
            "domain": "LOCAL",
            "is_fallback": False,
        },
    )

    response = client.post(
        "/api/v1/auth/desktop/auto-login",
        headers=_desktop_auth_headers(client, "test-install-secret"),
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["user"]["role"] == "user"
    assert payload["data"]["user"]["is_admin"] is False

    with app.app_context():
        user = User.query.filter_by(sid="S-1-5-21-1000-1000-1000-1001").first()
        assert user is not None
        assert user.role == "user"
        assert user.is_admin is False


def test_desktop_auto_login_can_bootstrap_owner_when_explicitly_enabled(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "test-install-secret")
    monkeypatch.setenv("DESKTOP_AUTOLOGIN_BOOTSTRAP_OWNER", "true")
    monkeypatch.setattr("backend.routes.auth_routes.os.name", "nt", raising=False)
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        lambda: {
            "username": "bootstrap-owner",
            "sid": "S-1-5-21-1000-1000-1000-9001",
            "domain": "LOCAL",
            "is_fallback": False,
        },
    )

    response = client.post(
        "/api/v1/auth/desktop/auto-login",
        headers=_desktop_auth_headers(client, "test-install-secret"),
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["user"]["role"] == "owner"
    assert payload["data"]["user"]["is_admin"] is True
