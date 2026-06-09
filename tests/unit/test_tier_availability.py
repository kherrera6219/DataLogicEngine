"""Unit tests for backend.llm_gateway.tier_availability.

Tests cover:
- find_best_available_tier cascade logic (all cases)
- probe_local_tiers: available models, missing models, Ollama offline
- is_local_tier_available helper
"""
from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import contextmanager

import pytest

# ---------------------------------------------------------------------------
# Helpers to reset the module-level cache between tests
# ---------------------------------------------------------------------------

def _reset_cache() -> None:
    """Force the tier_availability module to re-import with a clean cache."""
    mod = sys.modules.get("backend.llm_gateway.tier_availability")
    if mod is not None:
        mod._available_local_tiers = None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# find_best_available_tier — cascade logic
# ---------------------------------------------------------------------------

class TestFindBestAvailableTier:
    """Cascade rules when probe cache is populated."""

    def setup_method(self) -> None:
        _reset_cache()

    def _set_available(self, tiers: set[int]) -> None:
        import backend.llm_gateway.tier_availability as ta
        ta._available_local_tiers = frozenset(tiers)

    def test_returns_requested_tier_when_available(self) -> None:
        from backend.llm_gateway.tier_availability import find_best_available_tier
        self._set_available({0, 1, 2, 3})
        assert find_best_available_tier(2) == 2

    def test_cascades_down_when_tier_missing(self) -> None:
        """T2 not pulled → should fall back to T1."""
        from backend.llm_gateway.tier_availability import find_best_available_tier
        self._set_available({0, 1, 3})  # T2 missing
        assert find_best_available_tier(2) == 1

    def test_cascades_to_t0_when_only_t0_available(self) -> None:
        from backend.llm_gateway.tier_availability import find_best_available_tier
        self._set_available({0})
        # Classifier picked T3, only T0 is present
        assert find_best_available_tier(3) == 0

    def test_returns_original_when_no_probe_run(self) -> None:
        """Pre-probe (cache=None) → optimistic pass-through."""
        from backend.llm_gateway.tier_availability import find_best_available_tier
        _reset_cache()  # ensure None
        assert find_best_available_tier(2) == 2

    def test_cloud_tier_passthrough(self) -> None:
        """Cloud tiers (T4/T5) bypass the local cascade logic entirely."""
        from backend.llm_gateway.tier_availability import find_best_available_tier
        self._set_available(set())  # no local models at all
        # T4 is cloud — should come back unchanged
        assert find_best_available_tier(4, allow_cloud=True) == 4

    def test_escalates_to_cloud_when_no_local_and_allow_cloud(self) -> None:
        """No local models + allow_cloud=True → return lowest cloud tier (4)."""
        from backend.llm_gateway.tier_availability import find_best_available_tier
        self._set_available(set())
        result = find_best_available_tier(2, allow_cloud=True)
        assert result == 4

    def test_returns_original_when_no_local_and_cloud_not_allowed(self) -> None:
        """No local models + cloud not allowed → return original (gateway will fail)."""
        from backend.llm_gateway.tier_availability import find_best_available_tier
        self._set_available(set())
        result = find_best_available_tier(2, allow_cloud=False)
        assert result == 2  # nothing better; gateway surfaces the error

    def test_requested_tier_0_not_available_returns_self(self) -> None:
        """T0 missing with no lower tiers to cascade to → return 0."""
        from backend.llm_gateway.tier_availability import find_best_available_tier
        self._set_available({1, 2, 3})  # T0 not pulled
        result = find_best_available_tier(0, allow_cloud=False)
        # No lower tier exists; returns 0 and gateway will fail gracefully
        assert result == 0


# ---------------------------------------------------------------------------
# is_local_tier_available
# ---------------------------------------------------------------------------

class TestIsLocalTierAvailable:
    def setup_method(self) -> None:
        _reset_cache()

    def _set_available(self, tiers: set[int]) -> None:
        import backend.llm_gateway.tier_availability as ta
        ta._available_local_tiers = frozenset(tiers)

    def test_true_when_tier_in_cache(self) -> None:
        from backend.llm_gateway.tier_availability import is_local_tier_available
        self._set_available({0, 1})
        assert is_local_tier_available(0) is True

    def test_false_when_tier_not_in_cache(self) -> None:
        from backend.llm_gateway.tier_availability import is_local_tier_available
        self._set_available({0})
        assert is_local_tier_available(2) is False

    def test_true_when_not_yet_probed(self) -> None:
        """Optimistic when cache is None."""
        from backend.llm_gateway.tier_availability import is_local_tier_available
        assert is_local_tier_available(3) is True


# ---------------------------------------------------------------------------
# probe_local_tiers — async probe behaviour
# ---------------------------------------------------------------------------

class TestProbeLocalTiers:
    def setup_method(self) -> None:
        _reset_cache()

    @pytest.mark.asyncio
    async def test_all_models_present(self) -> None:
        """All four local models pulled → all four tiers available."""
        from backend.llm_gateway.tier_availability import probe_local_tiers

        all_models = [
            "gemma4:latest",
            "gemma4:12b",
            "qwen3:14b",
            "devstral-small-2:latest",
        ]
        with _ollama_patch(all_models):
            result = await probe_local_tiers()

        assert result == frozenset({0, 1, 2, 3})

    @pytest.mark.asyncio
    async def test_no_models_pulled(self) -> None:
        """Ollama running but no models pulled → empty availability set."""
        from backend.llm_gateway.tier_availability import probe_local_tiers, get_available_local_tiers

        with patch(
            "ukg_sdk.providers.ollama.OllamaProvider",
            create=True,
        ):
            # Simulate OllamaProvider returning empty list
            async def _empty_list_models():
                return []

            with _ollama_patch([]):
                result = await probe_local_tiers()

        assert result == frozenset()
        assert get_available_local_tiers() == frozenset()

    @pytest.mark.asyncio
    async def test_ollama_offline(self) -> None:
        """Ollama not reachable → empty availability set, no exception raised."""
        from backend.llm_gateway.tier_availability import probe_local_tiers

        with _ollama_patch(exc=ConnectionRefusedError("Ollama not running")):
            result = await probe_local_tiers()

        assert result == frozenset()

    @pytest.mark.asyncio
    async def test_partial_models(self) -> None:
        """Only T0 and T1 pulled → only those tiers available."""
        from backend.llm_gateway.tier_availability import probe_local_tiers

        with _ollama_patch(["gemma4:latest", "gemma4:12b"]):
            result = await probe_local_tiers()

        assert result == frozenset({0, 1})

    @pytest.mark.asyncio
    async def test_base_name_match(self) -> None:
        """Ollama may omit the tag; probe should still match by base name."""
        from backend.llm_gateway.tier_availability import probe_local_tiers

        # "gemma4" without ":latest" tag still matches OLLAMA_TIER0_MODEL
        with _ollama_patch(["gemma4", "gemma4:12b", "qwen3:14b", "devstral-small-2"]):
            result = await probe_local_tiers()

        assert 0 in result  # gemma4:latest matched by base name
        assert 3 in result  # devstral-small-2:latest matched by base name

    @pytest.mark.asyncio
    async def test_cache_is_set_after_probe(self) -> None:
        """After probe, get_available_local_tiers() returns non-None."""
        from backend.llm_gateway.tier_availability import probe_local_tiers, get_available_local_tiers

        with _ollama_patch(["gemma4:latest"]):
            await probe_local_tiers()

        assert get_available_local_tiers() is not None


# ---------------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------------

@contextmanager
def _ollama_patch(pulled: list[str] | None = None, *, exc: Exception | None = None):
    """Patch OllamaProvider.list_models inside tier_availability module."""
    mock_instance = AsyncMock()
    if exc is not None:
        mock_instance.list_models = AsyncMock(side_effect=exc)
    else:
        mock_instance.list_models = AsyncMock(return_value=pulled or [])

    mock_cls = MagicMock(return_value=mock_instance)

    # Patch the import inside probe_local_tiers by pre-populating sys.modules
    fake_module = MagicMock()
    fake_module.OllamaProvider = mock_cls

    orig = sys.modules.get("ukg_sdk.providers.ollama")
    sys.modules["ukg_sdk.providers.ollama"] = fake_module
    try:
        yield
    finally:
        if orig is None:
            sys.modules.pop("ukg_sdk.providers.ollama", None)
        else:
            sys.modules["ukg_sdk.providers.ollama"] = orig
