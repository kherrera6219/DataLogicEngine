"""
CSRF token helpers for session-authenticated JSON API requests.
"""

from __future__ import annotations

import hmac
import os
import secrets
from typing import Optional, Tuple

from flask import request, session


API_CSRF_SESSION_KEY = "api_csrf_token"


def _env_truthy(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def is_api_csrf_enforced() -> bool:
    """Enable strict API CSRF enforcement by default in production."""
    is_production = (os.environ.get("FLASK_ENV") or "").strip().lower() == "production"
    return _env_truthy("ENFORCE_API_CSRF_TOKENS", is_production)


def get_or_create_api_csrf_token() -> str:
    token = session.get(API_CSRF_SESSION_KEY)
    if isinstance(token, str) and token:
        return token

    token = secrets.token_urlsafe(32)
    session[API_CSRF_SESSION_KEY] = token
    return token


def clear_api_csrf_token() -> None:
    session.pop(API_CSRF_SESSION_KEY, None)


def validate_api_csrf_request() -> Tuple[bool, Optional[str]]:
    expected = session.get(API_CSRF_SESSION_KEY)
    if not expected:
        return False, "CSRF session token missing"

    provided = (
        request.headers.get("X-CSRF-Token")
        or request.headers.get("X-XSRF-Token")
    )
    if not provided:
        return False, "CSRF request token missing"

    if not hmac.compare_digest(str(provided), str(expected)):
        return False, "CSRF request token invalid"

    return True, None
