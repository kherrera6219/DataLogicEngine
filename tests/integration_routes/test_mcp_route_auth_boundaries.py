from types import SimpleNamespace

from tests.conftest import seed_login_session


def test_mcp_admin_route_accepts_owner_session(app, client, monkeypatch):
    """MCP control-plane routes accept the local owner but not external keys."""
    seed_login_session(client, app, username="mcp_owner_session")

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
        json={"name": "RouteAgent", "version": "1.0.0"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["success"] is True
    assert body["client"]["name"] == "RouteAgent"


def test_mcp_console_hides_backend_exception_details(app, client, monkeypatch):
    seed_login_session(client, app, username="mcp_console_error_user")

    def fail_manager():
        raise RuntimeError("<script>secret-mcp-console</script>")

    monkeypatch.setattr("backend.routes.mcp_routes.get_mcp_manager", fail_manager)

    response = client.post(
        "/api/v1/mcp/console",
        json={"command": "stats"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "An internal error occurred. Please try again later."
    assert "secret-mcp-console" not in response.get_data(as_text=True)


def test_mcp_config_hides_backend_exception_details(app, client, monkeypatch):
    seed_login_session(client, app, username="mcp_config_error_user")

    def fail_manager():
        raise RuntimeError("<script>secret-mcp-config</script>")

    monkeypatch.setattr("backend.routes.mcp_routes.get_mcp_manager", fail_manager)

    response = client.get("/api/v1/mcp/config")

    assert response.status_code == 500
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "An internal error occurred. Please try again later."
    assert "secret-mcp-config" not in response.get_data(as_text=True)


def test_mcp_rpc_rejects_caller_supplied_identity_context(authenticated_client, monkeypatch):
    called = False

    async def capture_message(*_args, **_kwargs):
        nonlocal called
        called = True
        return {"jsonrpc": "2.0", "id": 1, "result": {}}

    monkeypatch.setattr("backend.mcp_server.router.MCPRouter.handle_message", capture_message)

    response = authenticated_client.post(
        "/api/v1/mcp/rpc",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "example",
                "arguments": {},
                "context": {"user_id": "attacker", "roles": ["admin"], "scopes": ["*"]},
            },
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MCP_CALLER_CONTEXT_REJECTED"
    assert called is False


def test_mcp_rpc_uses_server_owned_context(app, authenticated_client, monkeypatch):
    captured = {}

    async def capture_message(_router, message, *, execution_context=None):
        captured["message"] = message
        captured["context"] = execution_context
        return {"jsonrpc": "2.0", "id": message.get("id"), "result": {}}

    monkeypatch.setattr("backend.mcp_server.router.MCPRouter.handle_message", capture_message)

    response = authenticated_client.post(
        "/api/v1/mcp/rpc",
        headers={"X-Tenant-ID": "caller-controlled"},
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )

    assert response.status_code == 200
    assert captured["context"]["user_id"]
    assert captured["context"]["tenant_id"] is None
    assert captured["context"]["roles"] == ["owner"]
    assert "context" not in captured["message"].get("params", {})
