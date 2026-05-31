"""
Integration tests for previously-uncovered route modules.

Covers: user_data, ingestion (route layer), search, settings, storage,
retention, privacy, location, and multimodal routes at the HTTP level.

Blueprint names discovered from the live app: auth_api, user_data,
settings_api (N/A — settings is under storage_api), storage_api,
ingestion_api, search_api, retention, privacy, location_api,
multimodal_api, compliance_api, feature_flags, knowledge_api,
notifications.
"""

import json
import os

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ.setdefault("SECRET_KEY", "test-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt")
os.environ.setdefault("OPENAI_API_KEY", "mock-key")
os.environ.setdefault("USE_REDIS", "False")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("IS_DESKTOP_APP", "true")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, app):
    """Register and log in a test user, returning the user_id."""
    from models import User
    from extensions import db

    with app.app_context():
        user = User(username="routeuser", email="route@test.com")
        user.set_password("SecureRoute!1")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client.post("/api/v1/auth/login", json={
        "username": "routeuser",
        "password": "SecureRoute!1",
    })
    return user_id


# ====================================================================
# 1. User Data Routes  (/api/v1/user/data/*)
# ====================================================================

class TestUserDataRoutes:
    """Integration tests for routes/user_data_routes.py."""

    def test_export_requires_auth(self, client):
        resp = client.get("/api/v1/user/data/export")
        assert resp.status_code in (401, 302, 403)

    def test_summary_requires_auth(self, client):
        resp = client.get("/api/v1/user/data/summary")
        assert resp.status_code in (401, 302, 403)

    def test_delete_requires_auth(self, client):
        resp = client.post(
            "/api/v1/user/data/delete",
            json={"confirm": "DELETE"},
        )
        assert resp.status_code in (401, 302, 403)

    def test_export_authenticated(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/user/data/export")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "profile" in data
        assert "version" in data

    def test_summary_authenticated(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/user/data/summary")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("success") is True
        assert "data_summary" in body.get("data", {})

    def test_delete_requires_confirmation(self, app, client):
        _login(client, app)
        resp = client.post(
            "/api/v1/user/data/delete",
            json={"confirm": "nope"},
        )
        assert resp.status_code == 400

    def test_delete_with_confirmation(self, app, client):
        _login(client, app)
        resp = client.post(
            "/api/v1/user/data/delete",
            json={"confirm": "DELETE"},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("success") is True


# ====================================================================
# 2. Ingestion Route Layer  (/api/v1/ingestion/*)
# ====================================================================

class TestIngestionRoutes:
    """Integration tests for backend/routes/ingestion_routes.py."""

    def test_supported_requires_auth(self, client):
        resp = client.get("/api/v1/ingestion/supported")
        assert resp.status_code in (401, 302, 403)

    def test_supported_returns_extensions(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/ingestion/supported")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("success") is True
        exts = body["data"]["extensions"]
        assert ".txt" in exts
        assert ".md" in exts

    def test_history_returns_list(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/ingestion/history")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("success") is True
        # history.data may have manifests key or be an empty list
        data = body.get("data", {})
        assert isinstance(data, (dict, list))

    def test_local_ingest_rejects_nonexistent_path(self, app, client):
        _login(client, app)
        resp = client.post(
            "/api/v1/ingestion/local",
            json={"source_path": "/nonexistent/path/to/nowhere"},
        )
        # Should fail gracefully (not 500 without a stack trace)
        assert resp.status_code in (400, 404, 500)


# ====================================================================
# 3. Search Routes  (/api/search/*)
# ====================================================================

class TestSearchRoutes:
    """Integration tests for backend/routes/search_routes.py."""

    def test_search_nodes_requires_auth(self, client):
        resp = client.get("/api/search/nodes?q=test")
        assert resp.status_code in (401, 302, 403)

    def test_search_nodes_requires_query(self, app, client):
        _login(client, app)
        resp = client.get("/api/search/nodes")
        assert resp.status_code == 400

    def test_search_nodes_rejects_short_query(self, app, client):
        _login(client, app)
        resp = client.get("/api/search/nodes?q=a")
        assert resp.status_code == 400

    def test_search_nodes_valid(self, app, client):
        _login(client, app)
        resp = client.get("/api/search/nodes?q=knowledge")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("success") is True or "results" in body

    def test_global_search(self, app, client):
        _login(client, app)
        resp = client.get("/api/search/global?q=compliance")
        assert resp.status_code == 200


# ====================================================================
# 4. Storage Routes  (/api/v1/storage/*)
# ====================================================================

class TestStorageRoutes:
    """Integration tests for backend/routes/storage_routes.py."""

    def test_storage_health_requires_auth(self, client):
        resp = client.get("/api/v1/storage/health")
        assert resp.status_code in (401, 302, 403)

    def test_storage_health(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/storage/health")
        assert resp.status_code == 200

    def test_desktop_metrics(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/storage/desktop-metrics")
        assert resp.status_code in (200, 403)

    def test_desktop_flags(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/storage/desktop-flags")
        assert resp.status_code in (200, 403)

    def test_test_connection(self, app, client):
        _login(client, app)
        resp = client.post(
            "/api/v1/storage/test-connection",
            json={"service": "sqlite"},
        )
        assert resp.status_code in (200, 400, 403)


# ====================================================================
# 5. Retention Routes  (/api/v1/retention/*)
# ====================================================================

class TestRetentionRoutes:
    """Integration tests for backend/routes/retention_routes.py."""

    def test_retention_policies_requires_auth(self, client):
        resp = client.get("/api/v1/retention/policies")
        assert resp.status_code in (401, 302, 403)

    def test_retention_policies(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/retention/policies")
        # May require admin role (403) or return policies (200)
        assert resp.status_code in (200, 403)

    def test_retention_health(self, app, client):
        _login(client, app)
        resp = client.get("/api/v1/retention/health")
        assert resp.status_code in (200, 403)


# ====================================================================
# 6. Privacy Routes  (/api/v1/privacy/*)
# ====================================================================

class TestPrivacyRoutes:
    """Integration tests for backend/routes/privacy_routes.py."""

    def test_purge_request_requires_auth(self, client):
        resp = client.post("/api/v1/privacy/purge-request")
        assert resp.status_code in (401, 302, 403, 405)

    def test_tenant_cleanup_requires_auth(self, client):
        resp = client.post("/api/v1/privacy/tenant-cleanup")
        assert resp.status_code in (401, 302, 403, 405)


# ====================================================================
# 7. Location Routes  (/api/locations/*)
# ====================================================================

class TestLocationRoutes:
    """Integration tests for backend/routes/location_routes.py."""

    def test_locations_list_requires_auth(self, client):
        resp = client.get("/api/locations")
        assert resp.status_code in (401, 302, 403)

    def test_locations_list(self, app, client):
        _login(client, app)
        resp = client.get("/api/locations")
        assert resp.status_code in (200, 403)

    def test_locations_hierarchy(self, app, client):
        _login(client, app)
        resp = client.get("/api/locations/hierarchy")
        assert resp.status_code in (200, 403)


# ====================================================================
# 8. Multimodal Routes  (/api/v1/multimodal/*)
# ====================================================================

class TestMultimodalRoutes:
    """Integration tests for backend/routes/multimodal_routes.py."""

    def test_document_process_requires_auth(self, client):
        resp = client.post("/api/v1/multimodal/document/process")
        assert resp.status_code in (401, 302, 403)

    def test_audio_transcribe_requires_auth(self, client):
        resp = client.post("/api/v1/multimodal/audio/transcribe")
        assert resp.status_code in (401, 302, 403)

    def test_video_analyze_requires_auth(self, client):
        resp = client.post("/api/v1/multimodal/video/analyze")
        assert resp.status_code in (401, 302, 403)

    def test_document_process_rejects_empty(self, app, client):
        _login(client, app)
        resp = client.post("/api/v1/multimodal/document/process")
        # Missing file → 400 or 415
        assert resp.status_code in (400, 415)


# ====================================================================
# 9. Route registration sanity
# ====================================================================

class TestRouteRegistration:
    """Verify that all expected route blueprints are registered."""

    def test_critical_blueprints_registered(self, app):
        registered = set(app.blueprints.keys())
        # Use actual blueprint names from the live app
        critical = {
            "auth_api", "user_data", "search_api", "ingestion_api",
            "storage_api", "retention", "privacy", "multimodal_api",
        }
        for bp in critical:
            assert bp in registered, f"Blueprint '{bp}' not registered"

    def test_health_endpoint_accessible(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_api_auth_login_exists(self, client):
        resp = client.post("/api/v1/auth/login", json={})
        # Should return 400 (bad request) not 404 (not found)
        assert resp.status_code != 404
