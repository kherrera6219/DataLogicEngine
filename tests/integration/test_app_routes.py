import importlib


def test_index_route_renders(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    app_module = importlib.import_module("app")
    importlib.reload(app_module)
    app = app_module.app

    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
