from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.genai import types

from backend.governed_execution.contracts import GovernedRequest
from backend.llm_gateway import api
from backend.llm_gateway.governance import AIGovernanceEngine
from backend.llm_gateway.providers.google import GoogleProvider
from backend.llm_gateway.providers.openai import OpenAIProvider
from backend.llm_gateway.provider_manifest import provider_model_definition
from backend.llm_gateway.schemas import DesktopGatewayChatRequest, GatewayChatRequest
from backend.knowledge_algorithms.ka_1072_context_window_optimizer import ContextElement


@pytest.mark.asyncio
async def test_desktop_google_chat_uses_full_model_output_capacity(monkeypatch):
    preferences = SimpleNamespace(
        preferred_provider="google", preferred_model="gemini-3.8-flash"
    )
    lookup = MagicMock()
    lookup.filter_by.return_value.first.return_value = preferences
    monkeypatch.setattr(api, "UserAIPreferences", SimpleNamespace(query=lookup))
    gateway = SimpleNamespace(
        _get_eligible_providers=AsyncMock(
            return_value=[
                SimpleNamespace(provider_type="google", model_id="gemini-3.8-flash")
            ]
        )
    )

    assert (
        await api._chat_output_tokens({}, user_id=1, gateway=gateway, external=False)
        == 65_536
    )
    gateway._get_eligible_providers.assert_awaited_once_with("google", None)


@pytest.mark.asyncio
async def test_chat_output_default_preserves_explicit_and_external_limits(monkeypatch):
    lookup = MagicMock()
    lookup.filter_by.return_value.first.return_value = None
    monkeypatch.setattr(api, "UserAIPreferences", SimpleNamespace(query=lookup))
    gateway = SimpleNamespace(
        _get_eligible_providers=AsyncMock(
            return_value=[
                SimpleNamespace(provider_type="openai", model_id="gpt-6-sol")
            ]
        )
    )

    assert (
        await api._chat_output_tokens(
            {"max_tokens": 2048}, user_id=1, gateway=gateway, external=False
        )
        == 2048
    )
    assert (
        await api._chat_output_tokens({}, user_id=1, gateway=gateway, external=True)
        == 1024
    )
    assert (
        await api._chat_output_tokens({}, user_id=1, gateway=gateway, external=False)
        == 128_000
    )


def test_governed_request_retains_gemini_output_cap():
    request = GovernedRequest(
        messages=[{"role": "user", "content": "Explain this in detail"}],
        max_tokens=65_536,
    )
    assert request.max_tokens == 65_536


def test_google_adapter_sends_full_output_limit_to_sdk():
    provider = GoogleProvider.__new__(GoogleProvider)
    provider.types = types
    request = provider._request(
        [{"role": "user", "content": "Explain this in detail"}],
        "gemini-3.8-flash",
        0.7,
        65_536,
    )
    assert request["model"] == "gemini-3.8-flash"
    assert request["config"].max_output_tokens == 65_536


def test_openai_adapter_uses_gpt_6_sol_high_with_full_output_limit():
    request = OpenAIProvider._request(
        [{"role": "user", "content": "Explain this in detail"}],
        "gpt-6-sol",
        0.7,
        128_000,
    )
    assert request["model"] == "gpt-6-sol"
    assert request["max_output_tokens"] == 128_000
    assert request["reasoning"] == {"effort": "high"}


def test_model_input_budgets_match_declared_capabilities():
    openai = provider_model_definition("openai", "gpt-6-sol")
    google = provider_model_definition("google", "gemini-3.8-flash")
    assert (openai.max_context_tokens, openai.max_input_tokens, openai.max_output_tokens) == (
        1_050_000, 1_050_000, 128_000
    )
    assert (google.max_context_tokens, google.max_input_tokens, google.max_output_tokens) == (
        None, 1_048_576, 65_536
    )


def test_context_planner_accepts_model_sized_message():
    element = ContextElement(element_id="large-user-turn", token_count=1_048_576, relevance=1)
    assert element.token_count == 1_048_576


def test_desktop_input_does_not_inherit_public_gateway_message_limits():
    long_message = {"role": "user", "content": "A" * 200_001}
    many_messages = [{"role": "user", "content": "context"}] * 65
    assert DesktopGatewayChatRequest(messages=[long_message]).messages[0].content == long_message["content"]
    assert len(DesktopGatewayChatRequest(messages=many_messages).messages) == 65
    with pytest.raises(ValueError):
        GatewayChatRequest(messages=[long_message])
    with pytest.raises(ValueError):
        GatewayChatRequest(messages=many_messages)


def test_desktop_full_output_budget_is_reserved_and_operator_limit_remains_authoritative(
    monkeypatch,
):
    engine = AIGovernanceEngine(db_session=None)
    request = SimpleNamespace(
        meta={},
        max_tokens=65_536,
        user_id=None,
        api_key_id=None,
        principal_kind="desktop",
    )
    monkeypatch.delenv("AI_TOKEN_BUDGET_PER_REQUEST", raising=False)
    decision = engine.prepare_request(request, "Explain this in detail")
    assert decision.ok is True
    assert decision.estimated_request_tokens > 65_536

    monkeypatch.setenv("AI_TOKEN_BUDGET_PER_REQUEST", "32000")
    limited = engine.prepare_request(request, "Explain this in detail")
    assert limited.ok is False
    assert limited.error == "Token budget exceeded for this request"
