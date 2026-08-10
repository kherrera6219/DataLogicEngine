"""Resolve storage endpoints from the active app-owned runtime first."""

from __future__ import annotations

import os
from typing import Any


def _active_config() -> dict[str, Any] | None:
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            return current_app.config
    except (ImportError, RuntimeError):
        return None
    return None


def runtime_redis_url(default: str = "redis://127.0.0.1:6379/0") -> str:
    config = _active_config()
    if config is not None:
        managed = config.get("DLE_REDIS_URL")
        if managed:
            return str(managed)
    return os.environ.get("REDIS_URL", default)


def runtime_neo4j_settings() -> tuple[str, str, str]:
    config = _active_config()
    if config is not None and config.get("DLE_NEO4J_URI"):
        return (
            str(config["DLE_NEO4J_URI"]),
            str(config["DLE_NEO4J_USER"]),
            str(config["DLE_NEO4J_PASSWORD"]),
        )
    return (
        os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"),
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", "password"),
    )
