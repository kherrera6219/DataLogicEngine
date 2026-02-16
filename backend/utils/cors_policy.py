"""
Shared CORS policy resolution for service entrypoints.
"""

from __future__ import annotations

import os
from typing import Iterable


DEFAULT_LOCAL_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "app://-",
)


def _parse_origins(raw_origins: str | Iterable[str] | None) -> list[str]:
    if raw_origins is None:
        return []

    if isinstance(raw_origins, str):
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    if isinstance(raw_origins, (list, tuple, set)):
        return [str(origin).strip() for origin in raw_origins if str(origin).strip()]

    return []


def _is_production() -> bool:
    env = (os.environ.get("FLASK_ENV") or os.environ.get("ENV") or "").strip().lower()
    return env == "production"


def resolve_service_cors_policy(
    *,
    preferred_env_var: str = "FASTAPI_CORS_ORIGINS",
    fallback_env_var: str = "CORS_ORIGINS",
) -> tuple[list[str], bool]:
    """
    Resolve CORS origins for FastAPI services with production-safe defaults.

    Returns:
        (origins, allow_credentials)
    """
    raw_origins = os.environ.get(preferred_env_var) or os.environ.get(fallback_env_var)
    origins = _parse_origins(raw_origins)

    if _is_production() and (not origins or "*" in origins):
        raise RuntimeError(
            f"{preferred_env_var} (or {fallback_env_var}) must be explicitly configured in production"
        )

    if not origins:
        origins = list(DEFAULT_LOCAL_ORIGINS)

    allow_credentials = "*" not in origins
    return origins, allow_credentials
