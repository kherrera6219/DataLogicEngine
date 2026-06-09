"""
Local Model Acceleration — package entry point.

Exports a module-level singleton accessor so the gateway and API can call::

    from backend.local_model_acceleration import get_local_model_acceleration_manager
    manager = get_local_model_acceleration_manager()

The singleton is initialised lazily on first access (not at import time)
so that module load doesn't trigger DB creation or Ollama probes during
test collection.
"""
from __future__ import annotations

import threading
from typing import Optional

from backend.local_model_acceleration.manager import LocalModelAccelerationManager

_manager: Optional[LocalModelAccelerationManager] = None
_manager_lock = threading.Lock()


def get_local_model_acceleration_manager() -> LocalModelAccelerationManager:
    """Return the process-wide LocalModelAccelerationManager singleton."""
    global _manager  # noqa: PLW0603
    if _manager is None:
        with _manager_lock:
            if _manager is None:  # double-checked locking
                _manager = LocalModelAccelerationManager()
    return _manager


__all__ = ["get_local_model_acceleration_manager", "LocalModelAccelerationManager"]
