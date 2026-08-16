"""Legacy API surface governance.

Default product boot has legacy /api/* mirrors OFF (DLE_LEGACY_API_PREFIXES).
Deprecation-header tests build a temporary app with legacy mirrors enabled.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app import _legacy_api_successor_path, create_app
from tests._helpers import authenticate_client_session, TEST_DATABASE_URL


def test_legacy_successor_path_maps_known_prefixes():
    assert (
        _legacy_api_successor_path("/api/compliance/frameworks")
        == "/api/v1/regulatory/frameworks"
    )
    assert _legacy_api_successor_path("/api/simulations") == "/api/v1/simulations"
    assert (
        _legacy_api_successor_path("/api/simulations/abc/run")
        == "/api/v1/simulations/abc/run"
    )
    assert (
        _legacy_api_successor_path("/api/ka/algorithms/ka-001/execute")
        == "/api/v1/ka/algorithms/ka-001/execute"
    )
    assert (
        _legacy_api_successor_path("/api/mcp/servers/test/tools")
        == "/api/v1/mcp/servers/test/tools"
    )
    assert _legacy_api_successor_path("/api/persona/query") == "/api/v1/persona/query"
    assert (
        _legacy_api_successor_path("/api/pillar/mappings") == "/api/v1/pillar/mappings"
    )
    assert _legacy_api_successor_path("/api/truth/health") == "/api/v1/truth/health"
    assert _legacy_api_successor_path("/api/ukg/pillars") == "/api/v1/pillars"
    assert _legacy_api_successor_path("/api/v1/ukg/pillars") == "/api/v1/pillars"
    assert _legacy_api_successor_path("/api/admin/providers") is None
    assert _legacy_api_successor_path("/api/search/global") is None
    assert _legacy_api_successor_path("/api/v1/simulations") is None


@pytest.fixture
def legacy_client(tmp_path, monkeypatch):
    """App with legacy /api/* mirrors registered for deprecation-header tests."""
    monkeypatch.setenv("DLE_LEGACY_API_PREFIXES", "true")
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DLE_TESTING", "true")
    app = create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'legacy.db'}",
            "DLE_RUNTIME_ROOT": str(tmp_path / "runtime"),
            "DLE_INITIALIZE_SCHEMA": True,
            "DLE_INITIALIZE_STORES": False,
            "DLE_START_MANAGED_SERVICES": False,
            "DLE_START_BACKGROUND_WORKERS": False,
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "DLE_LEGACY_API_PREFIXES": True,
        },
        start_runtime=False,
    )
    app.config["DLE_LEGACY_API_PREFIXES"] = True
    client = app.test_client()
    with app.app_context():
        from extensions import db
        from models import User
        from werkzeug.security import generate_password_hash

        db.create_all()
        # Avoid email encryption path (needs dle_encryption_manager).
        user = User()
        user.username = "legacy-tester"
        user._email = "legacy@example.com"
        user.password_hash = generate_password_hash("test-password-not-used")
        user.active = True
        db.session.add(user)
        db.session.commit()
        authenticate_client_session(client, user.id)
    yield client


def test_legacy_simulation_alias_emits_deprecation_headers(legacy_client):
    # List is enough to prove the legacy mirror is registered and tagged;
    # POST create requires a full accepting runtime (covered on /api/v1).
    response = legacy_client.get("/api/simulations")

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "Wed, 30 Sep 2026 00:00:00 GMT"
    assert response.headers["X-DataLogicEngine-Route-Status"] == "legacy"
    assert "/api/v1/simulations" in response.headers.get("Link", "")


def test_legacy_truth_alias_emits_deprecation_headers(legacy_client):
    response = legacy_client.get("/api/truth/health")

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "Wed, 30 Sep 2026 00:00:00 GMT"
    assert response.headers["X-DataLogicEngine-Route-Status"] == "legacy"
    assert "/api/v1/truth/health" in response.headers.get("Link", "")


def test_legacy_ukg_alias_emits_deprecation_headers(legacy_client):
    response = legacy_client.get("/api/ukg/pillars")

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "Wed, 30 Sep 2026 00:00:00 GMT"
    assert response.headers["X-DataLogicEngine-Route-Status"] == "legacy"
    assert "/api/v1/pillars" in response.headers.get("Link", "")


def test_legacy_v1_ukg_alias_emits_deprecation_headers(legacy_client):
    response = legacy_client.get("/api/v1/ukg/pillars")

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "Wed, 30 Sep 2026 00:00:00 GMT"
    assert response.headers["X-DataLogicEngine-Route-Status"] == "legacy"
    assert "/api/v1/pillars" in response.headers.get("Link", "")


def test_canonical_simulation_route_has_no_deprecation_headers(authenticated_client):
    response = authenticated_client.get("/api/v1/simulations")

    assert response.status_code == 200
    assert "Deprecation" not in response.headers
    assert "Sunset" not in response.headers
    assert response.headers.get("X-DataLogicEngine-Route-Status") != "legacy"


def test_legacy_routes_absent_when_flag_off(authenticated_client):
    """Default product path: legacy mirrors are not registered."""
    assert authenticated_client.get("/api/truth/health").status_code == 404
    assert authenticated_client.get("/api/v1/truth/health").status_code == 200
