from routes import simulation_routes as simulation_routes_module


def test_canonical_v1_auth_failures_are_json_401s(client):
    cases = [
        ("GET", "/api/v1/graph", None),
        ("POST", "/api/v1/query", {}),
        ("POST", "/api/v1/simulation/run", {}),
        ("POST", "/api/v1/simulations", {}),
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


def test_canonical_v1_query_validation_returns_422(authenticated_client):
    response = authenticated_client.post("/api/v1/query", json={})

    assert response.status_code == 422
    body = response.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "query" in body["error"]["details"]["validation_errors"]


def test_canonical_v1_simulation_run_validation_returns_422(authenticated_client):
    response = authenticated_client.post("/api/v1/simulation/run", json={})

    assert response.status_code == 422
    body = response.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "query" in body["error"]["details"]["validation_errors"]


def test_canonical_v1_simulation_create_missing_parameters_returns_400(authenticated_client):
    response = authenticated_client.post("/api/v1/simulations", json={})

    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "Missing parameters"


def test_canonical_v1_simulation_routes_have_strict_happy_path_contract(authenticated_client, monkeypatch):
    monkeypatch.setattr(
        simulation_routes_module.engine,
        "process_query",
        lambda query, context: {"status": "completed", "final_conclusion": "ok"},
    )

    create_response = authenticated_client.post(
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

    list_response = authenticated_client.get("/api/v1/simulations")
    assert list_response.status_code == 200
    list_body = list_response.get_json()
    assert list_body["success"] is True
    assert any(item["session_id"] == session_id for item in list_body["data"])

    run_response = authenticated_client.post(f"/api/v1/simulations/{session_id}/run")
    assert run_response.status_code == 200
    run_body = run_response.get_json()
    assert run_body["success"] is True
    assert run_body["data"]["status"] == "completed"

    get_response = authenticated_client.get(f"/api/v1/simulations/{session_id}")
    assert get_response.status_code == 200
    get_body = get_response.get_json()
    assert get_body["success"] is True
    assert get_body["data"]["session_id"] == session_id
