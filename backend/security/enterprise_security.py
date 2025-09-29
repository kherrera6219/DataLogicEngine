"""Security hardening utilities for the public web application."""
from __future__ import annotations

from flask import Flask, abort, request
from flask_talisman import Talisman

from config.enterprise_settings import EnterpriseSettings


DEFAULT_CSP = {
    "default-src": ["'self'"],
    "img-src": ["'self'", "data:"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "font-src": ["'self'", "data:"],
    "connect-src": ["'self'"],
}


def apply_enterprise_security(app: Flask, settings: EnterpriseSettings) -> None:
    """Apply HTTP hardening aligned with Microsoft SDL guidance."""

    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config["SESSION_COOKIE_SECURE"] = settings.enforce_https
    app.config["PREFERRED_URL_SCHEME"] = "https" if settings.enforce_https else "http"

    talisman_kwargs = {
        "force_https": settings.enforce_https,
        "strict_transport_security": settings.enforce_https,
        "strict_transport_security_preload": False,
        "strict_transport_security_max_age": 31536000,
        "content_security_policy": DEFAULT_CSP,
        "frame_options": "DENY",
        "session_cookie_secure": settings.enforce_https,
    }

    Talisman(app, **talisman_kwargs)

    if settings.allowed_hosts:
        allowed = set(settings.allowed_hosts)

        @app.before_request
        def _validate_host() -> None:  # pragma: no cover - simple guard
            host = request.host.split(":", 1)[0]
            if host not in allowed:
                abort(400)
