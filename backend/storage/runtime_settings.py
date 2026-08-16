"""
Runtime storage settings persistence.

Stores user-editable storage preferences in a small JSON file so desktop
behavior (like database auto-start) can persist across restarts.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from backend.security.dpapi_store import decrypt_data, encrypt_data
from backend.security.windows_acl import ensure_restricted_user_acl


DEFAULT_STORAGE_SETTINGS: dict[str, Any] = {
    "auto_start_databases": True,
    "local_slm_audit_mode": True,
    "offline_queue_enabled": True,
    # Local Model Acceleration — disabled (G-GEN=B0 cloud BYOK generative).
    # Settings keys retained for migration/read compatibility only.
    "local_model_acceleration_enabled": False,
    "local_model_keepalive_enabled": False,
    "local_model_exact_cache_enabled": False,
    "local_model_semantic_cache_enabled": False,
    "local_model_keepalive_minutes": 60,
    "local_model_heartbeat_seconds": 240,
    "local_model_cache_ttl_days": 30,
    "local_model_cache_max_prompt_chars": 24000,
}

PROTECTED_CLOUD_SETTING_KEYS = frozenset(
    {
        "postgres_url",
        "redis_url",
        "neo4j_uri",
        "pinecone_api_key",
        "s3_access_key",
        "s3_secret_key",
    }
)
DPAPI_SETTING_PREFIX = "dpapi:v1:"


def _production_desktop_mode() -> bool:
    return (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        and os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
    )


def _protect_cloud_settings(cloud: Any) -> dict[str, Any]:
    if not isinstance(cloud, dict):
        return {}
    protected = dict(cloud)
    for key in PROTECTED_CLOUD_SETTING_KEYS:
        value = protected.get(key)
        if value is None or value == "":
            continue
        text = str(value)
        if text.startswith(DPAPI_SETTING_PREFIX):
            continue
        encrypted = encrypt_data(text)
        if not encrypted:
            raise RuntimeError(f"DPAPI is required to persist protected storage setting {key}")
        protected[key] = f"{DPAPI_SETTING_PREFIX}{encrypted}"
    return protected


def _unprotect_cloud_settings(cloud: Any) -> dict[str, Any]:
    if not isinstance(cloud, dict):
        return {}
    unprotected = dict(cloud)
    for key in PROTECTED_CLOUD_SETTING_KEYS:
        value = unprotected.get(key)
        if not isinstance(value, str) or not value.startswith(DPAPI_SETTING_PREFIX):
            continue
        decrypted = decrypt_data(value.removeprefix(DPAPI_SETTING_PREFIX))
        if not decrypted:
            raise RuntimeError(f"Protected storage setting {key} could not be decrypted")
        unprotected[key] = decrypted
    return unprotected


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

    settings["cloud_config"] = _unprotect_cloud_settings(settings.get("cloud_config"))
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
    normalized["cloud_config"] = _protect_cloud_settings(normalized.get("cloud_config"))
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
    dir_name = os.path.dirname(path)
    os.makedirs(dir_name, exist_ok=True)
    # Atomic write (RT-10): serialize to a temp file in the same directory, then
    # os.replace() into place. A crash mid-write can no longer truncate/corrupt
    # the live settings file (load_storage_settings() would otherwise catch the
    # JSON error and silently fall back to defaults, losing saved preferences).
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".storage_settings.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2)
        os.replace(tmp_path, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        ensure_restricted_user_acl(path, required=_production_desktop_mode())
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

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
