"""Enterprise-grade configuration helpers for the DataLogicEngine web stack.

This module consolidates configuration management in a way that aligns with
Microsoft enterprise guidance.  The helpers exposed here provide a
single-location for environment driven configuration, sensible defaults for
local development, and guard rails for production workloads.
"""
from __future__ import annotations

import os
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Tuple


_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_allowed_hosts(raw: str | None) -> Tuple[str, ...]:
    if not raw:
        return tuple()
    return tuple(host.strip() for host in raw.split(",") if host.strip())


@dataclass(frozen=True)
class EnterpriseSettings:
    """Strongly-typed view of the application settings."""

    environment: str
    session_secret: str
    database_url: str | None
    enforce_https: bool
    allowed_hosts: Tuple[str, ...]
    app_insights_connection_string: str | None
    request_logging_enabled: bool
    log_level: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def logging_config(self) -> Dict[str, object]:
        """Return a dictConfig payload for structured logging."""

        base_format = (
            "%(asctime)sZ | %(levelname)s | %(name)s | %(message)s | "
            "correlation_id=%(correlation_id)s"
        )

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {
                    "format": base_format,
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            },
            "filters": {
                "correlation": {
                    "()": "config.enterprise_settings.RequestCorrelationFilter",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "structured",
                    "filters": ["correlation"],
                }
            },
            "root": {
                "level": self.log_level,
                "handlers": ["console"],
            },
        }


class RequestCorrelationFilter:
    """Ensure log records have a correlation identifier."""

    def filter(self, record):  # type: ignore[override]
        if not hasattr(record, "correlation_id"):
            record.correlation_id = _correlation_id.get()
        return True


@lru_cache(maxsize=1)
def get_settings() -> EnterpriseSettings:
    environment = os.environ.get("APP_ENVIRONMENT", "development").lower()
    session_secret = os.environ.get("SESSION_SECRET", "change-me")
    database_url = os.environ.get("DATABASE_URL")
    enforce_https = _parse_bool(os.environ.get("ENFORCE_HTTPS"), default=environment == "production")
    allowed_hosts = _parse_allowed_hosts(os.environ.get("ALLOWED_HOSTS"))
    app_insights = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    request_logging_enabled = _parse_bool(os.environ.get("REQUEST_LOGGING"), default=True)
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    return EnterpriseSettings(
        environment=environment,
        session_secret=session_secret,
        database_url=database_url,
        enforce_https=enforce_https,
        allowed_hosts=allowed_hosts,
        app_insights_connection_string=app_insights,
        request_logging_enabled=request_logging_enabled,
        log_level=log_level,
    )


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def clear_correlation_id() -> None:
    _correlation_id.set("-")
