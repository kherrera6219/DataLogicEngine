"""Unit tests for shared CORS policy resolution safety guarantees.

These tests protect production CORS hardening behavior and ensure local
developer defaults remain usable when explicit origins are not configured.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


_MODULE_PATH = Path(__file__).resolve().parents[2] / "backend" / "utils" / "cors_policy.py"
_SPEC = importlib.util.spec_from_file_location("dle_cors_policy", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load cors_policy module from {_MODULE_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

DEFAULT_LOCAL_ORIGINS = _MODULE.DEFAULT_LOCAL_ORIGINS
resolve_service_cors_policy = _MODULE.resolve_service_cors_policy


def test_resolve_service_cors_policy_defaults_to_local_in_non_production(monkeypatch):
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    origins, allow_credentials = resolve_service_cors_policy(
        preferred_env_var="CORS_ORIGINS",
        fallback_env_var="CORS_ORIGINS",
    )

    assert origins == list(DEFAULT_LOCAL_ORIGINS)
    assert allow_credentials is True


def test_resolve_service_cors_policy_rejects_wildcard_in_production(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(RuntimeError):
        resolve_service_cors_policy(
            preferred_env_var="CORS_ORIGINS",
            fallback_env_var="CORS_ORIGINS",
        )


def test_resolve_service_cors_policy_parses_explicit_origins(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com, https://admin.example.com")

    origins, allow_credentials = resolve_service_cors_policy(
        preferred_env_var="CORS_ORIGINS",
        fallback_env_var="CORS_ORIGINS",
    )

    assert origins == ["https://app.example.com", "https://admin.example.com"]
    assert allow_credentials is True
