"""
Shared ASGI middleware for FastAPI security and request correlation.
"""

from __future__ import annotations

import os
import uuid
from typing import Callable

from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware


def _is_development() -> bool:
    runtime = (os.environ.get("FLASK_ENV") or os.environ.get("ENV") or "").strip().lower()
    return runtime in {"development", "dev", "testing", "test"}


class CorrelationAndSecurityMiddleware(BaseHTTPMiddleware):
    """Apply correlation IDs and baseline security headers for FastAPI services."""

    def __init__(self, app, service_name: str = "service"):
        super().__init__(app)
        self.service_name = service_name
        self.is_development = _is_development()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        response.headers.setdefault("X-Correlation-ID", correlation_id)
        response.headers.setdefault("X-Request-ID", correlation_id)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        if not self.is_development:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )

        return response


def apply_standard_fastapi_middleware(app, service_name: str) -> None:
    """Attach shared FastAPI middleware stack."""
    app.add_middleware(CorrelationAndSecurityMiddleware, service_name=service_name)
