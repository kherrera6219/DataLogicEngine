"""Startup contract — documented, testable product boot expectations.

Phase 5: centralize flags and required product-path settings so ``create_app``
and desktop Electron can share one authority without reading ad-hoc env sites.
"""

from __future__ import annotations

import os
from typing import Any, Mapping


def env_flag(name: str, default: bool = False) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


# Product path defaults (owner gates 2026-08-12).
DEFAULT_LEGACY_API_PREFIXES = False
DEFAULT_ALLOW_LEGACY_APP = False
DEFAULT_GENERATIVE_LOCALITY = "cloud_byok"


def legacy_api_prefixes_enabled(config: Mapping[str, Any] | None = None) -> bool:
    if config is not None and "DLE_LEGACY_API_PREFIXES" in config:
        return bool(config.get("DLE_LEGACY_API_PREFIXES"))
    return env_flag("DLE_LEGACY_API_PREFIXES", DEFAULT_LEGACY_API_PREFIXES)


def allow_legacy_app() -> bool:
    if "PYTEST_CURRENT_TEST" in os.environ:
        return True
    return env_flag("DLE_ALLOW_LEGACY_APP", DEFAULT_ALLOW_LEGACY_APP)


def startup_contract_summary() -> dict[str, Any]:
    return {
        "entry": "app.create_app",
        "legacy_app_allowed": allow_legacy_app(),
        "legacy_api_prefixes": legacy_api_prefixes_enabled(),
        "generative_locality": DEFAULT_GENERATIVE_LOCALITY,
        "gateway_admin_prefix": "/api/v1/admin/gateway",
        "ops_admin_prefix": "/api/v1/admin",
        "openapi_authority": "docs/openapi.yaml",
        "policy": (
            "Desktop product boots create_app only. "
            "Legacy factories/prefixes are opt-in. "
            "Generative path is cloud BYOK (G-GEN=B0)."
        ),
    }
