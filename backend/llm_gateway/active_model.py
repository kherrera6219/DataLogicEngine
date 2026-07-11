"""Resolve the user's selected cloud model and run a single completion.

This is the cloud-only replacement for the former local-Ollama path used by
internal steps (DSQP answer generation, defense-supervisor screening). The app
no longer ships local models, so these steps call the user's configured cloud
model — OpenAI ``gpt-5.5`` or Google ``gemini-3.1-pro-preview``.

Design contract
---------------
- **Best-effort, never raises.** Returns ``None`` when no cloud provider/key is
  configured or the call fails, so callers fall back to their deterministic
  (DSQP) or fail-open (defense supervisor) behavior.
- **Synchronous.** Callers run inside the async gateway pipeline, so the async
  SDK ``complete()`` is bridged to a sync call (using a worker thread when an
  event loop is already running).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Ensure the SDK is importable (mirrors gateway.py).
_SDK_PATH = str(Path(__file__).resolve().parent.parent.parent / "sdk" / "UKG_Python_SDK")
if _SDK_PATH not in sys.path:
    sys.path.insert(0, _SDK_PATH)

# Provider types the user can select. gpt-5.5 (openai) and gemini-3.1-pro-preview
# (google/gemini) are the only supported cloud models.
_CLOUD_TYPES: tuple[str, ...] = ("openai", "google", "gemini")


def _preferred_env_provider() -> str | None:
    """Return the configured env-provider preference, if one is supported."""
    preferred = (
        os.environ.get("LLM_DEFAULT_PROVIDER")
        or os.environ.get("AI_PROVIDER")
        or ""
    ).strip().lower()
    if preferred == "gemini":
        preferred = "google"
    return preferred if preferred in {"openai", "google"} else None


def resolve_active_cloud_model() -> Optional[tuple[str, str, str]]:
    """Return ``(provider_type, api_key, model)`` for the active cloud provider.

    Resolution order:
    1. The first active ``LLMProvider`` DB record of a cloud type with a stored
       key (keys saved through Settings).
    2. Environment keys (``OPENAI_API_KEY`` / ``GOOGLE_API_KEY`` /
       ``GEMINI_API_KEY``).

    Returns ``None`` when nothing is configured.
    """
    from backend.llm_gateway.model_defaults import (
        GOOGLE_LATEST_MODEL,
        OPENAI_LATEST_MODEL,
        default_model_for_provider,
    )

    preferred = _preferred_env_provider()

    # 1. DB-configured providers (best-effort, context-safe). An operator
    # default is authoritative for every internal model call, not only the
    # final gateway completion.
    try:
        from models import LLMProvider

        def _query() -> Optional[tuple[str, str, str]]:
            rows = (
                LLMProvider.query.filter_by(is_active=True)
                .order_by(LLMProvider.priority)
                .all()
            )
            if preferred:
                preferred_types = {preferred}
                if preferred == "google":
                    preferred_types.add("gemini")
                rows = [
                    row
                    for row in rows
                    if str(getattr(row, "provider_type", "") or "").strip().lower()
                    in preferred_types
                ]
            for row in rows:
                ptype = str(getattr(row, "provider_type", "") or "").strip().lower()
                if ptype not in _CLOUD_TYPES:
                    continue
                try:
                    key = row.get_api_key()
                except Exception:  # noqa: BLE001
                    key = None
                if not key:
                    continue
                model = str(getattr(row, "model_id", "") or "") or default_model_for_provider(ptype)
                return (ptype, key, model)
            return None

        from flask import current_app as _cur_app

        try:
            app = _cur_app._get_current_object()
        except RuntimeError:
            app = None
        if app is not None:
            with app.app_context():
                hit = _query()
        else:
            hit = _query()
        if hit:
            return hit
    except Exception as exc:  # noqa: BLE001
        logger.debug("Active cloud model resolution (DB) failed: %s", exc)

    # 2. Environment fallback.
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    providers = {
        "openai": ("openai", openai_key, OPENAI_LATEST_MODEL),
        "google": ("google", google_key, GOOGLE_LATEST_MODEL),
    }
    provider_order = [preferred] if preferred else []
    provider_order.extend(provider for provider in ("openai", "google") if provider != preferred)
    for provider in provider_order:
        provider_type, api_key, model = providers[provider]
        if api_key:
            return (provider_type, api_key, model)
    return None


def _run_coro_sync(coro):
    """Run *coro* to completion from sync code, even inside a running loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


def generate_with_active_model(
    prompt: str,
    *,
    system: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> Optional[str]:
    """Run one completion on the active cloud model. Returns text or ``None``.

    Never raises — any resolution/SDK/network failure returns ``None`` so the
    caller can fall back to its deterministic / fail-open path.
    """
    resolved = resolve_active_cloud_model()
    if not resolved:
        return None
    provider_type, api_key, model = resolved

    try:
        from ukg_sdk.providers import GoogleGeminiProvider, OpenAIProvider

        if provider_type in ("google", "gemini"):
            provider = GoogleGeminiProvider(api_key=api_key, model=model)
        else:
            provider = OpenAIProvider(api_key=api_key)

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async def _call():
            return await provider.complete(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        response = _run_coro_sync(_call())
        text = getattr(response, "text", None)
        return text if text else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("generate_with_active_model failed: %s", exc)
        return None
