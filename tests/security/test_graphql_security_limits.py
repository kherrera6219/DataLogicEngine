"""GraphQL must enforce production introspection, depth, and complexity limits."""

from __future__ import annotations


def test_graphql_introspection_is_disabled_by_policy(app, authenticated_client, monkeypatch):
    monkeypatch.setitem(app.config, "GRAPHQL_ALLOW_INTROSPECTION", False)

    response = authenticated_client.post(
        "/graphql",
        json={"query": "query { __schema { queryType { name } } }"},
    )

    assert response.status_code == 400
    assert response.get_json()["errors"][0]["code"] == "GRAPHQL_INTROSPECTION_DISABLED"


def test_graphql_depth_limit_rejects_before_execution(app, authenticated_client, monkeypatch):
    monkeypatch.setitem(app.config, "GRAPHQL_MAX_DEPTH", 2)

    response = authenticated_client.post(
        "/graphql",
        json={"query": "query { first { second { third } } }"},
    )

    assert response.status_code == 400
    assert response.get_json()["errors"][0]["code"] == "GRAPHQL_DEPTH_EXCEEDED"


def test_graphql_complexity_limit_rejects_before_execution(app, authenticated_client, monkeypatch):
    monkeypatch.setitem(app.config, "GRAPHQL_MAX_FIELDS", 3)

    response = authenticated_client.post(
        "/graphql",
        json={"query": "query { a: users { id } b: users { id } }"},
    )

    assert response.status_code == 400
    assert response.get_json()["errors"][0]["code"] == "GRAPHQL_COMPLEXITY_EXCEEDED"
