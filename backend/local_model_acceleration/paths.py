"""
Cache directory resolution for Local Model Acceleration.

All persistent files (SQLite DB, future embedding index) live under a
single root directory that is:

  Windows  %APPDATA%/DataLogicEngine/cache/local_model_acceleration/
  macOS/Linux  ~/.datalogicengine/cache/local_model_acceleration/

Override the root via DATALOGIC_ACCELERATION_CACHE_DIR (useful for CI or
when the operator wants cache on a specific drive).  The directory is
created on first access.
"""
from __future__ import annotations

import os
from pathlib import Path


def get_acceleration_cache_dir() -> Path:
    """Return (and create) the acceleration cache root directory."""
    explicit = os.environ.get("DATALOGIC_ACCELERATION_CACHE_DIR", "").strip()
    if explicit:
        root = Path(explicit)
    elif os.name == "nt":
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        root = Path(appdata) / "DataLogicEngine" / "cache" / "local_model_acceleration"
    else:
        root = Path.home() / ".datalogicengine" / "cache" / "local_model_acceleration"

    root.mkdir(parents=True, exist_ok=True)
    return root


def get_response_cache_path() -> Path:
    """Return the path to the SQLite exact-cache database."""
    return get_acceleration_cache_dir() / "llm_response_cache.db"
