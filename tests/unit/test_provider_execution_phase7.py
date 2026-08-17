from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.desktop.offline_queue import (
    delete_item,
    enqueue_chat_request,
    list_queue,
)
from backend.governed_execution.contracts import GovernedContext, GovernedMode, GovernedRequest
from backend.llm_gateway.provider_budget import ProviderBudgetPolicy
from backend.llm_gateway.provider_errors import (
    ProviderFailureClass,
    classify_provider_failure,
)
from backend.llm_gateway.providers.google import GoogleProvider
from backend.llm_gateway.providers.openai import OpenAIProvider


class _HTTPError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


@pytest.mark.parametrize(
    ("error", "failure_class", "retryable", "replayable"),
    [
        (_HTTPError("invalid API key", 401), ProviderFailureClass.INVALID_KEY, False, False),
        (_HTTPError("model not found", 404), ProviderFailureClass.INVALID_MODEL, False, False),
        (_HTTPError("rate limit", 429), ProviderFailureClass.RATE_LIMITED, False, False),
        (_HTTPError("service unavailable", 503), ProviderFailureClass.PROVIDER_OUTAGE, True, True),
        (TimeoutError("timed out"), ProviderFailureClass.TIMEOUT, True, True),
        (ConnectionError("DNS resolution failed"), ProviderFailureClass.NETWORK, True, True),
        (RuntimeError("unexpected contract bug"), ProviderFailureClass.UNKNOWN, False, False),
    ],
)
def test_provider_failure_classification_is_explicit(error, failure_class, retryable, replayable):
    result = classify_provider_failure(error)
    assert result.failure_class is failure_class
    assert result.retryable is retryable
    assert result.replayable is replayable


@pytest.mark.asyncio
async def test_openai_adapter_uses_async_client_and_disables_sdk_retries(monkeypatch):
    response = SimpleNamespace(
        id="resp-1",
        output_text="pong",
        usage=SimpleNamespace(input_tokens=2, output_tokens=1, total_tokens=3),
    )
    client = SimpleNamespace(
        responses=SimpleNamespace(create=AsyncMock(return_value=response)),
        close=AsyncMock(),
    )
    factory = MagicMock(return_value=client)
    monkeypatch.setattr("openai.AsyncOpenAI", factory)

    provider = OpenAIProvider(api_key="test-key", timeout_seconds=7)
    result = await provider.complete(
        messages=[{"role": "user", "content": "ping"}],
        model="gpt-5.6-sol",
        max_tokens=16,
    )
    await provider.close()

    assert result.text == "pong"
    assert result.usage["total_tokens"] == 3
    assert factory.call_args.kwargs["max_retries"] == 0
    assert client.responses.create.await_count == 1
    assert client.responses.create.await_args.kwargs["model"] == "gpt-5.6-sol"
    assert client.responses.create.await_args.kwargs["reasoning"] == {"effort": "high"}
    assert "temperature" not in client.responses.create.await_args.kwargs


@pytest.mark.asyncio
async def test_google_adapter_uses_async_generate_content(monkeypatch):
    response = SimpleNamespace(
        text="pong",
        usage_metadata=SimpleNamespace(
            prompt_token_count=2,
            candidates_token_count=1,
            total_token_count=3,
        ),
    )
    aio = SimpleNamespace(
        models=SimpleNamespace(generate_content=AsyncMock(return_value=response)),
        aclose=AsyncMock(),
    )
    client = SimpleNamespace(aio=aio)
    monkeypatch.setattr("google.genai.Client", MagicMock(return_value=client))

    provider = GoogleProvider(api_key="test-key", timeout_seconds=7)
    result = await provider.complete(
        messages=[{"role": "user", "content": "ping"}],
        model="gemini-3.7-flash",
        max_tokens=16,
    )
    await provider.close()

    assert result.text == "pong"
    assert aio.models.generate_content.await_count == 1
    assert aio.models.generate_content.await_args.kwargs["model"] == "gemini-3.7-flash"
    assert aio.aclose.await_count == 1


def test_standard_and_enhanced_call_budgets_cannot_be_raised_by_renderer():
    assert ProviderBudgetPolicy.request_call_limit(
        GovernedMode.STANDARD, {"max_provider_calls": 99}
    ) == 1
    assert ProviderBudgetPolicy.request_call_limit(
        GovernedMode.ENHANCED, {"max_provider_calls": 99}
    ) == 2
    assert ProviderBudgetPolicy.request_call_limit(
        GovernedMode.ENHANCED, {"max_provider_calls": 1}
    ) == 1


def test_request_budget_counts_retries_as_provider_calls():
    request = GovernedRequest(
        messages=[{"role": "user", "content": "hello"}],
        mode=GovernedMode.STANDARD,
    )
    context = GovernedContext(request=request, provider_call_count=1)
    decision = ProviderBudgetPolicy().evaluate(
        context=context,
        projected_input_tokens=10,
        projected_output_tokens=10,
    )
    assert decision.allowed is False
    assert decision.code == "REQUEST_CALLS_HARD_LIMIT"


def test_monthly_spend_ceiling_is_server_enforced_when_price_is_known(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_SPEND_USD_PER_MONTH", "1.00")
    request = GovernedRequest(
        messages=[{"role": "user", "content": "hello"}],
        mode=GovernedMode.STANDARD,
    )
    context = GovernedContext(request=request)

    decision = ProviderBudgetPolicy().evaluate(
        context=context,
        projected_input_tokens=10,
        projected_output_tokens=10,
        projected_cost_usd=1.01,
    )

    assert decision.allowed is False
    assert decision.code == "MONTHLY_SPEND_USD_HARD_LIMIT"


def test_unknown_price_uses_call_and_token_limits_instead_of_zero_cost(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_SPEND_USD_PER_MONTH", "1.00")
    request = GovernedRequest(
        messages=[{"role": "user", "content": "hello"}],
        mode=GovernedMode.STANDARD,
    )
    context = GovernedContext(request=request)

    decision = ProviderBudgetPolicy().evaluate(
        context=context,
        projected_input_tokens=10,
        projected_output_tokens=10,
        projected_cost_usd=None,
    )

    assert decision.allowed is True
    assert decision.usage["monthly_spend_usd"] is None
    assert decision.limits["monthly_spend_usd"] == 1.0


def test_spend_warning_requires_explicit_owner_confirmation(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_SPEND_USD_PER_MONTH", "1.00")
    request = GovernedRequest(
        messages=[{"role": "user", "content": "hello"}],
        mode=GovernedMode.STANDARD,
    )
    context = GovernedContext(request=request)

    warning = ProviderBudgetPolicy().evaluate(
        context=context,
        projected_input_tokens=10,
        projected_output_tokens=10,
        projected_cost_usd=0.80,
    )
    request.metadata["budget_warning_confirmed"] = True
    confirmed = ProviderBudgetPolicy().evaluate(
        context=context,
        projected_input_tokens=10,
        projected_output_tokens=10,
        projected_cost_usd=0.80,
    )

    assert warning.allowed is False
    assert warning.code == "BUDGET_WARNING_CONFIRMATION_REQUIRED"
    assert confirmed.allowed is True


def test_offline_queue_encrypts_payload_deduplicates_and_hides_content(tmp_path, monkeypatch):
    path = tmp_path / "offline_queue.json"
    monkeypatch.setenv("DATALOGIC_OFFLINE_QUEUE_PATH", str(path))
    monkeypatch.setenv("IS_DESKTOP_APP", "false")
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "phase7-test-secret")
    payload = {
        "request_id": "request-12345",
        "messages": [{"role": "user", "content": "sensitive hello"}],
    }

    first = enqueue_chat_request(payload, failure_class="network")
    second = enqueue_chat_request(payload, failure_class="network")
    raw = path.read_text(encoding="utf-8")

    assert first["id"] == second["id"]
    assert first["encrypted"] is True
    assert "sensitive hello" not in raw
    assert "payload" not in list_queue()["items"][0]
    assert list_queue(include_payload=True)["items"][0]["payload"] == payload
    assert delete_item(first["id"]) is True
    assert list_queue()["items"] == []


@pytest.mark.parametrize("failure_class", ["invalid_key", "rate_limited", "policy_block", "internal_error"])
def test_offline_queue_rejects_non_transient_failure_classes(tmp_path, monkeypatch, failure_class):
    monkeypatch.setenv("DATALOGIC_OFFLINE_QUEUE_PATH", str(tmp_path / "queue.json"))
    with pytest.raises(ValueError, match="not replayable"):
        enqueue_chat_request(
            {"messages": [{"role": "user", "content": "hello"}]},
            failure_class=failure_class,
        )
