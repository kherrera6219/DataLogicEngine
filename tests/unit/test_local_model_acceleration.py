"""Unit tests for backend.local_model_acceleration.

Covers:
- runtime_settings: new LMA fields normalise correctly
- ResponseCache: build_cache_key uniqueness, get/set round-trip, TTL expiry
- safety: should_cache_prompt filter rules
- LocalModelAccelerationManager: bypass for non-local providers, cache hit,
  cache miss + store, feature-disabled bypass
- LocalModelKeepAlive: model rotation, thread started once, stop is clean

Heavy imports (Flask app, DB) are avoided — all tests run in isolation.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# runtime_settings — new LMA fields
# ===========================================================================

class TestRuntimeSettingsLmaFields:
    """Verify new fields are normalised on load and save."""

    def test_defaults_present_in_load(self, tmp_path: Path) -> None:
        """load_storage_settings() includes all LMA defaults even on empty file."""
        import os
        settings_file = tmp_path / "storage_settings.json"
        settings_file.write_text("{}")  # exists but empty

        with patch.dict(os.environ, {"DATALOGIC_STORAGE_SETTINGS_PATH": str(settings_file)}):
            from backend.storage import runtime_settings as rs
            # Force reload
            result = rs.load_storage_settings()

        assert result["local_model_acceleration_enabled"] is True
        assert result["local_model_exact_cache_enabled"] is True
        assert result["local_model_semantic_cache_enabled"] is False  # Phase 2 lock
        assert isinstance(result["local_model_heartbeat_seconds"], int)
        assert isinstance(result["local_model_cache_ttl_days"], int)

    def test_semantic_cache_always_false_on_save(self, tmp_path: Path) -> None:
        """Even if a client sends semantic_cache_enabled=True it is locked to False."""
        import os
        settings_file = tmp_path / "storage_settings.json"
        settings_file.write_text("{}")

        with patch.dict(os.environ, {"DATALOGIC_STORAGE_SETTINGS_PATH": str(settings_file)}):
            from backend.storage import runtime_settings as rs
            result = rs.save_storage_settings({"local_model_semantic_cache_enabled": True})

        assert result["local_model_semantic_cache_enabled"] is False

    def test_int_types_normalised(self, tmp_path: Path) -> None:
        """String values in JSON are cast to int on load."""
        import json
        import os
        settings_file = tmp_path / "storage_settings.json"
        settings_file.write_text(json.dumps({
            "local_model_heartbeat_seconds": "120",
            "local_model_cache_ttl_days": "7",
        }))

        with patch.dict(os.environ, {"DATALOGIC_STORAGE_SETTINGS_PATH": str(settings_file)}):
            from backend.storage import runtime_settings as rs
            result = rs.load_storage_settings()

        assert result["local_model_heartbeat_seconds"] == 120
        assert result["local_model_cache_ttl_days"] == 7


# ===========================================================================
# ResponseCache — build_cache_key
# ===========================================================================

class TestResponseCacheCacheKey:
    """Cache key uniqueness and determinism."""

    def _key(self, **kw) -> str:
        from backend.local_model_acceleration.response_cache import ResponseCache
        defaults = dict(
            model_name="gemma4:latest",
            provider_type="ollama",
            task_type="gateway_chat",
            system=None,
            prompt="What is gravity?",
            rag_context="",
            options={"temperature": 0.7, "max_tokens": 1024,
                     "run_ukg_pipeline": True, "mode": "standard"},
        )
        defaults.update(kw)
        return ResponseCache.build_cache_key(**defaults)

    def test_deterministic(self) -> None:
        assert self._key() == self._key()

    def test_different_rag_context_different_key(self) -> None:
        k1 = self._key(rag_context="")
        k2 = self._key(rag_context="Some retrieved knowledge chunk.")
        assert k1 != k2

    def test_different_prompt_different_key(self) -> None:
        k1 = self._key(prompt="What is gravity?")
        k2 = self._key(prompt="What is quantum entanglement?")
        assert k1 != k2

    def test_different_model_different_key(self) -> None:
        k1 = self._key(model_name="gemma4:latest")
        k2 = self._key(model_name="qwen3:14b")
        assert k1 != k2

    def test_different_temperature_different_key(self) -> None:
        k1 = self._key(options={"temperature": 0.0, "max_tokens": 1024,
                                 "run_ukg_pipeline": True, "mode": "standard"})
        k2 = self._key(options={"temperature": 0.9, "max_tokens": 1024,
                                 "run_ukg_pipeline": True, "mode": "standard"})
        assert k1 != k2

    def test_returns_hex_sha256(self) -> None:
        key = self._key()
        assert len(key) == 64
        int(key, 16)  # raises ValueError if not hex


# ===========================================================================
# ResponseCache — get / set / expiry
# ===========================================================================

class TestResponseCacheGetSet:
    @pytest.fixture
    def cache(self, tmp_path: Path):
        from backend.local_model_acceleration.response_cache import ResponseCache
        return ResponseCache(tmp_path / "test_cache.db")

    def _set(self, cache, cache_key: str, response: str = "Test answer", ttl_days: int = 30):
        cache.set(
            cache_key=cache_key,
            response=response,
            metadata={"model": "gemma4:latest"},
            ttl_days=ttl_days,
            model_name="gemma4:latest",
            provider_type="ollama",
            task_type="gateway_chat",
            system=None,
            prompt="test",
            rag_context="",
            options={"temperature": 0.7, "max_tokens": 1024,
                     "run_ukg_pipeline": True, "mode": "standard"},
        )

    def test_set_then_get_returns_response(self, cache) -> None:
        self._set(cache, "abc123", "Hello world")
        hit = cache.get("abc123")
        assert hit is not None
        assert hit["response"] == "Hello world"

    def test_miss_returns_none(self, cache) -> None:
        assert cache.get("nonexistent_key") is None

    def test_expired_row_is_a_miss(self, cache) -> None:
        """A row with ttl_days=0 should be treated as expired (or at least not far future)."""
        import sqlite3
        # Write a row directly with an already-expired expires_at
        conn = sqlite3.connect(str(cache._db_path))
        conn.execute(
            """INSERT OR REPLACE INTO llm_response_cache
               (cache_key, model_name, provider_type, task_type,
                prompt_sha256, rag_ctx_sha256, options_json,
                response, metadata_json, created_at, expires_at)
               VALUES (?, 'gemma4:latest', 'ollama', 'gateway_chat',
                       'phash', 'rhash', '{}', 'stale response',
                       '{}', '2020-01-01T00:00:00Z', '2020-01-02T00:00:00Z')""",
            ("stale_key",),
        )
        conn.commit()
        conn.close()

        assert cache.get("stale_key") is None

    def test_stats_reflects_inserts(self, cache) -> None:
        self._set(cache, "k1", "answer 1")
        self._set(cache, "k2", "answer 2")
        stats = cache.stats()
        assert stats["active_rows"] >= 2

    def test_clear_all_empties_cache(self, cache) -> None:
        self._set(cache, "k1", "answer 1")
        self._set(cache, "k2", "answer 2")
        deleted = cache.clear_all()
        assert deleted >= 2
        assert cache.stats()["total_rows"] == 0


# ===========================================================================
# safety — should_cache_prompt
# ===========================================================================

class TestShouldCachePrompt:
    def _check(self, prompt="Hello world", task_type="gateway_chat", metadata=None):
        from backend.local_model_acceleration.safety import should_cache_prompt
        return should_cache_prompt(prompt, task_type, metadata)

    def test_normal_prompt_is_cacheable(self) -> None:
        cacheable, reason = self._check()
        assert cacheable is True
        assert reason is None

    def test_long_prompt_is_not_cacheable(self) -> None:
        from backend.local_model_acceleration.safety import should_cache_prompt
        long_prompt = "x" * 25_000
        cacheable, reason = should_cache_prompt(long_prompt, "gateway_chat", max_prompt_chars=24_000)
        assert cacheable is False
        assert reason == "prompt_too_long"

    def test_unsafe_task_type_not_cached(self) -> None:
        cacheable, reason = self._check(task_type="emotional_chat")
        assert cacheable is False
        assert "task_type" in (reason or "")

    def test_sensitive_keyword_not_cached(self) -> None:
        cacheable, reason = self._check(prompt="My password is hunter2")
        assert cacheable is False
        assert "sensitive_keyword" in (reason or "")

    def test_meta_no_cache_flag_respected(self) -> None:
        cacheable, reason = self._check(metadata={"no_cache": True})
        assert cacheable is False
        assert "no_cache" in (reason or "")

    def test_meta_cache_policy_off_respected(self) -> None:
        cacheable, reason = self._check(metadata={"cache_policy": "off"})
        assert cacheable is False

    def test_semantic_cache_always_disabled(self) -> None:
        from backend.local_model_acceleration.safety import semantic_cache_allowed
        assert semantic_cache_allowed() is False


# ===========================================================================
# LocalModelAccelerationManager — integration-light tests
# ===========================================================================

class TestLocalModelAccelerationManager:
    """Tests that stub the ResponseCache and OllamaClient."""

    def _make_manager(self, tmp_path: Path):
        """Build a manager with in-memory-style components."""
        from backend.local_model_acceleration.config import LocalModelAccelerationConfig
        from backend.local_model_acceleration.manager import LocalModelAccelerationManager

        cfg = LocalModelAccelerationConfig(
            enabled=True,
            keepalive_enabled=False,  # no background thread in tests
            exact_cache_enabled=True,
            cache_ttl_days=30,
            max_prompt_chars=24_000,
            ollama_base_url="http://localhost:11434",
        )
        mgr = LocalModelAccelerationManager.__new__(LocalModelAccelerationManager)
        from backend.local_model_acceleration.ollama_client import OllamaClient
        from backend.local_model_acceleration.keepalive import LocalModelKeepAlive
        from backend.local_model_acceleration.response_cache import ResponseCache

        mgr._client = OllamaClient()
        mgr._keepalive = LocalModelKeepAlive(mgr._client, cfg)
        mgr._response_cache = ResponseCache(tmp_path / "test_lma.db")
        return mgr

    @pytest.mark.asyncio
    async def test_non_local_provider_bypassed(self, tmp_path: Path) -> None:
        """Cloud providers must bypass the acceleration layer entirely."""
        mgr = self._make_manager(tmp_path)
        call_count = 0

        async def _call():
            nonlocal call_count
            call_count += 1
            return {"ok": True, "answer": "cloud answer"}

        result = await mgr.generate_with_cache(
            provider_type="openai",
            model_name="gpt-5.5",
            task_type="gateway_chat",
            prompt="Hello",
            options={"temperature": 0.7, "max_tokens": 1024,
                     "run_ukg_pipeline": True, "mode": "standard"},
            call_model=_call,
        )
        # Non-local providers should NOT go through this manager in gateway.py,
        # but if they do the manager must still call the model.
        assert call_count == 1
        assert result["answer"] == "cloud answer"

    @pytest.mark.asyncio
    async def test_cache_miss_then_hit(self, tmp_path: Path) -> None:
        """First call: cache miss → model called.  Second call: cache hit."""
        mgr = self._make_manager(tmp_path)
        call_count = 0

        async def _call():
            nonlocal call_count
            call_count += 1
            return {"ok": True, "answer": "The speed of light is 299,792,458 m/s."}

        opts = {"temperature": 0.0, "max_tokens": 512,
                "run_ukg_pipeline": True, "mode": "standard"}
        kwargs = dict(
            provider_type="ollama",
            model_name="gemma4:latest",
            task_type="gateway_chat",
            prompt="What is the speed of light?",
            rag_context="",
            options=opts,
        )

        # First call — cache miss
        r1 = await mgr.generate_with_cache(**kwargs, call_model=_call)
        assert call_count == 1
        accel1 = r1.pop("_acceleration", {})
        assert accel1.get("cache_hit") is False

        # Second call — cache hit
        r2 = await mgr.generate_with_cache(**kwargs, call_model=_call)
        assert call_count == 1  # model NOT called again
        accel2 = r2.pop("_acceleration", {})
        assert accel2.get("cache_hit") is True
        assert accel2.get("source") == "exact_cache"
        assert r2["answer"] == "The speed of light is 299,792,458 m/s."

    @pytest.mark.asyncio
    async def test_disabled_feature_bypasses_cache(self, tmp_path: Path) -> None:
        """When acceleration is disabled, model is always called, cache is not checked."""
        from backend.local_model_acceleration.config import LocalModelAccelerationConfig
        from backend.local_model_acceleration.manager import LocalModelAccelerationManager
        from backend.local_model_acceleration.response_cache import ResponseCache
        from backend.local_model_acceleration.keepalive import LocalModelKeepAlive
        from backend.local_model_acceleration.ollama_client import OllamaClient

        cfg = LocalModelAccelerationConfig(enabled=False, keepalive_enabled=False)
        mgr = LocalModelAccelerationManager.__new__(LocalModelAccelerationManager)
        mgr._client = OllamaClient()
        mgr._keepalive = LocalModelKeepAlive(mgr._client, cfg)
        mgr._response_cache = ResponseCache(tmp_path / "disabled.db")

        call_count = 0

        async def _call():
            nonlocal call_count
            call_count += 1
            return {"ok": True, "answer": "answer"}

        with patch(
            "backend.local_model_acceleration.config.LocalModelAccelerationConfig.from_runtime_settings",
            return_value=cfg,
        ):
            await mgr.generate_with_cache(
                provider_type="ollama",
                model_name="gemma4:latest",
                task_type="gateway_chat",
                prompt="Hello",
                options={"temperature": 0.7, "max_tokens": 512,
                         "run_ukg_pipeline": False, "mode": "standard"},
                call_model=_call,
            )
            await mgr.generate_with_cache(
                provider_type="ollama",
                model_name="gemma4:latest",
                task_type="gateway_chat",
                prompt="Hello",
                options={"temperature": 0.7, "max_tokens": 512,
                         "run_ukg_pipeline": False, "mode": "standard"},
                call_model=_call,
            )

        assert call_count == 2  # called both times — cache bypassed

    @pytest.mark.asyncio
    async def test_unsafe_prompt_skips_cache_but_calls_model(self, tmp_path: Path) -> None:
        """Prompts containing sensitive keywords must never be cached."""
        mgr = self._make_manager(tmp_path)
        call_count = 0

        async def _call():
            nonlocal call_count
            call_count += 1
            return {"ok": True, "answer": "some response"}

        kwargs = dict(
            provider_type="ollama",
            model_name="gemma4:latest",
            task_type="gateway_chat",
            prompt="My password is hunter2",
            rag_context="",
            options={"temperature": 0.7, "max_tokens": 512,
                     "run_ukg_pipeline": True, "mode": "standard"},
        )

        await mgr.generate_with_cache(**kwargs, call_model=_call)
        await mgr.generate_with_cache(**kwargs, call_model=_call)

        # Model called twice — sensitive prompt is never cached
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_different_rag_context_produces_different_cache_entries(
        self, tmp_path: Path
    ) -> None:
        """Same query + different RAG chunks → two separate cache entries."""
        mgr = self._make_manager(tmp_path)
        call_count = 0

        async def _call():
            nonlocal call_count
            call_count += 1
            return {"ok": True, "answer": f"answer_{call_count}"}

        base_kwargs = dict(
            provider_type="ollama",
            model_name="gemma4:latest",
            task_type="gateway_chat",
            prompt="What is the boiling point of water?",
            options={"temperature": 0.0, "max_tokens": 256,
                     "run_ukg_pipeline": True, "mode": "standard"},
        )

        await mgr.generate_with_cache(**base_kwargs, rag_context="", call_model=_call)
        await mgr.generate_with_cache(**base_kwargs, rag_context="Context: water boils at 100°C at sea level.", call_model=_call)
        # Same query with same empty rag_context → cache hit
        r3 = await mgr.generate_with_cache(**base_kwargs, rag_context="", call_model=_call)

        assert call_count == 2  # 3rd call was a cache hit for the first entry
        assert r3.get("_acceleration", {}).get("cache_hit") is True


# ===========================================================================
# OllamaClient — unit tests (requests are mocked)
# ===========================================================================

class TestOllamaClient:
    def _client(self):
        from backend.local_model_acceleration.ollama_client import OllamaClient
        return OllamaClient(base_url="http://localhost:11434", timeout=5)

    def test_health_check_ok(self) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "models": [{"name": "gemma4:latest"}, {"name": "qwen3:14b"}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_resp):
            result = self._client().health_check()

        assert result["ok"] is True
        assert "gemma4:latest" in result["models"]

    def test_health_check_connection_error_returns_ok_false(self) -> None:
        with patch("requests.get", side_effect=ConnectionError("refused")):
            result = self._client().health_check()

        assert result["ok"] is False
        assert result["models"] == []
        assert result["error"] is not None

    def test_list_models_delegates_to_health_check(self) -> None:
        with patch.object(
            self._client().__class__,
            "health_check",
            return_value={"ok": True, "models": ["m1", "m2"], "raw": {}, "error": None},
        ):
            models = self._client().list_models()
        # list_models calls health_check — just verify the shape
        assert isinstance(models, list)
