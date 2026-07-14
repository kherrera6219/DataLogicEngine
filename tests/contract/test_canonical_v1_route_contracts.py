from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def session_authenticated_client(authenticated_client):
    return authenticated_client


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
        # NOTE: /api/v1/auth/{logout,mfa/setup,mfa/confirm,step-up} were removed
        # in the desktop-only auth refactor (commit "refactor(auth): remove dead
        # web-app auth routes; keep desktop-only endpoints"). They no longer
        # exist, so they are not part of the canonical authenticated-failure
        # contract. Desktop auth uses /api/v1/auth/desktop/*.
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


def test_graph_endpoint_uses_active_uskd_memory_graph(session_authenticated_client):
    from backend.storage.uskd_memory_graph import UskdMemoryGraph

    graph = UskdMemoryGraph()
    graph.add_pillar("pillar-1", name="Technology", data={"description": "Technology pillar"})
    graph.add_knowledge_node("node-1", title="AI Governance", axis_number=8)
    graph.add_relationship("pillar-1", "node-1", "HAS_KNOWLEDGE_NODE", weight=0.8)

    with patch("backend.storage.get_uskd_memory_graph", return_value=graph):
        response = session_authenticated_client.get("/api/v1/graph")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["source"] == "uskd_memory_graph"
    assert {node["id"] for node in payload["nodes"]} == {"pillar-1", "node-1"}
    nodes = {node["id"]: node for node in payload["nodes"]}
    assert nodes["pillar-1"]["pillar"] == "Technology"
    assert nodes["node-1"]["pillar"] == "Technology"
    assert payload["links"][0]["label"] == "HAS_KNOWLEDGE_NODE"
    assert payload["stats"]["source_revision"].startswith("sha256:")

    with patch("backend.storage.get_uskd_memory_graph", return_value=graph):
        axis_response = session_authenticated_client.get("/api/v1/graph?axis=8")
    assert {node["id"] for node in axis_response.get_json()["nodes"]} == {"pillar-1", "node-1"}

    with patch("backend.storage.get_uskd_memory_graph", return_value=graph):
        expanded = session_authenticated_client.get(
            "/api/v1/graph?root=node-1&depth=1"
        )
    assert {node["id"] for node in expanded.get_json()["nodes"]} == {
        "pillar-1",
        "node-1",
    }
    assert expanded.get_json()["scope"] == {"root": "node-1", "depth": 1}


def test_canonical_v1_retention_policies_authenticated_returns_ok(session_authenticated_client):
    # Single-mode / OS-level auth (auth deprecation Phase B): no admin gate on
    # retention policies — any authenticated owner can read them.
    response = session_authenticated_client.get("/api/v1/retention/policies")

    assert response.status_code == 200
    assert response.is_json


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
    # shared error_response wraps detail in body["error"]["message"];
    # accept both the old flat shape and the new envelope shape.
    error_val = body.get("error", "")
    error_msg = error_val.get("message", "") if isinstance(error_val, dict) else error_val
    assert error_msg == "Missing parameters" or body.get("message") == "Missing parameters"


def test_simulation_create_rejects_missing_scenario_query(session_authenticated_client):
    create_response = session_authenticated_client.post(
        "/api/v1/simulations",
        json={"name": "Missing scenario", "parameters": {"mode": "standard"}},
    )
    assert create_response.status_code == 422
    body = create_response.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_simulation_preflight_declares_hard_budget(session_authenticated_client):
    response = session_authenticated_client.post(
        "/api/v1/simulations/preflight",
        json={"query": "Evaluate this scenario", "depth": "deep", "seed": 42},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["scenario"]["contract_version"] == "dle-simulation.v1"
    assert data["scenario_revision"]
    assert data["plan"]["engine"] == "multi-agent-debate"
    assert data["plan"]["max_provider_calls"] == 7
    assert data["budget"]["max_total_tokens"] == 10_000
    assert data["budget"]["estimated_cost_usd"] is None
    assert data["budget"]["pricing_status"] == "unknown"


def test_canonical_v1_simulation_routes_expose_phase10_boundary(session_authenticated_client):
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
    assert create_body["data"]["contract_version"] == "dle-simulation.v1"
    assert create_body["data"]["plan"]["max_provider_calls"] == 5
    assert create_body["data"]["scenario_revision"]

    list_response = session_authenticated_client.get("/api/v1/simulations")
    assert list_response.status_code == 200
    list_body = list_response.get_json()
    assert list_body["success"] is True
    assert any(item["session_id"] == session_id for item in list_body["data"])

    runner = MagicMock()
    runner.live_state.return_value = None
    with patch(
        "backend.simulation.jobs.get_simulation_job_runner",
        return_value=runner,
    ):
        run_response = session_authenticated_client.post(
            f"/api/v1/simulations/{session_id}/run"
        )
        get_response = session_authenticated_client.get(
            f"/api/v1/simulations/{session_id}"
        )

    assert run_response.status_code == 202
    run_body = run_response.get_json()
    assert run_body["success"] is True
    assert run_body["data"]["status"] == "queued"
    runner.submit.assert_called_once_with(session_id)
    assert get_response.status_code == 200
    get_body = get_response.get_json()
    assert get_body["success"] is True
    assert get_body["data"]["session_id"] == session_id
    assert get_body["data"]["status"] == "queued"

    with patch(
        "backend.simulation.jobs.get_simulation_job_runner",
        return_value=runner,
    ):
        cancel_response = session_authenticated_client.post(
            f"/api/v1/simulations/{session_id}/cancel"
        )
    assert cancel_response.status_code == 202
    assert cancel_response.get_json()["data"]["status"] == "cancelled"
    runner.request_cancel.assert_called_once()
