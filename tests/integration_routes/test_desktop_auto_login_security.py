from models import User


def _desktop_headers():
    return {"X-DataLogic-Desktop": "true"}


def test_desktop_auto_login_requires_desktop_header(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setattr("routes.auth_routes.os.name", "nt", raising=False)

    response = client.post("/api/v1/auth/desktop/auto-login")
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False


def test_desktop_auto_login_rejects_fallback_identity(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setattr("routes.auth_routes.os.name", "nt", raising=False)
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        lambda: {
            "username": "fallback-user",
            "sid": "S-1-5-local-fallback",
            "domain": "LOCAL",
            "is_fallback": True,
        },
    )

    response = client.post("/api/v1/auth/desktop/auto-login", headers=_desktop_headers())
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False


def test_desktop_auto_login_defaults_first_user_to_standard_role(app, client, monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_AUTOLOGIN_BOOTSTRAP_OWNER", "false")
    monkeypatch.setattr("routes.auth_routes.os.name", "nt", raising=False)
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        lambda: {
            "username": "owner",
            "sid": "S-1-5-21-1000-1000-1000-1001",
            "domain": "LOCAL",
            "is_fallback": False,
        },
    )

    response = client.post("/api/v1/auth/desktop/auto-login", headers=_desktop_headers())
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
    monkeypatch.setenv("DESKTOP_AUTOLOGIN_BOOTSTRAP_OWNER", "true")
    monkeypatch.setattr("routes.auth_routes.os.name", "nt", raising=False)
    monkeypatch.setattr(
        "backend.auth.windows_identity.get_windows_user_identity",
        lambda: {
            "username": "bootstrap-owner",
            "sid": "S-1-5-21-1000-1000-1000-9001",
            "domain": "LOCAL",
            "is_fallback": False,
        },
    )

    response = client.post("/api/v1/auth/desktop/auto-login", headers=_desktop_headers())
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["user"]["role"] == "owner"
    assert payload["data"]["user"]["is_admin"] is True
