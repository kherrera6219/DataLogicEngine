from unittest.mock import MagicMock

import pytest

from app import app as flask_app, db
from extensions import limiter
from routes import simulation_routes as simulation_routes_module


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['RATELIMIT_ENABLED'] = False

    from limits.storage.memory import MemoryStorage
    limiter._storage = MemoryStorage()
    limiter.enabled = False

    with flask_app.app_context():
        db.create_all()
        try:
            from models import SimulationSession, User

            SimulationSession.query.delete()
            user = User.query.filter_by(username="testuser").first()
            if user is None:
                user = User(username="testuser", email="test@example.com", role="user")
                user.set_password("SecureTest789$#@")
                db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
        yield flask_app
        db.session.remove()


@pytest.fixture
def client(app):
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def session_authenticated_client(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_authenticated = True
    mock_user.is_admin = False
    mock_user.role = "user"
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user)
    return client


def test_canonical_v1_auth_failures_are_json_401s(client):
    cases = [
        ("GET", "/api/v1/graph", None),
        ("POST", "/api/v1/query", {}),
        ("POST", "/api/v1/simulation/run", {}),
        ("POST", "/api/v1/simulations", {}),
        ("GET", "/api/v1/analytics/overview", None),
        ("POST", "/api/v1/gdpr/export", None),
        ("POST", "/api/v1/privacy/purge-request", None),
        ("GET", "/api/v1/storage/health", None),
        ("POST", "/api/v1/persona/query", {"query": "test"}),
        ("GET", "/api/v1/trace/runs", None),
        ("GET", "/api/v1/retention/policies", None),
        ("POST", "/api/v1/auth/logout", {}),
        ("POST", "/api/v1/auth/mfa/setup", {}),
        ("POST", "/api/v1/auth/mfa/confirm", {"token": "123456"}),
        ("POST", "/api/v1/auth/step-up", {"token": "123456"}),
    ]

    for method, path, payload in cases:
        response = (
            client.open(path, method=method, json=payload)
            if payload is not None
            else client.open(path, method=method)
        )

        assert response.status_code == 401, f"Expected 401 for {method} {path}"
        assert response.is_json, f"Expected JSON response for {method} {path}"
        assert response.headers.get("Location") is None, f"Unexpected redirect for {method} {path}"
        body = response.get_json()
        assert body["code"] == "UNAUTHORIZED"
        assert "Authentication required" in body["message"]


def test_canonical_v1_retention_policies_non_admin_returns_json_403(session_authenticated_client):
    response = session_authenticated_client.get("/api/v1/retention/policies")

    assert response.status_code == 403
    assert response.is_json
    body = response.get_json()
    assert body["code"] == "FORBIDDEN"
    assert "Admin privileges required" in body["message"]


def test_canonical_v1_query_validation_returns_422(session_authenticated_client):
    response = session_authenticated_client.post("/api/v1/query", json={})

    assert response.status_code == 422
    body = response.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "query" in body["error"]["details"]["validation_errors"]


def test_canonical_v1_simulation_run_validation_returns_422(session_authenticated_client):
    response = session_authenticated_client.post("/api/v1/simulation/run", json={})

    assert response.status_code == 422
    body = response.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "query" in body["error"]["details"]["validation_errors"]


def test_canonical_v1_simulation_create_missing_parameters_returns_400(session_authenticated_client):
    response = session_authenticated_client.post("/api/v1/simulations", json={})

    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "Missing parameters"


def test_canonical_v1_simulation_routes_have_strict_happy_path_contract(session_authenticated_client, monkeypatch):
    monkeypatch.setattr(
        simulation_routes_module.engine,
        "process_query",
        lambda query, context: {"status": "completed", "final_conclusion": "ok"},
    )

    create_response = session_authenticated_client.post(
        "/api/v1/simulations",
        json={
            "name": "Contract Simulation",
            "query": "How does the canonical contract behave?",
            "sim_type": "standard",
        },
    )

    assert create_response.status_code == 201
    create_body = create_response.get_json()
    assert create_body["success"] is True
    session_id = create_body["data"]["session_id"]

    list_response = session_authenticated_client.get("/api/v1/simulations")
    assert list_response.status_code == 200
    list_body = list_response.get_json()
    assert list_body["success"] is True
    assert any(item["session_id"] == session_id for item in list_body["data"])

    run_response = session_authenticated_client.post(f"/api/v1/simulations/{session_id}/run")
    assert run_response.status_code == 200
    run_body = run_response.get_json()
    assert run_body["success"] is True
    assert run_body["data"]["status"] == "completed"

    get_response = session_authenticated_client.get(f"/api/v1/simulations/{session_id}")
    assert get_response.status_code == 200
    get_body = get_response.get_json()
    assert get_body["success"] is True
    assert get_body["data"]["session_id"] == session_id
