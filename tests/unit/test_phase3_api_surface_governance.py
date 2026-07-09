from app import _legacy_api_successor_path


def test_legacy_successor_path_maps_known_prefixes():
    assert _legacy_api_successor_path("/api/compliance/frameworks") == "/api/v1/compliance/frameworks"
    assert _legacy_api_successor_path("/api/simulations") == "/api/v1/simulations"
    assert _legacy_api_successor_path("/api/simulations/abc/run") == "/api/v1/simulations/abc/run"
    assert _legacy_api_successor_path("/api/ka/algorithms/ka-001/execute") == "/api/v1/ka/algorithms/ka-001/execute"
    assert _legacy_api_successor_path("/api/mcp/servers/test/tools") == "/api/v1/mcp/servers/test/tools"
    assert _legacy_api_successor_path("/api/persona/query") == "/api/v1/persona/query"
    assert _legacy_api_successor_path("/api/pillar/mappings") == "/api/v1/pillar/mappings"
    assert _legacy_api_successor_path("/api/truth/health") == "/api/v1/truth/health"
    assert _legacy_api_successor_path("/api/ukg/pillars") == "/api/v1/pillars"
    assert _legacy_api_successor_path("/api/v1/ukg/pillars") == "/api/v1/pillars"
    assert _legacy_api_successor_path("/api/admin/providers") is None
    assert _legacy_api_successor_path("/api/search/global") is None
    assert _legacy_api_successor_path("/api/v1/simulations") is None


def test_legacy_simulation_alias_emits_deprecation_headers(authenticated_client):
    response = authenticated_client.post(
        "/api/simulations",
        json={
            "name": "Legacy Alias",
            "query": "Explain the current policy delta",
            "sim_type": "standard",
        },
    )

    assert response.status_code == 201
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "Wed, 30 Sep 2026 00:00:00 GMT"
    assert response.headers["X-DataLogicEngine-Route-Status"] == "legacy"
    assert "/api/v1/simulations" in response.headers.get("Link", "")


def test_legacy_truth_alias_emits_deprecation_headers(client):
    response = client.get("/api/truth/health")

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "Wed, 30 Sep 2026 00:00:00 GMT"
    assert response.headers["X-DataLogicEngine-Route-Status"] == "legacy"
    assert "/api/v1/truth/health" in response.headers.get("Link", "")


def test_legacy_ukg_alias_emits_deprecation_headers(authenticated_client):
    response = authenticated_client.get("/api/ukg/pillars")

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "Wed, 30 Sep 2026 00:00:00 GMT"
    assert response.headers["X-DataLogicEngine-Route-Status"] == "legacy"
    assert "/api/v1/pillars" in response.headers.get("Link", "")


def test_legacy_v1_ukg_alias_emits_deprecation_headers(authenticated_client):
    response = authenticated_client.get("/api/v1/ukg/pillars")

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
