from types import SimpleNamespace

from flask import g

from backend.auth import api_decorators


def test_check_api_auth_rejects_query_string_api_key(app, monkeypatch):
    """Legacy query-param API key auth must stay disabled."""
    with app.test_request_context("/api/v1/knowledge/nodes?api_key=ukg_deadbeef", method="GET"):
        monkeypatch.setattr(
            api_decorators,
            "current_user",
            SimpleNamespace(is_authenticated=False),
        )
        is_auth, principal = api_decorators.check_api_auth()
        assert is_auth is False
        assert principal is None


def test_check_api_auth_accepts_hashed_external_key_header(app, monkeypatch):
    """Header-based ExternalAPIKey auth should resolve to an active user principal."""
    api_key_record = SimpleNamespace(user_id=7)
    principal_user = SimpleNamespace(
        id=7,
        active=True,
        is_active=True,
        is_admin=False,
    )

    class _UserQuery:
        @staticmethod
        def get(user_id):
            if user_id == 7:
                return principal_user
            return None

    class _UserModel:
        query = _UserQuery()

    with app.test_request_context(
        "/api/v1/knowledge/nodes",
        method="GET",
        headers={"X-API-Key": "ukg_aabbccdd_validtoken"},
    ):
        monkeypatch.setattr(
            api_decorators,
            "current_user",
            SimpleNamespace(is_authenticated=False),
        )
        monkeypatch.setattr(
            api_decorators.ExternalAPIKey,
            "verify_key",
            staticmethod(lambda _key: api_key_record),
        )
        monkeypatch.setattr(api_decorators, "User", _UserModel)

        is_auth, principal = api_decorators.check_api_auth()
        assert is_auth is True
        assert principal is principal_user
        assert g.auth_mode == "api_key"
        assert g.auth_user is principal_user


def test_api_admin_required_allows_admin_api_key_principal(app, monkeypatch):
    """Admin-only decorators should honor an admin principal resolved via API key."""
    api_key_record = SimpleNamespace(user_id=12)
    admin_user = SimpleNamespace(
        id=12,
        active=True,
        is_active=True,
        is_admin=True,
    )

    class _UserQuery:
        @staticmethod
        def get(user_id):
            if user_id == 12:
                return admin_user
            return None

    class _UserModel:
        query = _UserQuery()

    @api_decorators.api_admin_required
    def _protected():
        return {"ok": True}, 200

    with app.test_request_context(
        "/api/v1/admin/providers",
        method="POST",
        headers={"Authorization": "Bearer ukg_abcdef_admin"},
    ):
        monkeypatch.setattr(
            api_decorators,
            "current_user",
            SimpleNamespace(is_authenticated=False),
        )
        monkeypatch.setattr(
            api_decorators.ExternalAPIKey,
            "verify_key",
            staticmethod(lambda _key: api_key_record),
        )
        monkeypatch.setattr(api_decorators, "User", _UserModel)

        body, status_code = _protected()
        assert status_code == 200
        assert body["ok"] is True


def test_get_authenticated_principal_prefers_resolved_auth_user(app, monkeypatch):
    """Shared API helpers should read the principal resolved by API decorators."""
    resolved_user = SimpleNamespace(id=21, is_authenticated=True)

    with app.test_request_context("/api/v1/user/data/summary", method="GET"):
        g.auth_user = resolved_user
        monkeypatch.setattr(
            api_decorators,
            "current_user",
            SimpleNamespace(id=99, is_authenticated=True),
        )

        assert api_decorators.get_authenticated_principal() is resolved_user


def test_mcp_tool_context_uses_external_api_key_principal(app):
    """MCP tool execution context should use API-key principals from g.auth_user."""
    from backend.routes import mcp_routes

    with app.test_request_context(
        "/api/v1/mcp/servers/server-1/tools/3/call",
        method="POST",
        headers={"X-Tenant-ID": "ignored-header-tenant"},
    ):
        g.auth_user = SimpleNamespace(id=42, tenant_id="tenant-from-user")
        g.external_api_key = SimpleNamespace(
            permissions={"connector_scopes": ["connector:github:read"]}
        )

        context = mcp_routes._build_tool_execution_context()

        assert context["user_id"] == "42"
        assert context["tenant_id"] == "tenant-from-user"
        assert "mcp:execute" in context["scopes"]
        assert "connector:github:read" in context["scopes"]
