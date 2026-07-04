from types import SimpleNamespace

from backend.auth import api_decorators
from tests.conftest import create_test_user


def test_mcp_admin_route_accepts_external_api_key(app, client, monkeypatch):
    """Admin MCP routes must not be blocked by Flask-Login session-only wrappers."""
    with app.app_context():
        user_id = create_test_user(
            username="mcp_api_key_user",
            email="mcp_api_key_user@test.com",
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
