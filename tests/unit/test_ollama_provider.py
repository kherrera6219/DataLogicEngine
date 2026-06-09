"""
Tests for OllamaProvider.

Structure
---------
TestOllamaProviderUnit
    Fully mocked — no live Ollama required.  Covers:
    • health_check() — OK, HTTP error, connection refused
    • list_models()
    • chat_async()   — OK, HTTP error, connection refused
    • chat_stream_async() — OK, HTTP error
    • generate_json_async() — OK, parse error → retry → success,
                               parse error → exhausted retries,
                               schema validation fail → retry,
                               provider error passthrough

TestOllamaProviderIntegration
    Live Ollama required (http://localhost:11434).
    Skipped automatically when Ollama is not reachable.
    Validates both installed models: gemma4:12b and gemma4:latest.
"""
from __future__ import annotations

import socket
import sys
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the SDK is importable from the project root
# ---------------------------------------------------------------------------
import pathlib

_SDK_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "sdk"
    / "UKG_Python_SDK"
)
if str(_SDK_PATH) not in sys.path:
    sys.path.insert(0, str(_SDK_PATH))

from ukg_sdk.providers.ollama import (  # noqa: E402
    OLLAMA_DEFAULT_MODEL,
    OLLAMA_FAST_MODEL,
    OllamaModelInfo,
    OllamaProvider,
)
from ukg_sdk.providers.base import LLMResponse  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _oai_chat_response(content: str, model: str = OLLAMA_DEFAULT_MODEL) -> dict:
    """Minimal OpenAI-compatible /v1/chat/completions response payload."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def _tags_response(names: list[str]) -> dict:
    """Minimal /api/tags response payload."""
    return {
        "models": [
            {
                "name": n,
                "model": n,
                "size": 7_000_000_000,
                "modified_at": "2026-06-08T00:00:00Z",
                "details": {},
            }
            for n in names
        ]
    }


# ── aiohttp mock factory ────────────────────────────────────────────────────

def _make_mock_response(
    *,
    status: int = 200,
    json_data: dict | None = None,
    text_data: str = "",
    content_lines: list[bytes] | None = None,
) -> MagicMock:
    """
    Build an async context-manager mock that mimics an aiohttp response.

    ``content_lines`` is a list of raw bytes lines for SSE streaming tests.
    """
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data or {})
    mock_resp.text = AsyncMock(return_value=text_data)

    # SSE content iterator
    async def _content_iter() -> AsyncIterator[bytes]:
        for line in (content_lines or []):
            yield line

    mock_resp.content = _content_iter()

    # Async context manager protocol
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    return mock_resp


def _make_mock_session(mock_resp: MagicMock) -> MagicMock:
    """Build an async context-manager mock for aiohttp.ClientSession."""
    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    return mock_session


# ── Integration skip marker ─────────────────────────────────────────────────

def _ollama_reachable() -> bool:
    """Return True when Ollama TCP port 11434 is open."""
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=1):
            return True
    except OSError:
        return False


_skip_if_no_ollama = pytest.mark.skipif(
    not _ollama_reachable(),
    reason="Ollama not running on localhost:11434 — integration tests skipped",
)


# ===========================================================================
# Unit tests (fully mocked)
# ===========================================================================

class TestOllamaProviderUnit:
    """Mocked unit tests — zero network I/O."""

    provider = OllamaProvider()

    # ── Constructor ──────────────────────────────────────────────────────────

    def test_base_url_strips_v1_suffix(self):
        p = OllamaProvider(base_url="http://localhost:11434/v1")
        assert p._base_url == "http://localhost:11434"
        assert p._oai_url == "http://localhost:11434/v1"

    def test_base_url_without_v1_unchanged(self):
        p = OllamaProvider(base_url="http://localhost:11434")
        assert p._base_url == "http://localhost:11434"
        assert p._oai_url == "http://localhost:11434/v1"

    def test_default_models(self):
        p = OllamaProvider()
        assert p.default_model == OLLAMA_DEFAULT_MODEL
        assert p.fast_model == OLLAMA_FAST_MODEL

    def test_custom_models(self):
        p = OllamaProvider(default_model="llama3:8b", fast_model="tinyllama")
        assert p.default_model == "llama3:8b"
        assert p.fast_model == "tinyllama"

    # ── health_check ─────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_health_check_ok(self):
        names = [OLLAMA_DEFAULT_MODEL, OLLAMA_FAST_MODEL]
        mock_resp = _make_mock_response(json_data=_tags_response(names))
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.health_check()

        assert result["ok"] is True
        assert set(result["models"]) == set(names)
        assert len(result["model_infos"]) == 2
        for info in result["model_infos"]:
            assert isinstance(info, OllamaModelInfo)
            assert info.size_gb == pytest.approx(7.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_health_check_http_error(self):
        mock_resp = _make_mock_response(status=500, text_data="internal error")
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.health_check()

        assert result["ok"] is False
        assert "HTTP 500" in result["error"]
        assert result["models"] == []

    @pytest.mark.asyncio
    async def test_health_check_connection_refused(self):
        import aiohttp as _aiohttp

        with patch(
            "aiohttp.ClientSession",
            side_effect=_aiohttp.ClientConnectorError(
                connection_key=MagicMock(), os_error=OSError("refused")
            ),
        ):
            result = await self.provider.health_check()

        assert result["ok"] is False
        assert "Cannot connect" in result["error"]

    # ── list_models ──────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_models_returns_sorted_names(self):
        names = ["qwen3:14b", OLLAMA_DEFAULT_MODEL, OLLAMA_FAST_MODEL]
        mock_resp = _make_mock_response(json_data=_tags_response(names))
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            models = await self.provider.list_models()

        assert models == sorted(names)

    @pytest.mark.asyncio
    async def test_list_models_returns_empty_on_error(self):
        mock_resp = _make_mock_response(status=503, text_data="unavailable")
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            models = await self.provider.list_models()

        assert models == []

    # ── chat_async ───────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_chat_async_ok(self):
        payload = _oai_chat_response("Hello!")
        mock_resp = _make_mock_response(json_data=payload)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.chat_async(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert isinstance(result, LLMResponse)
        assert result.text == "Hello!"
        assert result.model == OLLAMA_DEFAULT_MODEL
        assert result.usage is not None

    @pytest.mark.asyncio
    async def test_chat_async_uses_specified_model(self):
        payload = _oai_chat_response("response", model=OLLAMA_FAST_MODEL)
        mock_resp = _make_mock_response(json_data=payload)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.chat_async(
                messages=[{"role": "user", "content": "Hi"}],
                model=OLLAMA_FAST_MODEL,
            )

        assert result.model == OLLAMA_FAST_MODEL

    @pytest.mark.asyncio
    async def test_chat_async_http_error_returns_not_ok(self):
        mock_resp = _make_mock_response(status=404, text_data="model not found")
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.chat_async(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert result.raw.get("ok") is False
        assert result.raw.get("retryable") is False  # 404 is not retryable

    @pytest.mark.asyncio
    async def test_chat_async_server_error_is_retryable(self):
        mock_resp = _make_mock_response(status=503, text_data="overloaded")
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.chat_async(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert result.raw.get("ok") is False
        assert result.raw.get("retryable") is True  # 503 is retryable

    @pytest.mark.asyncio
    async def test_chat_async_connection_error_is_retryable(self):
        import aiohttp as _aiohttp

        with patch(
            "aiohttp.ClientSession",
            side_effect=_aiohttp.ClientConnectorError(
                connection_key=MagicMock(), os_error=OSError("refused")
            ),
        ):
            result = await self.provider.chat_async(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert result.raw.get("ok") is False
        assert result.raw.get("retryable") is True

    # ── complete (ABC bridge) ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_complete_delegates_to_chat_async(self):
        payload = _oai_chat_response("Bridge works")
        mock_resp = _make_mock_response(json_data=payload)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.complete(
                messages=[{"role": "user", "content": "test"}],
                model=OLLAMA_DEFAULT_MODEL,
            )

        assert result.text == "Bridge works"

    # ── chat_stream_async ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_chat_stream_yields_text_chunks(self):
        sse_lines = [
            b'data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}\n',
            b'data: {"choices":[{"delta":{"content":" world"},"index":0}]}\n',
            b"data: [DONE]\n",
        ]
        mock_resp = _make_mock_response(content_lines=sse_lines)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            chunks = []
            async for chunk in self.provider.chat_stream_async(
                messages=[{"role": "user", "content": "Hi"}]
            ):
                chunks.append(chunk)

        assert chunks == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_chat_stream_yields_error_on_http_failure(self):
        mock_resp = _make_mock_response(status=500, text_data="internal error")
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            chunks = []
            async for chunk in self.provider.chat_stream_async(
                messages=[{"role": "user", "content": "Hi"}]
            ):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].startswith("[ERROR:")

    @pytest.mark.asyncio
    async def test_chat_stream_skips_malformed_sse_lines(self):
        sse_lines = [
            b"data: not-json\n",
            b'data: {"choices":[{"delta":{"content":"OK"},"index":0}]}\n',
            b"data: [DONE]\n",
        ]
        mock_resp = _make_mock_response(content_lines=sse_lines)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            chunks = []
            async for chunk in self.provider.chat_stream_async(
                messages=[{"role": "user", "content": "Hi"}]
            ):
                chunks.append(chunk)

        assert chunks == ["OK"]

    # ── generate_json_async ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_generate_json_ok_first_try(self):
        json_payload = _oai_chat_response('{"status": "ok"}')
        mock_resp = _make_mock_response(json_data=json_payload)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.generate_json_async(prompt="Return status")

        assert result["ok"] is True
        assert result["data"] == {"status": "ok"}
        assert result["model_used"] == OLLAMA_FAST_MODEL

    @pytest.mark.asyncio
    async def test_generate_json_strips_code_fences(self):
        json_payload = _oai_chat_response("```json\n{\"status\": \"ok\"}\n```")
        mock_resp = _make_mock_response(json_data=json_payload)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.generate_json_async(prompt="Return status")

        assert result["ok"] is True
        assert result["data"] == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_generate_json_retries_on_parse_error(self):
        """First response is bad JSON; second response is valid — should succeed."""
        bad_payload = _oai_chat_response("not valid json at all")
        good_payload = _oai_chat_response('{"fixed": true}')

        call_count = 0

        class _MultiResponseSession:
            # Must be a regular def — the caller uses `async with session.post(...)`
            # which requires post() to return an async context manager object, not
            # a coroutine.  AsyncMock would wrap the return value in a coroutine
            # layer, causing the same protocol error.
            def post(self, *_args, **_kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return _make_mock_response(json_data=bad_payload)
                return _make_mock_response(json_data=good_payload)

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                pass

        with patch("aiohttp.ClientSession", return_value=_MultiResponseSession()):
            result = await self.provider.generate_json_async(
                prompt="Return something", retries=1
            )

        assert result["ok"] is True
        assert result["data"] == {"fixed": True}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_generate_json_returns_not_ok_when_retries_exhausted(self):
        bad_payload = _oai_chat_response("still not json")
        mock_resp = _make_mock_response(json_data=bad_payload)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.generate_json_async(
                prompt="Return JSON", retries=0
            )

        assert result["ok"] is False
        assert "JSON parse error" in result["error"]
        assert result["data"] is None

    @pytest.mark.asyncio
    async def test_generate_json_schema_required_keys(self):
        schema = {
            "type": "object",
            "required": ["name", "score"],
            "properties": {
                "name": {"type": "string"},
                "score": {"type": "number"},
            },
        }
        good_payload = _oai_chat_response('{"name": "Alice", "score": 42}')
        mock_resp = _make_mock_response(json_data=good_payload)
        with patch("aiohttp.ClientSession", return_value=_make_mock_session(mock_resp)):
            result = await self.provider.generate_json_async(
                prompt="Give me a person object", schema=schema
            )

        assert result["ok"] is True
        assert result["data"]["name"] == "Alice"
        assert result["data"]["score"] == 42

    @pytest.mark.asyncio
    async def test_generate_json_passthrough_on_provider_error(self):
        """Connection errors abort immediately without consuming retry budget."""
        import aiohttp as _aiohttp

        with patch(
            "aiohttp.ClientSession",
            side_effect=_aiohttp.ClientConnectorError(
                connection_key=MagicMock(), os_error=OSError("refused")
            ),
        ):
            result = await self.provider.generate_json_async(
                prompt="Return JSON", retries=2
            )

        assert result["ok"] is False
        assert "Cannot connect" in result["error"]


# ===========================================================================
# Integration tests (live Ollama required)
# ===========================================================================

# All four local tier model names (must match exactly what `ollama list` reports).
_TIER_MODELS = [
    ("T0", "gemma4:latest"),          # ultra-light, ~1-2 s
    ("T1", "gemma4:12b"),             # primary, thinking model ~30 s
    ("T2", "qwen3:14b"),              # medium/coding, thinking model ~40 s
    ("T3", "devstral-small-2:latest"),# heavy agentic coding ~30 s
]


@_skip_if_no_ollama
class TestOllamaProviderIntegration:
    """
    Live integration suite — only runs when Ollama is up on localhost:11434.

    All four installed local tiers are exercised:
      T0 gemma4:latest  · T1 gemma4:12b  · T2 qwen3:14b  · T3 devstral-small-2:latest
    """

    provider = OllamaProvider()

    # ── health & model discovery ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_health_check_is_ok(self):
        result = await self.provider.health_check()
        assert result["ok"] is True, f"health_check failed: {result.get('error')}"
        assert len(result["models"]) >= 4, (
            f"Expected all 4 tier models installed, found: {result['models']}"
        )

    @pytest.mark.asyncio
    async def test_list_models_contains_all_four_tiers(self):
        models = await self.provider.list_models()
        assert isinstance(models, list)
        expected = {m for _, m in _TIER_MODELS}
        missing = expected - set(models)
        assert not missing, (
            f"Missing tier models: {missing}\nInstalled: {models}"
        )

    # ── chat_async with default model (gemma4:12b) ───────────────────────────

    @pytest.mark.asyncio
    async def test_chat_async_default_model(self):
        # gemma4:12b is a thinking model — it emits a "reasoning" chain-of-thought
        # before the visible content.  max_tokens must be generous enough to cover
        # both; 16 tokens is exhausted during reasoning, leaving content empty.
        result = await self.provider.chat_async(
            messages=[{"role": "user", "content": "Reply with exactly: PONG"}],
            max_tokens=512,
        )
        assert result.raw.get("ok") is not False, (
            f"chat_async failed: {result.raw.get('error')}"
        )
        assert isinstance(result.text, str)
        assert len(result.text) > 0

    # ── chat_async with fast model (gemma4:latest) ───────────────────────────

    @pytest.mark.asyncio
    async def test_chat_async_fast_model(self):
        result = await self.provider.chat_async(
            messages=[{"role": "user", "content": "Reply with exactly: PONG"}],
            model=OLLAMA_FAST_MODEL,
            max_tokens=256,
        )
        assert result.raw.get("ok") is not False, (
            f"chat_async fast model failed: {result.raw.get('error')}"
        )
        assert isinstance(result.text, str)
        assert len(result.text) > 0

    # ── complete() ABC bridge ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_complete_abc_bridge(self):
        result = await self.provider.complete(
            messages=[{"role": "user", "content": "Say hi"}],
            model=OLLAMA_DEFAULT_MODEL,
            max_tokens=512,
        )
        assert result.raw.get("ok") is not False
        assert len(result.text) > 0

    # ── chat_stream_async ─────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_chat_stream_default_model(self):
        chunks: list[str] = []
        async for chunk in self.provider.chat_stream_async(
            messages=[{"role": "user", "content": "Count to 3"}],
            max_tokens=512,
        ):
            chunks.append(chunk)
            if chunk.startswith("[ERROR:"):
                pytest.fail(f"Stream returned error: {chunk}")

        full_text = "".join(chunks)
        assert len(full_text) > 0, "Streaming returned no content"

    # ── generate_json_async — all four tier models ───────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier_label,model", _TIER_MODELS)
    async def test_generate_json_all_tiers(self, tier_label: str, model: str):
        """Every local tier model must return valid JSON for a simple prompt."""
        result = await self.provider.generate_json_async(
            prompt='Return a JSON object with key "status" set to "ok".',
            model=model,
            retries=2,
        )
        assert result["ok"] is True, (
            f"generate_json failed for {tier_label} ({model}): "
            f"{result.get('error')} | raw: {result.get('raw_text')}"
        )
        assert isinstance(result["data"], dict)
        assert "status" in result["data"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier_label,model", _TIER_MODELS)
    async def test_generate_json_schema_all_tiers(self, tier_label: str, model: str):
        """Every tier model respects a required-keys schema."""
        schema = {
            "type": "object",
            "required": ["answer", "confidence"],
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number"},
            },
        }
        result = await self.provider.generate_json_async(
            prompt=(
                'Return a JSON object with "answer" (a short string) '
                'and "confidence" (a float between 0 and 1).'
            ),
            model=model,
            schema=schema,
            retries=2,
        )
        assert result["ok"] is True, (
            f"Schema JSON failed for {tier_label} ({model}): "
            f"{result.get('error')} | raw: {result.get('raw_text')}"
        )
        assert "answer" in result["data"]
        assert "confidence" in result["data"]
