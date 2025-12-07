from flask import Flask, Response

from backend.security.security_headers import configure_security_headers


def create_app(env="production"):
    app = Flask(__name__)
    app.config["TESTING"] = True

    configure_security_headers(app, {"ENV": env})

    @app.route("/text")
    def text_response():
        return "ok"

    @app.route("/api")
    def api_response():
        return Response("{}", mimetype="application/vnd.api+json")

    return app


def test_security_headers_enabled_in_production():
    app = create_app(env="production")
    client = app.test_client()

    response = client.get("/api")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Strict-Transport-Security"].startswith("max-age=31536000")
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"].startswith("geolocation=()")
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert response.headers["Cache-Control"].startswith("no-store")
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"


def test_security_headers_relaxed_in_development():
    app = create_app(env="development")
    client = app.test_client()

    response = client.get("/text")

    assert response.status_code == 200
    # HSTS should be omitted in development to avoid HTTPS issues locally
    assert "Strict-Transport-Security" not in response.headers
    # Development CSP allows wildcard sources for better DX
    csp_value = response.headers["Content-Security-Policy"]
    assert "script-src 'self' 'unsafe-inline' 'unsafe-eval' *" in csp_value
    assert "connect-src 'self' *" in csp_value
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

