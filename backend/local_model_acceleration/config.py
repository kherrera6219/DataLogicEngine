"""
Configuration dataclass for Local Model Acceleration.

Settings are loaded from runtime_settings.py (persisted JSON) and can be
overridden by environment variables for deployment / CI flexibility.

Phase 1 note: semantic cache is always disabled (``semantic_cache_enabled``
is hard-wired to ``False``).  The field exists so the Phase 2 toggle can
be added to the UI and API without schema changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LocalModelAccelerationConfig:
    """All tuneable knobs for the local model acceleration subsystem."""

    # Master switch — set False to bypass everything in manager.generate_with_cache
    enabled: bool = True

    # Keep-alive: send a lightweight ping to prevent model eviction from VRAM
    keepalive_enabled: bool = True
    keepalive_minutes: int = 60           # keep_alive param sent to Ollama (e.g. "60m")
    heartbeat_seconds: int = 240          # how often the daemon thread pings

    # Exact (deterministic) response cache
    exact_cache_enabled: bool = True
    cache_ttl_days: int = 30
    max_prompt_chars: int = 24_000        # prompts longer than this bypass cache

    # Semantic cache — Phase 2, always False in Phase 1
    semantic_cache_enabled: bool = False
    semantic_threshold: float = 0.92
    embedding_model: str = "nomic-embed-text"

    # Ollama connection
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_seconds: int = 10      # for health / list_models calls

    @classmethod
    def from_runtime_settings(cls) -> "LocalModelAccelerationConfig":
        """Build config from persisted settings + env-var overrides."""
        from backend.storage.runtime_settings import get_local_model_acceleration_settings

        s = get_local_model_acceleration_settings()

        keepalive_minutes = int(s.get("local_model_keepalive_minutes", 60))

        return cls(
            enabled=bool(s.get("local_model_acceleration_enabled", True)),
            keepalive_enabled=bool(s.get("local_model_keepalive_enabled", True)),
            keepalive_minutes=keepalive_minutes,
            heartbeat_seconds=int(s.get("local_model_heartbeat_seconds", 240)),
            exact_cache_enabled=bool(s.get("local_model_exact_cache_enabled", True)),
            cache_ttl_days=int(s.get("local_model_cache_ttl_days", 30)),
            max_prompt_chars=int(s.get("local_model_cache_max_prompt_chars", 24_000)),
            semantic_cache_enabled=False,  # Phase 2 lock
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_timeout_seconds=int(os.environ.get("OLLAMA_TIMEOUT", "10")),
        )

    @property
    def keep_alive_str(self) -> str:
        """Ollama keep_alive duration string, e.g. '60m'."""
        return f"{self.keepalive_minutes}m"
