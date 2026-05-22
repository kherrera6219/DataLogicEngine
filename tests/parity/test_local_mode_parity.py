from __future__ import annotations

from config import DesktopConfig, ProductionConfig, get_config


def _desktop_headers() -> dict[str, str]:
    return {"X-DataLogic-Desktop": "true"}


def test_desktop_challenge_rejects_cloud_mode(client, monkeypatch) -> None:
    monkeypatch.setenv("IS_DESKTOP_APP", "false")
    monkeypatch.setattr("routes.auth_routes._is_windows_desktop_host", lambda: True)

    response = client.post("/api/v1/auth/desktop/challenge", headers=_desktop_headers())
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False


def test_desktop_challenge_requires_loopback_origin(client, monkeypatch) -> None:
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setattr("routes.auth_routes._is_windows_desktop_host", lambda: True)

    response = client.post(
        "/api/v1/auth/desktop/challenge",
        headers=_desktop_headers(),
        environ_base={"REMOTE_ADDR": "203.0.113.20"},
    )
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False


def test_desktop_challenge_succeeds_in_local_desktop_mode(client, monkeypatch) -> None:
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setattr("routes.auth_routes._is_windows_desktop_host", lambda: True)

    response = client.post("/api/v1/auth/desktop/challenge", headers=_desktop_headers())
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert isinstance(payload["data"].get("nonce"), str)
    assert payload["data"].get("expires_in_seconds", 0) >= 30


def test_desktop_auto_login_rejects_cloud_mode(client, monkeypatch) -> None:
    monkeypatch.setenv("IS_DESKTOP_APP", "false")
    monkeypatch.setattr("routes.auth_routes._is_windows_desktop_host", lambda: True)

    response = client.post("/api/v1/auth/desktop/auto-login", headers=_desktop_headers())
    assert response.status_code == 403
    payload = response.get_json()
    assert payload["success"] is False
    assert payload.get("code") is None


def test_runtime_config_parity_switches_between_desktop_and_cloud(monkeypatch) -> None:
    monkeypatch.setenv("FLASK_ENV", "production")

    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    desktop_config = get_config()
    assert isinstance(desktop_config, DesktopConfig)

    monkeypatch.setenv("IS_DESKTOP_APP", "false")
    cloud_config = get_config()
    assert isinstance(cloud_config, ProductionConfig)
