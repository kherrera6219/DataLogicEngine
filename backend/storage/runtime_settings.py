"""
Runtime storage settings persistence.

Stores user-editable storage preferences in a small JSON file so desktop
behavior (like database auto-start) can persist across restarts.
"""

from __future__ import annotations

import json
import os
from typing import Any


DEFAULT_STORAGE_SETTINGS: dict[str, Any] = {
    "auto_start_databases": True,
    "local_slm_audit_mode": True,
    "offline_queue_enabled": True,
    # Local Model Acceleration (Phase 1)
    "local_model_acceleration_enabled": True,
    "local_model_keepalive_enabled": True,
    "local_model_exact_cache_enabled": True,
    "local_model_semantic_cache_enabled": False,  # Phase 2 — always False for now
    "local_model_keepalive_minutes": 60,
    "local_model_heartbeat_seconds": 240,
    "local_model_cache_ttl_days": 30,
    "local_model_cache_max_prompt_chars": 24000,
}


def _settings_file_path() -> str:
    """Resolve the runtime settings path for the current OS."""
    explicit_path = os.environ.get("DATALOGIC_STORAGE_SETTINGS_PATH")
    if explicit_path:
        return explicit_path

    if os.name == "nt":
        base_dir = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")),
            "DataLogicEngine",
        )
    else:
        base_dir = os.path.join(os.path.expanduser("~"), ".datalogicengine")

    return os.path.join(base_dir, "storage_settings.json")


def load_storage_settings() -> dict[str, Any]:
    """Load runtime settings from disk with safe defaults."""
    path = _settings_file_path()
    settings: dict[str, Any] = dict(DEFAULT_STORAGE_SETTINGS)

    if not os.path.exists(path):
        return settings

    try:
        with open(path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            settings.update(loaded)
    except Exception:
        # Keep defaults on malformed or unreadable files.
        return settings

    settings["auto_start_databases"] = bool(settings.get("auto_start_databases", True))
    settings["local_slm_audit_mode"] = bool(settings.get("local_slm_audit_mode", True))
    settings["offline_queue_enabled"] = bool(settings.get("offline_queue_enabled", True))
    # Local Model Acceleration — type-normalize
    settings["local_model_acceleration_enabled"] = bool(settings.get("local_model_acceleration_enabled", True))
    settings["local_model_keepalive_enabled"] = bool(settings.get("local_model_keepalive_enabled", True))
    settings["local_model_exact_cache_enabled"] = bool(settings.get("local_model_exact_cache_enabled", True))
    settings["local_model_semantic_cache_enabled"] = False  # Phase 2 lock
    settings["local_model_keepalive_minutes"] = int(settings.get("local_model_keepalive_minutes", 60))
    settings["local_model_heartbeat_seconds"] = int(settings.get("local_model_heartbeat_seconds", 240))
    settings["local_model_cache_ttl_days"] = int(settings.get("local_model_cache_ttl_days", 30))
    settings["local_model_cache_max_prompt_chars"] = int(settings.get("local_model_cache_max_prompt_chars", 24000))
    return settings


def save_storage_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Persist runtime settings to disk and return normalized settings."""
    normalized = dict(DEFAULT_STORAGE_SETTINGS)
    normalized.update(settings)
    normalized["auto_start_databases"] = bool(normalized.get("auto_start_databases", True))
    normalized["local_slm_audit_mode"] = bool(normalized.get("local_slm_audit_mode", True))
    normalized["offline_queue_enabled"] = bool(normalized.get("offline_queue_enabled", True))
    # Local Model Acceleration — type-normalize on save
    normalized["local_model_acceleration_enabled"] = bool(normalized.get("local_model_acceleration_enabled", True))
    normalized["local_model_keepalive_enabled"] = bool(normalized.get("local_model_keepalive_enabled", True))
    normalized["local_model_exact_cache_enabled"] = bool(normalized.get("local_model_exact_cache_enabled", True))
    normalized["local_model_semantic_cache_enabled"] = False  # Phase 2 lock
    normalized["local_model_keepalive_minutes"] = int(normalized.get("local_model_keepalive_minutes", 60))
    normalized["local_model_heartbeat_seconds"] = int(normalized.get("local_model_heartbeat_seconds", 240))
    normalized["local_model_cache_ttl_days"] = int(normalized.get("local_model_cache_ttl_days", 30))
    normalized["local_model_cache_max_prompt_chars"] = int(normalized.get("local_model_cache_max_prompt_chars", 24000))

    path = _settings_file_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2)

    return normalized


def get_auto_start_databases() -> bool:
    """Return whether local databases should auto-start in desktop mode."""
    settings = load_storage_settings()
    return bool(settings.get("auto_start_databases", True))


def set_auto_start_databases(enabled: bool) -> bool:
    """Update and persist the auto-start preference."""
    settings = load_storage_settings()
    settings["auto_start_databases"] = bool(enabled)
    persisted = save_storage_settings(settings)
    return bool(persisted.get("auto_start_databases", True))


def get_local_slm_audit_mode() -> bool:
    """Return whether LocalSLM answers should carry explicit audit metadata."""
    settings = load_storage_settings()
    return bool(settings.get("local_slm_audit_mode", True))


def set_local_slm_audit_mode(enabled: bool) -> bool:
    """Update and persist the LocalSLM audit-mode preference."""
    settings = load_storage_settings()
    settings["local_slm_audit_mode"] = bool(enabled)
    persisted = save_storage_settings(settings)
    return bool(persisted.get("local_slm_audit_mode", True))


def get_offline_queue_enabled() -> bool:
    """Return whether desktop failed chat requests should be queued locally."""
    settings = load_storage_settings()
    return bool(settings.get("offline_queue_enabled", True))


def set_offline_queue_enabled(enabled: bool) -> bool:
    """Update and persist the desktop offline queue preference."""
    settings = load_storage_settings()
    settings["offline_queue_enabled"] = bool(enabled)
    persisted = save_storage_settings(settings)
    return bool(persisted.get("offline_queue_enabled", True))


# ---------------------------------------------------------------------------
# Local Model Acceleration settings
# ---------------------------------------------------------------------------

def get_local_model_acceleration_settings() -> dict[str, Any]:
    """Return all local-model-acceleration settings as a flat dict."""
    s = load_storage_settings()
    return {
        "local_model_acceleration_enabled": bool(s.get("local_model_acceleration_enabled", True)),
        "local_model_keepalive_enabled": bool(s.get("local_model_keepalive_enabled", True)),
        "local_model_exact_cache_enabled": bool(s.get("local_model_exact_cache_enabled", True)),
        "local_model_semantic_cache_enabled": False,  # Phase 2 lock
        "local_model_keepalive_minutes": int(s.get("local_model_keepalive_minutes", 60)),
        "local_model_heartbeat_seconds": int(s.get("local_model_heartbeat_seconds", 240)),
        "local_model_cache_ttl_days": int(s.get("local_model_cache_ttl_days", 30)),
        "local_model_cache_max_prompt_chars": int(s.get("local_model_cache_max_prompt_chars", 24000)),
    }


def save_local_model_acceleration_settings(patch: dict[str, Any]) -> dict[str, Any]:
    """Merge *patch* into stored settings, persist, and return the full result."""
    settings = load_storage_settings()
    _allowed = {
        "local_model_acceleration_enabled",
        "local_model_keepalive_enabled",
        "local_model_exact_cache_enabled",
        "local_model_keepalive_minutes",
        "local_model_heartbeat_seconds",
        "local_model_cache_ttl_days",
        "local_model_cache_max_prompt_chars",
    }
    for key, value in patch.items():
        if key in _allowed:
            settings[key] = value
    save_storage_settings(settings)
    return get_local_model_acceleration_settings()


def get_local_model_acceleration_enabled() -> bool:
    """Fast single-field read — avoids loading the full settings dict in hot path."""
    settings = load_storage_settings()
    return bool(settings.get("local_model_acceleration_enabled", True))
