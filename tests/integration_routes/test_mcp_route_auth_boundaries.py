from types import SimpleNamespace

from backend.auth import api_decorators
from tests.conftest import create_test_user


def _install_admin_api_key(app, monkeypatch, *, username="mcp_api_key_user"):
    with app.app_context():
        user_id = create_test_user(
            username=username,
            email=f"{username}@test.com",
        )

    monkeypatch.setattr(
        api_decorators.ExternalAPIKey,
        "verify_key",
        staticmethod(
            lambda _key: SimpleNamespace(
                user_id=user_id,
                permissions={"admin": True},
            )
        ),
    )
    return user_id


def test_mcp_admin_route_accepts_external_api_key(app, client, monkeypatch):
    """Admin MCP routes must not be blocked by Flask-Login session-only wrappers."""
    _install_admin_api_key(app, monkeypatch)

    mcp_client = SimpleNamespace(
        get_client_info=lambda: {
            "id": "client-1",
            "name": "RouteAgent",
            "version": "1.0.0",
        }
    )
    manager = SimpleNamespace(
        create_client=lambda name, version: mcp_client
    )
    monkeypatch.setattr("backend.routes.mcp_routes.get_mcp_manager", lambda: manager)

    response = client.post(
        "/api/v1/mcp/clients",
        headers={"X-API-Key": "ukg_valid_test_key"},
        json={"name": "RouteAgent", "version": "1.0.0"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["success"] is True
    assert body["client"]["name"] == "RouteAgent"


def test_mcp_console_hides_backend_exception_details(app, client, monkeypatch):
    _install_admin_api_key(app, monkeypatch, username="mcp_console_error_user")

    def fail_manager():
        raise RuntimeError("<script>secret-mcp-console</script>")

    monkeypatch.setattr("backend.routes.mcp_routes.get_mcp_manager", fail_manager)

    response = client.post(
        "/api/v1/mcp/console",
        headers={"X-API-Key": "ukg_valid_test_key"},
        json={"command": "stats"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "An internal error occurred. Please try again later."
    assert "secret-mcp-console" not in response.get_data(as_text=True)


def test_mcp_config_hides_backend_exception_details(app, client, monkeypatch):
    _install_admin_api_key(app, monkeypatch, username="mcp_config_error_user")

    def fail_manager():
        raise RuntimeError("<script>secret-mcp-config</script>")

    monkeypatch.setattr("backend.routes.mcp_routes.get_mcp_manager", fail_manager)

    response = client.get(
        "/api/v1/mcp/config",
        headers={"X-API-Key": "ukg_valid_test_key"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "An internal error occurred. Please try again later."
    assert "secret-mcp-config" not in response.get_data(as_text=True)
