"""
Local Model Acceleration Manager — public API surface.

This is the single orchestration point for Phase 1 features:

  1. **Keep-alive**: on every local-model request, registers the model with
     the keepalive thread so its VRAM residency is extended.

  2. **Exact response cache**: before calling the model, checks whether an
     identical request was answered before (within TTL).  On cache miss,
     calls the model and stores the response for next time.

The manager is designed to be a **fail-open** wrapper: if any internal
component raises (corrupt DB, OllamaClient timeout, import error), the
exception is caught and the call falls through to the real model.  This
guarantee is provided by the caller in gateway.py, not by this class.

Configuration is reloaded from runtime_settings on *every call* so that a
settings change in the UI takes effect without restarting the app.
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from backend.local_model_acceleration.config import LocalModelAccelerationConfig
from backend.local_model_acceleration.keepalive import LocalModelKeepAlive
from backend.local_model_acceleration.ollama_client import OllamaClient
from backend.local_model_acceleration.paths import get_response_cache_path
from backend.local_model_acceleration.response_cache import ResponseCache
from backend.local_model_acceleration.safety import should_cache_prompt

logger = logging.getLogger(__name__)

# Provider types that this manager handles.
_LOCAL_PROVIDER_TYPES: frozenset[str] = frozenset({"ollama", "local_slm", "vllm"})


class LocalModelAccelerationManager:
    """
    Orchestrates keep-alive and exact-cache for local LLM requests.

    Instantiate once (via the module-level singleton in ``__init__.py``)
    and call ``generate_with_cache`` on every gateway request that targets
    a local provider.
    """

    def __init__(self, config: LocalModelAccelerationConfig | None = None) -> None:
        cfg = config or LocalModelAccelerationConfig.from_runtime_settings()
        self._client = OllamaClient(
            base_url=cfg.ollama_base_url,
            timeout=cfg.ollama_timeout_seconds,
        )
        self._keepalive = LocalModelKeepAlive(self._client, cfg)
        self._response_cache = ResponseCache(get_response_cache_path())
        logger.debug(
            "LocalModelAccelerationManager initialised "
            "(exact_cache=%s, keepalive=%s)",
            cfg.exact_cache_enabled,
            cfg.keepalive_enabled,
        )

    # ------------------------------------------------------------------
    # Keepalive
    # ------------------------------------------------------------------

    def start_keepalive(self, model: str, provider_type: str = "ollama") -> None:
        """
        Register *model* with the keepalive thread.

        Silently ignores non-local provider types so the caller does not
        need to check before calling.

        Settings are reloaded on every call (matching generate_with_cache)
        so a UI keepalive toggle or heartbeat change applies without an
        app restart.
        """
        if provider_type not in _LOCAL_PROVIDER_TYPES:
            return
        try:
            cfg = LocalModelAccelerationConfig.from_runtime_settings()
            self._keepalive.update_config(cfg)
            if not cfg.keepalive_enabled:
                self._keepalive.stop()
                return
            self._keepalive.start(model)
        except Exception as exc:  # noqa: BLE001
            logger.debug("start_keepalive error (non-fatal): %s", exc)

    def stop_keepalive(self) -> None:
        """Stop the keepalive daemon (called on app shutdown or settings disable)."""
        try:
            self._keepalive.stop()
        except Exception as exc:  # noqa: BLE001
            logger.debug("stop_keepalive error (non-fatal): %s", exc)

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def cache_stats(self) -> dict[str, Any]:
        """Return current cache statistics for the /status API endpoint."""
        return self._response_cache.stats()

    def cache_clear(self) -> dict[str, Any]:
        """Wipe all cached responses.  Returns count of deleted rows."""
        deleted = self._response_cache.clear_all()
        return {"deleted_rows": deleted}

    def cache_purge_expired(self) -> dict[str, Any]:
        """Remove expired rows and return count."""
        deleted = self._response_cache.delete_expired()
        return {"deleted_rows": deleted}

    def invalidate_cache_on_knowledge_update(
        self, collection: str = "", source: str = "unknown"
    ) -> dict[str, Any]:
        """
        Evict all RAG-grounded cached responses after a knowledge-base update.

        Call this from the ingestion pipeline immediately after new documents
        are successfully written to ChromaDB.  Direct-LLM cached responses
        (where no RAG context was used) are preserved.

        Parameters
        ----------
        collection:
            The ChromaDB collection name that was updated (logged only —
            not used for filtering because the cache stores context hashes,
            not collection names).
        source:
            Short string identifying the call site (e.g. ``"ingest_document"``)
            for log correlation.

        Returns dict with ``deleted_rows`` and ``collection`` keys.
        """
        logger.info(
            "Knowledge-base update detected (source=%s, collection=%r) — "
            "invalidating RAG-grounded cache entries.",
            source,
            collection or "unspecified",
        )
        deleted = self._response_cache.invalidate_all_rag_responses()
        return {"deleted_rows": deleted, "collection": collection}

    def invalidate_cache_for_rag_context(self, rag_ctx_sha256: str) -> dict[str, Any]:
        """
        Evict cached responses for a specific RAG context hash.

        Use this when the gateway re-runs retrieval for a prompt, obtains a
        different context, and needs to replace the stale cache entry.

        Parameters
        ----------
        rag_ctx_sha256:
            Full 64-char SHA-256 hex digest of the RAG context to evict.
        """
        deleted = self._response_cache.invalidate_by_rag_ctx_sha(rag_ctx_sha256)
        return {"deleted_rows": deleted, "rag_ctx_sha256_prefix": rag_ctx_sha256[:12]}

    # ------------------------------------------------------------------
    # Core: generate with cache
    # ------------------------------------------------------------------

    async def generate_with_cache(
        self,
        *,
        provider_type: str,
        model_name: str,
        task_type: str,
        prompt: str,
        rag_context: str = "",
        system: str | None = None,
        options: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        call_model: Callable[[], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """
        Try the exact cache, then fall through to *call_model* on miss.

        Parameters
        ----------
        provider_type:
            Lowercase provider type (``"ollama"``, ``"local_slm"``, ``"vllm"``).
        model_name:
            Exact model name as configured in the gateway.
        task_type:
            Routing task type from request.meta or request.mode.
        prompt:
            The final user query (post-governance, pre-system-prompt merge).
        rag_context:
            The RAG chunks injected into this request (empty string for direct
            calls).  Included in the cache key so different RAG retrievals
            don't collide.
        system:
            System prompt, if any (included in cache key hash).
        options:
            Dict with at minimum ``temperature``, ``max_tokens``,
            ``run_ukg_pipeline``, ``mode``.
        metadata:
            ``request.meta`` dict forwarded from the gateway.
        call_model:
            Async callable that executes the real LLM call.  Must be called
            at most once.  Must return the standard gateway result dict.

        Returns
        -------
        The standard gateway result dict, with an extra ``_acceleration``
        key describing what happened (cache_hit, source, etc.).  The caller
        (gateway.py) is responsible for popping ``_acceleration`` and storing
        it in ``request.meta``.
        """
        # Reload config on every call so UI changes take effect immediately.
        config = LocalModelAccelerationConfig.from_runtime_settings()

        if not config.enabled:
            result = await call_model()
            result.setdefault(
                "_acceleration",
                {"acceleration_enabled": False, "cache_hit": False, "source": "model"},
            )
            return result

        # --- Safety check ------------------------------------------------
        cacheable, skip_reason = should_cache_prompt(
            prompt=prompt,
            task_type=task_type,
            metadata=metadata,
            max_prompt_chars=config.max_prompt_chars,
        )

        # --- Exact cache lookup -----------------------------------------
        cache_key: str | None = None
        if config.exact_cache_enabled and cacheable:
            cache_key = ResponseCache.build_cache_key(
                model_name=model_name,
                provider_type=provider_type,
                task_type=task_type,
                system=system,
                prompt=prompt,
                rag_context=rag_context,
                options=options,
            )
            hit = self._response_cache.get(cache_key)
            if hit is not None:
                logger.debug(
                    "Exact cache HIT model=%s task=%s key=%.12s…",
                    model_name,
                    task_type,
                    cache_key,
                )
                return {
                    "ok": True,
                    "answer": hit["response"],
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                    "explainability": {},
                    "warnings": [],
                    "tier": None,
                    "layers": None,
                    "trace": None,
                    "coordinate": None,
                    "error": None,
                    "_acceleration": {
                        "acceleration_enabled": True,
                        "cache_hit": True,
                        "source": "exact_cache",
                        "cache_key_prefix": cache_key[:12],
                        "original_run_id": hit["metadata"].get("original_run_id") if hit.get("metadata") else None,
                    },
                }

        # --- Cache miss: call the model ---------------------------------
        result = await call_model()

        # --- Store successful response ----------------------------------
        answer = result.get("answer", "")
        if (
            config.exact_cache_enabled
            and cacheable
            and cache_key is not None
            and answer
            and result.get("ok", True)
        ):
            try:
                self._response_cache.set(
                    cache_key=cache_key,
                    response=answer,
                    metadata={
                        "model": model_name,
                        "task_type": task_type,
                        "original_run_id": (metadata or {}).get("run_id")
                    },
                    ttl_days=config.cache_ttl_days,
                    model_name=model_name,
                    provider_type=provider_type,
                    task_type=task_type,
                    system=system,
                    prompt=prompt,
                    rag_context=rag_context,
                    options=options,
                )
                logger.debug(
                    "Exact cache WRITE model=%s task=%s key=%.12s…",
                    model_name,
                    task_type,
                    cache_key,
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug("Cache write error (non-fatal): %s", exc)

        result.setdefault(
            "_acceleration",
            {
                "acceleration_enabled": config.enabled,
                "cache_hit": False,
                "source": "model",
                "skip_reason": skip_reason,
            },
        )
        return result

    # ------------------------------------------------------------------
    # Ollama status (for the /status API endpoint)
    # ------------------------------------------------------------------

    def ollama_status(self) -> dict[str, Any]:
        """Return Ollama reachability and current keepalive model."""
        health = self._client.health_check()
        return {
            "ollama_reachable": health["ok"],
            "installed_models": health["models"],
            "keepalive_model": self._keepalive.current_model,
            "error": health.get("error"),
        }
