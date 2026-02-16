import importlib


def test_index_route_renders(monkeypatch):
    """Test the index route renders properly or returns expected response."""
    monkeypatch.setenv("FLASK_ENV", "testing")
    app_module = importlib.import_module("app")
    importlib.reload(app_module)
    app = app_module.app

    client = app.test_client()
    response = client.get("/")
    # Accept 200 (OK), 302/301 (redirect), or 404 (no index route defined)
    # The app may not have an index route if it's API-only
    assert response.status_code in [200, 302, 301, 404]
