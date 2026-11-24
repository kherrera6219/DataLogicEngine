"""The selected provider's saved endpoint reaches every guarded client."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.security.egress_guard import EgressDenied


@pytest.mark.parametrize(
    ("provider_type", "model", "class_name"),
    [
        ("openai", "gpt-6-sol", "OpenAIProvider"),
        ("google", "gemini-3.8-flash", "GoogleProvider"),
    ],
)
def test_optional_model_uses_selected_saved_endpoint(
    monkeypatch, provider_type, model, class_name
):
    import models
    from backend.llm_gateway import active_model, providers

    row = SimpleNamespace(
        provider_type=provider_type,
        model_id=model,
        endpoint="http://127.0.0.1:8765/v1",
        get_api_key=lambda: "test-key",
    )
    provider_model = MagicMock()
    provider_model.query.filter_by.return_value.order_by.return_value.all.return_value = [
        row
    ]
    monkeypatch.setattr(models, "LLMProvider", provider_model)
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", provider_type)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://other.example/v1")
    monkeypatch.setenv("GOOGLE_GEMINI_BASE_URL", "https://other.example/v1")
    calls = []

    class FakeProvider:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        async def complete(self, **_kwargs):
            return SimpleNamespace(text="local answer")

        async def close(self):
            pass

    monkeypatch.setattr(providers, class_name, FakeProvider)
    assert active_model.generate_with_active_model("test") == "local answer"
    assert calls[0]["base_url"] == row.endpoint


def test_invalid_saved_endpoint_does_not_fallback_to_environment(monkeypatch):
    import models
    from backend.llm_gateway import active_model

    row = SimpleNamespace(
        provider_type="openai",
        model_id="gpt-6-sol",
        endpoint=123,
        get_api_key=lambda: "test-key",
    )
    provider_model = MagicMock()
    provider_model.query.filter_by.return_value.order_by.return_value.all.return_value = [
        row
    ]
    monkeypatch.setattr(models, "LLMProvider", provider_model)
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "other-test-key")
    with pytest.raises(EgressDenied, match="endpoint must be text"):
        active_model.generate_with_active_model("test")


def test_google_gateway_passes_selected_saved_endpoint(monkeypatch):
    from backend.llm_gateway import gateway as gateway_module

    provider = SimpleNamespace(
        provider_type="google",
        endpoint="http://127.0.0.1:8765/v1",
        get_api_key=lambda: "test-key",
        timeout_seconds=30,
    )
    factory = MagicMock()
    monkeypatch.setattr(gateway_module, "GoogleProvider", factory)
    gateway = gateway_module.LLMGateway(db_session=MagicMock())
    gateway._create_sdk_provider(provider)
    assert factory.call_args.kwargs["base_url"] == provider.endpoint


def test_google_provider_guard_uses_saved_endpoint(monkeypatch):
    from backend.llm_gateway.providers.google import GoogleProvider

    monkeypatch.setenv("GOOGLE_GEMINI_BASE_URL", "https://other.example/v1")
    provider = GoogleProvider(api_key="test-key", base_url="http://127.0.0.1:8765/v1")
    try:
        assert provider.egress_policy.origins() == ("http://127.0.0.1:8765",)
    finally:
        provider.client.close()


@pytest.mark.parametrize("provider_type", ["openai", "google"])
def test_saved_remote_endpoint_is_refused_in_experimental_mode(
    monkeypatch, provider_type
):
    from backend.llm_gateway.providers.google import GoogleProvider
    from backend.llm_gateway.providers.openai import OpenAIProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", "true")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:8765/v1")
    monkeypatch.setenv("GOOGLE_GEMINI_BASE_URL", "http://127.0.0.1:8765/v1")
    provider = {"openai": OpenAIProvider, "google": GoogleProvider}[provider_type]
    with pytest.raises(EgressDenied, match="loopback IP"):
        provider(api_key="test-key", base_url="https://remote.example/v1")
