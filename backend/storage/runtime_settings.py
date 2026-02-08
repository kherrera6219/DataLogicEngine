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
    return settings


def save_storage_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Persist runtime settings to disk and return normalized settings."""
    normalized = dict(DEFAULT_STORAGE_SETTINGS)
    normalized.update(settings)
    normalized["auto_start_databases"] = bool(normalized.get("auto_start_databases", True))

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

