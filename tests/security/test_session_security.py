import importlib


def test_session_cookie_security_defaults(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")

    app_module = importlib.import_module("app")
    importlib.reload(app_module)
    app = app_module.app

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] in {"Lax", "Strict", "None"}
    assert app.config["SESSION_COOKIE_SECURE"] is True
