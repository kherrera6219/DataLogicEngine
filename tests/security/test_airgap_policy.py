"""Bounded tests for the experimental loopback-only model restriction.

These do not establish a complete air-gap boundary or a governed request.
"""

from __future__ import annotations

import httpx
import pytest

from core.security.egress_guard import (
    EgressDenied,
    EgressPolicy,
    GuardedAsyncHTTPTransport,
    GuardedHTTPTransport,
)


@pytest.mark.parametrize(
    "endpoint",
    ["https://models.example/v1", "http://192.0.2.1/v1", "http://localhost/v1"],
)
def test_experimental_airgap_rejects_remote_and_hostname_endpoints(
    monkeypatch, endpoint
):
    monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", "true")
    with pytest.raises(EgressDenied, match="loopback IP"):
        EgressPolicy.for_endpoint(endpoint)


@pytest.mark.parametrize(
    "endpoint", ["http://127.0.0.1:8080/v1", "http://[::1]:8080/v1"]
)
def test_experimental_airgap_accepts_loopback_model_endpoint(monkeypatch, endpoint):
    monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", "true")
    assert len(EgressPolicy.for_endpoint(endpoint).origins()) == 1


def test_enabling_experimental_airgap_blocks_preexisting_remote_policy(monkeypatch):
    monkeypatch.delenv("DLE_EXPERIMENTAL_AIR_GAP", raising=False)
    policy = EgressPolicy.for_endpoint("https://models.example/v1")
    monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", "true")

    def fail_if_sent(_transport, _request):
        pytest.fail("Remote request reached the network transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_sent)
    with httpx.Client(
        transport=GuardedHTTPTransport(policy), trust_env=False
    ) as client:
        with pytest.raises(EgressDenied, match="loopback IP"):
            client.get("https://models.example/v1")


@pytest.mark.asyncio
async def test_async_transport_blocks_preexisting_remote_policy(monkeypatch):
    monkeypatch.delenv("DLE_EXPERIMENTAL_AIR_GAP", raising=False)
    policy = EgressPolicy.for_endpoint("https://models.example/v1")
    monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", "true")

    async def fail_if_sent(_transport, _request):
        pytest.fail("Remote request reached the network transport")

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", fail_if_sent)
    async with httpx.AsyncClient(
        transport=GuardedAsyncHTTPTransport(policy), trust_env=False
    ) as client:
        with pytest.raises(EgressDenied, match="loopback IP"):
            await client.get("https://models.example/v1")


@pytest.mark.parametrize("setting", ["", "tru"])
def test_invalid_experimental_airgap_configuration_fails_closed(monkeypatch, setting):
    monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", setting)
    with pytest.raises(EgressDenied, match="Invalid DLE_EXPERIMENTAL_AIR_GAP"):
        EgressPolicy.for_endpoint("http://127.0.0.1:8080/v1")


def test_optional_model_call_does_not_hide_airgap_denial(monkeypatch):
    from backend.llm_gateway import active_model

    monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", "true")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://models.example/v1")
    monkeypatch.setattr(
        active_model,
        "_resolve_active_cloud_configuration",
        lambda: ("openai", "test-key", "gpt-6-sol", None),
    )
    with pytest.raises(EgressDenied, match="loopback IP"):
        active_model.generate_with_active_model("test")


def test_dsqp_does_not_hide_airgap_denial(monkeypatch):
    from backend.dsqp.dsqp_answer_generator import DSQPAnswerGenerator
    from backend.llm_gateway import active_model

    def deny(*_args, **_kwargs):
        raise EgressDenied("Air-gap mode requires a loopback IP")

    monkeypatch.setattr(active_model, "generate_with_active_model", deny)
    with pytest.raises(EgressDenied, match="loopback IP"):
        DSQPAnswerGenerator()._complete("test")


def test_dsqp_injected_client_does_not_hide_policy_denial():
    from backend.dsqp.dsqp_answer_generator import DSQPAnswerGenerator

    class DeniedClient:
        def generate(self, **_kwargs):
            raise EgressDenied("Denied by policy")

    with pytest.raises(EgressDenied, match="Denied by policy"):
        DSQPAnswerGenerator(client=DeniedClient())._complete("test")
