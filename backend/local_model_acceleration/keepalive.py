"""
Keep-alive daemon thread for local Ollama models.

When a local model finishes a generation, Ollama's default idle timer begins
counting down (usually 5 minutes).  If no further request arrives before the
timer expires the model is evicted from VRAM — meaning the *next* request
must wait for a full model reload (~5-30 s for 7B-14B quantised weights).

This module runs a background daemon thread that sends a 1-token generation
every ``heartbeat_seconds`` seconds, resetting Ollama's eviction timer.

Design notes
------------
- One thread per manager instance.  The manager is a singleton so there is
  effectively one keepalive thread per process.
- Only one model is kept warm at a time — the most-recently-used one.
  Warming multiple models would consume GPU memory for rarely-used tiers.
- All errors are swallowed: if Ollama is offline the heartbeat simply skips
  until the next interval.
- The thread is a daemon thread so it never prevents process exit.
"""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.local_model_acceleration.config import LocalModelAccelerationConfig
    from backend.local_model_acceleration.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

_KEEPALIVE_PROMPT = "hi"   # minimal token; Ollama still resets idle timer
_KEEPALIVE_OPTIONS = {"num_predict": 1, "temperature": 0}


class LocalModelKeepAlive:
    """
    Background daemon that keeps the most-recently-used local model warm.

    Usage::

        kl = LocalModelKeepAlive(client, config)
        kl.start("gemma4:latest")     # called by manager on each request
        kl.stop()                     # called on shutdown / settings disable
    """

    def __init__(
        self,
        client: "OllamaClient",
        config: "LocalModelAccelerationConfig",
    ) -> None:
        self._client = client
        self._config = config

        self._current_model: str | None = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, model: str) -> None:
        """
        Set *model* as the model to keep warm and ensure the thread is running.

        Safe to call on every gateway request — the thread is only started
        once and the model name is updated atomically.
        """
        if not self._config.keepalive_enabled:
            return

        with self._lock:
            self._current_model = model

        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="lma-keepalive",
                daemon=True,
            )
            self._thread.start()
            logger.debug("Keep-alive thread started for model: %s", model)

    def stop(self) -> None:
        """Signal the keepalive thread to exit cleanly."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None
        logger.debug("Keep-alive thread stopped.")

    def update_config(self, config: "LocalModelAccelerationConfig") -> None:
        """Swap in fresh settings; takes effect on the next heartbeat."""
        self._config = config

    @property
    def current_model(self) -> str | None:
        """Return the model currently being kept warm (thread-safe read)."""
        with self._lock:
            return self._current_model

    # ------------------------------------------------------------------
    # Thread body
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Daemon thread: ping the current model every heartbeat_seconds.

        Config values are re-read every iteration so ``update_config``
        swaps (heartbeat interval, keep-alive duration) take effect on
        the next heartbeat without a thread restart.
        """
        while not self._stop_event.wait(timeout=self._config.heartbeat_seconds):
            keep_alive_str = self._config.keep_alive_str
            with self._lock:
                model = self._current_model

            if model is None:
                continue

            try:
                result = self._client.generate(
                    model=model,
                    prompt=_KEEPALIVE_PROMPT,
                    keep_alive=keep_alive_str,
                    options=_KEEPALIVE_OPTIONS,
                )
                if result["ok"]:
                    logger.debug(
                        "Keep-alive ping ✓ model=%s latency=%dms keep_alive=%s",
                        model,
                        result.get("latency_ms", 0),
                        keep_alive_str,
                    )
                else:
                    logger.debug(
                        "Keep-alive ping failed (non-fatal) model=%s: %s",
                        model,
                        result.get("error"),
                    )
            except Exception as exc:  # noqa: BLE001
                # Completely non-fatal — Ollama may have been restarted.
                logger.debug("Keep-alive ping exception (non-fatal): %s", exc)
