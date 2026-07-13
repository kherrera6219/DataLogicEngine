import json


def test_graphql_node_and_edge_counts(authenticated_client):
    response = authenticated_client.post("/graphql", json={"query": "{ nodeCount edgeCount }"})
    assert response.status_code == 200

    payload = response.get_json()
    assert "errors" not in payload
    assert payload["data"]["nodeCount"] == 0
    assert payload["data"]["edgeCount"] == 0


def test_gdpr_export_returns_json(authenticated_client):
    response = authenticated_client.post("/api/v1/gdpr/export")
    assert response.status_code == 200
    assert response.mimetype == "application/json"

    payload = json.loads(response.data.decode("utf-8"))
    assert payload["user_profile"]["username"] == "testuser"
    assert payload["user_profile"]["email"] == "test@example.com"
