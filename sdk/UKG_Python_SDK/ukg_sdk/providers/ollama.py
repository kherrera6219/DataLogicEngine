"""
OllamaProvider — full-featured Ollama client for DataLogicEngine.

Uses the OpenAI-compatible endpoint at ``<base_url>/v1`` for all chat calls
and Ollama's native ``/api/tags`` for health and model listing.

Public API
----------
health_check()          GET /api/tags  → liveness + installed model inventory
list_models()           → sorted list of model name strings
chat_async()            POST /v1/chat/completions (non-streaming)
chat_stream_async()     POST /v1/chat/completions (SSE streaming) → yields str chunks
generate_json_async()   chat + JSON parse + retry + optional schema validation
complete()              LLMProvider ABC bridge → delegates to chat_async()

Constants
---------
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL    = "gemma4:12b"
OLLAMA_FAST_MODEL       = "gemma4:latest"
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# ── Public constants ──────────────────────────────────────────────────────────
OLLAMA_DEFAULT_BASE_URL: str = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL: str = "gemma4:12b"
OLLAMA_FAST_MODEL: str = "gemma4:latest"

# Ollama's OpenAI-compat endpoint requires *some* Bearer token, but ignores the
# value.  Using the conventional dummy "ollama" makes logs readable.
_DUMMY_API_KEY: str = "ollama"


@dataclass(frozen=True)
class OllamaModelInfo:
    """Metadata for a single installed Ollama model (subset of /api/tags entry)."""
    name: str
    size_gb: float
    modified_at: str


class OllamaProvider(LLMProvider):
    """
    Full-featured Ollama provider using the OpenAI-compatible chat endpoint.

    Parameters
    ----------
    base_url:
        Ollama base URL.  The OpenAI-compat subpath (``/v1``) is appended
        automatically.  Both ``http://localhost:11434`` and
        ``http://localhost:11434/v1`` are accepted — the ``/v1`` suffix is
        stripped if present to keep a single source of truth.
    default_model:
        Model used when the caller does not pin a specific model.
    fast_model:
        Lighter model used by ``generate_json_async()`` and quick-path calls.
    timeout_s:
        Per-request HTTP timeout in seconds (default 120 s for large-model
        generation; health checks use a hard-coded 5 s timeout).
    """

    DEFAULT_MODEL: str = OLLAMA_DEFAULT_MODEL
    FAST_MODEL: str = OLLAMA_FAST_MODEL

    def __init__(
        self,
        base_url: str = OLLAMA_DEFAULT_BASE_URL,
        default_model: str = OLLAMA_DEFAULT_MODEL,
        fast_model: str = OLLAMA_FAST_MODEL,
        timeout_s: float = 120.0,
    ) -> None:
        # Accept both bare base URL and OAI-compat URL
        cleaned = base_url.rstrip("/")
        if cleaned.endswith("/v1"):
            cleaned = cleaned[:-3]
        self._base_url: str = cleaned
        self._oai_url: str = f"{cleaned}/v1"
        self.default_model: str = default_model
        self.fast_model: str = fast_model
        self._timeout = aiohttp.ClientTimeout(total=timeout_s)
        self._auth_headers: Dict[str, str] = {
            "Authorization": f"Bearer {_DUMMY_API_KEY}",
            "Content-Type": "application/json",
        }

    # ── LLMProvider ABC ───────────────────────────────────────────────────────

    async def complete(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """
        ``LLMProvider`` ABC implementation — delegates to :meth:`chat_async`.

        This is the entry point used by the UKG gateway's ``_direct_llm_call``
        and ``UKGOverlay``.  All Ollama-specific callers should prefer
        :meth:`chat_async` directly so the ``model`` parameter can be
        ``Optional[str]`` and fall back to :attr:`default_model`.
        """
        return await self.chat_async(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # ── Health & discovery ────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """
        Probe Ollama at ``GET /api/tags``.

        Returns
        -------
        dict
            ``ok`` (bool), ``models`` (list[str]), ``model_infos``
            (list[OllamaModelInfo]).  On failure, ``error`` (str) is added and
            ``ok`` is False.
        """
        url = f"{self._base_url}/api/tags"
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return {
                            "ok": False,
                            "models": [],
                            "model_infos": [],
                            "error": f"HTTP {resp.status}: {text[:200]}",
                        }
                    data = await resp.json()
                    raw_models: List[Dict[str, Any]] = data.get("models", [])
                    names = [m["name"] for m in raw_models]
                    infos = [
                        OllamaModelInfo(
                            name=m["name"],
                            size_gb=round(m.get("size", 0) / 1_000_000_000, 2),
                            modified_at=m.get("modified_at", ""),
                        )
                        for m in raw_models
                    ]
                    return {"ok": True, "models": names, "model_infos": infos}
        except aiohttp.ClientConnectorError as exc:
            return {
                "ok": False,
                "models": [],
                "model_infos": [],
                "error": (
                    f"Cannot connect to Ollama at {self._base_url} — "
                    f"is `ollama serve` running? ({exc})"
                ),
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "models": [], "model_infos": [], "error": str(exc)}

    async def list_models(self) -> List[str]:
        """
        Return a sorted list of installed Ollama model names.

        Wraps :meth:`health_check`; returns ``[]`` instead of raising when
        Ollama is unreachable.
        """
        result = await self.health_check()
        return sorted(result.get("models", []))

    # ── Chat (non-streaming) ──────────────────────────────────────────────────

    async def chat_async(
        self,
        *,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """
        Non-streaming chat completion via ``POST /v1/chat/completions``.

        On any error (connection refused, non-200 HTTP, malformed response) an
        :class:`~ukg_sdk.providers.base.LLMResponse` with ``raw["ok"] = False``
        is returned — never raised — so the gateway circuit-breaker can handle
        failover transparently.

        Parameters
        ----------
        messages:
            OpenAI-style message list, e.g.
            ``[{"role": "user", "content": "Hello"}]``.
        model:
            Overrides :attr:`default_model`.
        temperature:
            Sampling temperature (0.0–1.0).
        max_tokens:
            Maximum output tokens.
        """
        target = model or self.default_model
        url = f"{self._oai_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": target,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with aiohttp.ClientSession(
                timeout=self._timeout, headers=self._auth_headers
            ) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(
                            "Ollama chat/%s HTTP %s: %s",
                            target,
                            resp.status,
                            error_text[:300],
                        )
                        return LLMResponse(
                            text="",
                            raw={
                                "ok": False,
                                "retryable": resp.status >= 500,
                                "error": f"Ollama HTTP {resp.status}: {error_text[:300]}",
                            },
                        )

                    data = await resp.json()
                    content: str = data["choices"][0]["message"]["content"]
                    usage: Dict[str, Any] = data.get("usage", {})
                    return LLMResponse(
                        text=content,
                        model=target,
                        usage=usage,
                        raw=data,
                    )

        except aiohttp.ClientConnectorError as exc:
            logger.error("Ollama connection refused (%s): %s", self._base_url, exc)
            return LLMResponse(
                text="",
                raw={
                    "ok": False,
                    "retryable": True,
                    "error": (
                        f"Cannot connect to Ollama at {self._base_url} — "
                        "is `ollama serve` running?"
                    ),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Ollama chat exception: %s", exc)
            return LLMResponse(
                text="", raw={"ok": False, "retryable": False, "error": str(exc)}
            )

    # ── Chat (streaming) ──────────────────────────────────────────────────────

    async def chat_stream_async(
        self,
        *,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """
        Streaming chat completion via ``POST /v1/chat/completions``
        with ``stream=True``.

        Yields
        ------
        str
            Text *delta* chunks as they arrive from the SSE stream.  The
            ``[DONE]`` sentinel is consumed and not yielded.  On connection
            or HTTP errors a single ``[ERROR: …]`` string is yielded so
            callers can detect failure without needing a try/except.
        """
        target = model or self.default_model
        url = f"{self._oai_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": target,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with aiohttp.ClientSession(
                timeout=self._timeout, headers=self._auth_headers
            ) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(
                            "Ollama stream/%s HTTP %s", target, resp.status
                        )
                        yield f"[ERROR: Ollama HTTP {resp.status}: {error_text[:200]}]"
                        return

                    async for raw_line in resp.content:
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if not line or not line.startswith("data: "):
                            continue
                        payload_str = line[6:]  # strip "data: " prefix
                        if payload_str.strip() == "[DONE]":
                            return
                        try:
                            chunk = json.loads(payload_str)
                            delta = chunk["choices"][0].get("delta", {})
                            text_piece: Optional[str] = delta.get("content")
                            if text_piece:
                                yield text_piece
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue  # malformed SSE line — skip silently

        except aiohttp.ClientConnectorError as exc:
            logger.error("Ollama stream connection refused: %s", exc)
            yield "[ERROR: Cannot connect to Ollama — is `ollama serve` running?]"
        except Exception as exc:  # noqa: BLE001
            logger.error("Ollama stream exception: %s", exc)
            yield f"[ERROR: {exc}]"

    # ── JSON generation ───────────────────────────────────────────────────────

    async def generate_json_async(
        self,
        *,
        prompt: str,
        model: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON response with automatic retry on parse error.

        The system prompt instructs the model to return **only** raw JSON.
        Markdown code fences are stripped before parsing.  If ``schema`` is
        supplied, the top-level ``"required"`` keys are checked and a corrective
        follow-up message is sent on failure.

        Parameters
        ----------
        prompt:
            User-facing instruction string.
        model:
            Defaults to :attr:`fast_model` (``gemma4:latest``).
        schema:
            Optional JSON Schema dict.  Only ``required`` key validation is
            performed — full ajv-style validation is outside scope here.
        temperature:
            Low temperature (default 0.1) for deterministic JSON output.
        retries:
            Number of *additional* attempts after the first try (total =
            ``retries + 1``).

        Returns
        -------
        dict
            ``ok`` (bool), ``data`` (parsed dict or None),
            ``raw_text`` (str), ``model_used`` (str).
            On failure: ``error`` (str) is also present.
        """
        target = model or self.fast_model
        system_msg = (
            "You are a JSON generation assistant. "
            "Your response MUST be valid JSON only — no markdown, no prose, "
            "no code fences. Return ONLY the raw JSON object."
        )
        if schema:
            system_msg += (
                f"\n\nAdhere strictly to this JSON Schema:\n"
                f"{json.dumps(schema, indent=2)}"
            )

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ]

        last_error = "No attempts made"
        raw_text = ""
        total_attempts = max(1, retries + 1)

        for attempt in range(total_attempts):
            response = await self.chat_async(
                messages=messages,
                model=target,
                temperature=temperature,
                max_tokens=1024,
            )

            # Connection / HTTP errors — do not retry; let caller handle.
            if response.raw.get("ok") is False:
                last_error = response.raw.get("error", "Unknown provider error")
                break

            raw_text = response.text.strip()

            # Strip markdown code fences that some models emit despite instructions
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text, flags=re.IGNORECASE).strip()

            try:
                parsed: Dict[str, Any] = json.loads(raw_text)

                # Optional top-level required-key validation
                if schema and isinstance(schema.get("required"), list):
                    missing = [k for k in schema["required"] if k not in parsed]
                    if missing:
                        last_error = (
                            f"Schema validation failed: missing required keys {missing}"
                        )
                        if attempt < total_attempts - 1:
                            # Corrective turn — feed the bad response back
                            messages.append({"role": "assistant", "content": raw_text})
                            messages.append(
                                {
                                    "role": "user",
                                    "content": (
                                        f"The JSON was missing required keys: {missing}. "
                                        "Please return a complete, valid JSON object."
                                    ),
                                }
                            )
                            continue
                        break

                return {
                    "ok": True,
                    "data": parsed,
                    "raw_text": raw_text,
                    "model_used": target,
                }

            except json.JSONDecodeError as exc:
                last_error = f"JSON parse error (attempt {attempt + 1}/{total_attempts}): {exc}"
                logger.warning(
                    "generate_json_async parse error (attempt %s/%s): %s",
                    attempt + 1,
                    total_attempts,
                    exc,
                )
                if attempt < total_attempts - 1:
                    # Corrective turn — ask the model to fix its output
                    messages.append({"role": "assistant", "content": raw_text})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "That response was not valid JSON. "
                                "Return ONLY raw JSON, no explanations."
                            ),
                        }
                    )

        return {
            "ok": False,
            "data": None,
            "raw_text": raw_text,
            "model_used": target,
            "error": last_error,
        }
