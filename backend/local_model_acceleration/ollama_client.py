"""
Thin synchronous HTTP wrapper around the Ollama REST API.

This is the canonical Ollama client for the entire Local Model Acceleration
subsystem.  It replaces the ad-hoc ``GET /api/tags`` calls that were
previously duplicated across OllamaProvider.health_check() and
tier_availability.probe_local_tiers().

Only the endpoints needed by this subsystem are implemented:
  - health_check   → GET /api/tags (side-effect: also returns model list)
  - list_models    → model names parsed from health_check response
  - generate       → POST /api/generate  (used for keep-alive pings)
  - unload_model   → POST /api/generate with keep_alive="0m"

All methods return structured dicts and never raise — errors are captured
in the returned ``error`` field.  This keeps keepalive and cache code
simple (no try/except at the call site).
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Low-level HTTP client for Ollama.  Thread-safe (no shared state)."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 10) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Health / model list
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """
        GET /api/tags — returns health status and installed model names.

        Returns::

            {
                "ok": True,
                "models": ["gemma4:latest", "qwen3:14b"],
                "raw": <full Ollama response dict>,
                "error": None,
            }
        """
        try:
            import requests  # local import keeps module loadable without requests at import time

            resp = requests.get(
                f"{self._base}/api/tags",
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return {"ok": True, "models": models, "raw": data, "error": None}
        except Exception as exc:  # noqa: BLE001
            logger.debug("Ollama health_check failed: %s", exc)
            return {"ok": False, "models": [], "raw": {}, "error": str(exc)}

    def list_models(self) -> list[str]:
        """Return a list of installed model names (empty if Ollama unreachable)."""
        return self.health_check()["models"]

    # ------------------------------------------------------------------
    # Generate (keep-alive ping + future direct use)
    # ------------------------------------------------------------------

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        keep_alive: str = "60m",
        options: dict[str, Any] | None = None,
        stream: bool = False,
        system: str | None = None,
        format_json: bool = False,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """
        POST /api/generate — run a non-streaming generation request.

        Used by keepalive to ping the model with a 1-token response so
        Ollama resets its idle-eviction timer, and by the defense
        supervisor for local JSON-mode security screening.

        ``stream=True`` is not supported (the response parser expects a
        single JSON body, not NDJSON) and returns an error dict.
        ``timeout_seconds`` overrides the default generation timeout of
        ``max(client timeout, 30)`` for latency-sensitive callers.

        Returns::

            {
                "ok": True,
                "response": "<model output>",
                "latency_ms": 123,
                "raw": <full Ollama response dict>,
                "error": None,
            }
        """
        if stream:
            return {
                "ok": False,
                "response": "",
                "latency_ms": 0,
                "raw": {},
                "error": "OllamaClient.generate does not support stream=True (NDJSON not parsed)",
            }

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": keep_alive,
        }
        if options:
            payload["options"] = options
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        t0 = time.monotonic()
        try:
            import requests

            resp = requests.post(
                f"{self._base}/api/generate",
                json=payload,
                timeout=timeout_seconds or max(self._timeout, 30),
            )
            resp.raise_for_status()
            data = resp.json()
            latency_ms = int((time.monotonic() - t0) * 1000)
            return {
                "ok": True,
                "response": data.get("response", ""),
                "latency_ms": latency_ms,
                "raw": data,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.debug("Ollama generate failed (model=%s): %s", model, exc)
            return {
                "ok": False,
                "response": "",
                "latency_ms": latency_ms,
                "raw": {},
                "error": str(exc),
            }

    def unload_model(self, model: str) -> dict[str, Any]:
        """
        Evict *model* from VRAM by sending keep_alive="0m".

        This is the Ollama-recommended way to free memory immediately.
        """
        logger.debug("Unloading Ollama model from VRAM: %s", model)
        return self.generate(
            model=model,
            prompt="",
            keep_alive="0m",
            options={"num_predict": 0},
        )
