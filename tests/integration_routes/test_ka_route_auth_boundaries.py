from types import SimpleNamespace

from backend.auth import api_decorators
from backend.routes import ka_routes
from tests.conftest import create_test_user


def _assert_json_unauthorized(response):
    assert response.status_code == 401
    body = response.get_json()
    assert body["success"] is False
    assert body["code"] == "UNAUTHORIZED"


class _FakeKAController:
    def __init__(self):
        self.algorithms = {
            "ka-001": {
                "metadata": {
                    "KA_ID": "KA-001",
                    "KA_Name": "Algorithm of Thought",
                    "Category": "Reasoning",
                    "Status": "Active",
                    "Risk_Class": "Low",
                }
            }
        }

    def get_available_algorithms(self):
        return self.algorithms

    def _normalize_ka_id(self, ka_id):
        return str(ka_id).lower()


def test_live_ka_routes_are_registered(app):
    """The active KA blueprint, not backend/api/ka_management.py, owns KA routes."""
    rules = {str(rule.rule) for rule in app.url_map.iter_rules()}

    assert "/api/v1/ka/algorithms" in rules
    assert "/api/ka/algorithms" in rules


def test_ka_algorithm_list_requires_json_auth(client):
    response = client.get("/api/v1/ka/algorithms")
    _assert_json_unauthorized(response)


def test_ka_health_remains_public(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())

    response = client.get("/api/v1/ka/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["total_algorithms"] == 1


def test_ka_algorithm_list_accepts_external_api_key(app, client, monkeypatch):
    with app.app_context():
        user_id = create_test_user(
            username="ka_api_key_user",
            email="ka_api_key_user@test.com",
        )

    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())
    monkeypatch.setattr(
        api_decorators.ExternalAPIKey,
        "verify_key",
        staticmethod(lambda _key: SimpleNamespace(user_id=user_id, permissions={"read": True})),
    )

    response = client.get(
        "/api/v1/ka/algorithms",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["algorithms"][0]["id"] == "KA-001"
