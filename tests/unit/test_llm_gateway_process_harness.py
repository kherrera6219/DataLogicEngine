"""LLMGateway.process() harness (audit A4-8).

Drives the full process() flow with internal seams stubbed at the
instance/module level, covering the local-model-acceleration block
(cache hit, fail-open) and the defense-supervisor block path (N2) that
unit tests on the manager alone cannot reach.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from backend.llm_gateway.gateway import GatewayRequest, LLMGateway


def _make_request(**overrides):
    defaults = dict(
        messages=[{"role": "user", "content": "Summarize the quarterly compliance report"}],
        provider="ollama",
        model="gemma4:12b",
        meta={"use_rag": False},
        run_ukg_pipeline=True,
    )
    defaults.update(overrides)
    return GatewayRequest(**defaults)


def _fake_provider_record():
    return SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        name="local-ollama",
        provider_type="ollama",
        priority=10,
        model="gemma4:12b",
    )


@pytest.fixture
def gateway(monkeypatch):
    gw = LLMGateway(db_session=None)
    record = _fake_provider_record()

    async def _eligible(*args, **kwargs):
        return [record]

    async def _noop(*args, **kwargs):
        return None

    pipeline_calls = {"count": 0}

    async def _overlay(*args, **kwargs):
        pipeline_calls["count"] += 1
        return {"ok": True, "answer": "model answer", "usage": {"prompt_tokens": 5, "completion_tokens": 7}}

    monkeypatch.setattr(gw, "_get_eligible_providers", _eligible)
    monkeypatch.setattr(gw, "_create_sdk_provider", lambda *_: MagicMock())
    monkeypatch.setattr(gw, "_run_ukg_overlay", _overlay)
    monkeypatch.setattr(gw, "_record_usage", _noop)
    # No defense supervisor by default — fail-open allow without model calls.
    monkeypatch.setenv("DEFENSE_SUPERVISOR_ENABLED", "false")
    gw._test_pipeline_calls = pipeline_calls
    return gw


class _StubAccelManager:
    """Acceleration manager stub honoring the generate_with_cache contract."""

    def __init__(self, mode: str):
        self.mode = mode  # "hit" | "miss" | "raise_before_call"
        self.keepalive_models: list[str] = []

    def start_keepalive(self, model, provider_type="ollama"):
        self.keepalive_models.append(model)

    async def generate_with_cache(self, *, call_model, **kwargs):
        if self.mode == "raise_before_call":
            raise RuntimeError("simulated acceleration failure before model call")
        if self.mode == "hit":
            return {
                "ok": True,
                "answer": "cached answer",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "explainability": {},
                "warnings": [],
                "error": None,
                "_acceleration": {"acceleration_enabled": True, "cache_hit": True, "source": "exact_cache"},
            }
        result = await call_model()
        result.setdefault("_acceleration", {"acceleration_enabled": True, "cache_hit": False, "source": "model"})
        return result


def _patch_accel(monkeypatch, manager):
    import backend.local_model_acceleration as lma

    monkeypatch.setattr(lma, "get_local_model_acceleration_manager", lambda: manager)


@pytest.mark.asyncio
async def test_process_cache_miss_returns_model_answer(gateway, monkeypatch):
    _patch_accel(monkeypatch, _StubAccelManager("miss"))

    response = await gateway.process(_make_request())

    assert response.content == "model answer"
    assert gateway._test_pipeline_calls["count"] == 1


@pytest.mark.asyncio
async def test_process_cache_hit_never_runs_pipeline(gateway, monkeypatch):
    """A4-1: cache hits must not start (or double-await) the pipeline coroutine."""
    _patch_accel(monkeypatch, _StubAccelManager("hit"))

    response = await gateway.process(_make_request())

    assert response.content == "cached answer"
    assert gateway._test_pipeline_calls["count"] == 0


@pytest.mark.asyncio
async def test_process_acceleration_failure_fails_open(gateway, monkeypatch):
    """A4-1: failures before the model call fall through to the bare await."""
    _patch_accel(monkeypatch, _StubAccelManager("raise_before_call"))

    response = await gateway.process(_make_request())

    assert response.content == "model answer"
    assert gateway._test_pipeline_calls["count"] == 1


@pytest.mark.asyncio
async def test_process_keepalive_registered_for_local_provider(gateway, monkeypatch):
    manager = _StubAccelManager("miss")
    _patch_accel(monkeypatch, manager)

    await gateway.process(_make_request())

    assert manager.keepalive_models == ["gemma4:12b"]


@pytest.mark.asyncio
async def test_process_defense_supervisor_block(gateway, monkeypatch):
    """N2: a BLOCK verdict stops the request before any provider call."""
    monkeypatch.setenv("DEFENSE_SUPERVISOR_ENABLED", "true")
    _patch_accel(monkeypatch, _StubAccelManager("miss"))

    supervisor = MagicMock()
    supervisor.enabled.return_value = True
    supervisor.screen.return_value = {
        "is_safe": False,
        "threat_score": 0.95,
        "threat_type": "Prompt Injection",
        "reason": "override attempt",
        "recommended_action": "BLOCK",
        "available": True,
    }
    import backend.security.defense_supervisor as ds

    monkeypatch.setattr(ds, "get_defense_supervisor", lambda: supervisor)

    request = _make_request()
    response = await gateway.process(request)

    assert response.error is not None
    assert "security policy" in response.error
    assert gateway._test_pipeline_calls["count"] == 0
    assert request.meta["defense_supervisor"]["recommended_action"] == "BLOCK"


@pytest.mark.asyncio
async def test_process_defense_supervisor_allow_records_verdict(gateway, monkeypatch):
    monkeypatch.setenv("DEFENSE_SUPERVISOR_ENABLED", "true")
    _patch_accel(monkeypatch, _StubAccelManager("miss"))

    supervisor = MagicMock()
    supervisor.enabled.return_value = True
    supervisor.screen.return_value = {
        "is_safe": True,
        "threat_score": 0.05,
        "threat_type": "None",
        "reason": "benign",
        "recommended_action": "ALLOW",
        "available": True,
    }
    import backend.security.defense_supervisor as ds

    monkeypatch.setattr(ds, "get_defense_supervisor", lambda: supervisor)

    request = _make_request()
    response = await gateway.process(request)

    assert response.content == "model answer"
    assert request.meta["defense_supervisor"]["recommended_action"] == "ALLOW"


def test_recent_context_summary_excludes_latest_and_truncates():
    messages = [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "x" * 500},
        {"role": "user", "content": "latest question"},
    ]
    summary = LLMGateway._recent_context_summary(messages, max_chars=100)

    assert "latest question" not in summary
    assert "first question" in summary
    assert "x" * 101 not in summary
