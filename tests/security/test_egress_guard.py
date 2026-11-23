from __future__ import annotations

import ast
from pathlib import Path

import httpx
import pytest

from backend.llm_gateway.provider_errors import (
    ProviderFailureClass,
    classify_provider_failure,
)
from backend.llm_gateway.providers.google import GoogleProvider
from backend.llm_gateway.providers.openai import OpenAIProvider
from core.security.egress_guard import EgressDenied, EgressPolicy, GuardedHTTPTransport


def test_configured_origin_reaches_transport(monkeypatch):
    def respond(_transport, request):
        assert request.url.path == "/v1/model"
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    policy = EgressPolicy.for_endpoint("https://models.example:443/v1")
    with httpx.Client(
        transport=GuardedHTTPTransport(policy), trust_env=False
    ) as client:
        assert client.get("https://models.example/v1/model").json() == {"ok": True}
    assert policy.origins() == ("https://models.example",)


@pytest.mark.parametrize(
    ("endpoint", "url", "headers"),
    [
        (None, "https://models.example/complete", {}),
        ("https://models.example", "https://other.example/complete", {}),
        ("https://models.example", "https://models.example:444/complete", {}),
        ("https://models.example", "http://models.example/complete", {}),
        (
            "https://models.example",
            "https://models.example/complete",
            {"host": "other.example"},
        ),
    ],
)
def test_denial_happens_before_network(monkeypatch, endpoint, url, headers):
    def fail_if_called(_transport, _request):
        pytest.fail("Denied request reached HTTP transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_called)
    policy = EgressPolicy.for_endpoint(endpoint) if endpoint else EgressPolicy()
    with httpx.Client(
        transport=GuardedHTTPTransport(policy), trust_env=False
    ) as client:
        with pytest.raises(EgressDenied, match="unapproved outbound HTTP destination"):
            client.get(url, headers=headers)


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        "file:///fixture",
        "https://*.example/v1",
        "https://models.example/v1?key=fixture",
    ],
)
def test_invalid_endpoint_is_rejected(endpoint):
    with pytest.raises(EgressDenied):
        EgressPolicy.for_endpoint(endpoint)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_type", "model"),
    [(OpenAIProvider, "gpt-6-sol"), (GoogleProvider, "gemini-3.8-flash")],
)
async def test_provider_denial_remains_typed_and_non_retryable(
    monkeypatch, provider_type, model
):
    async def fail_if_called(_transport, _request):
        pytest.fail("Denied provider request reached HTTP transport")

    monkeypatch.setattr(
        httpx.AsyncHTTPTransport, "handle_async_request", fail_if_called
    )
    monkeypatch.setattr(EgressPolicy, "for_endpoint", classmethod(lambda cls, _: cls()))
    provider = provider_type(api_key="test-key")
    try:
        with pytest.raises(EgressDenied) as denied:
            await provider.complete(
                messages=[{"role": "user", "content": "ping"}], model=model
            )
        classified = classify_provider_failure(denied.value)
        assert classified.failure_class is ProviderFailureClass.POLICY_BLOCK
        assert not classified.retryable
        assert not classified.replayable
    finally:
        await provider.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("provider_type", "model", "base_url_env", "path"),
    [
        (OpenAIProvider, "gpt-6-sol", "OPENAI_BASE_URL", "/v1/responses"),
        (
            GoogleProvider,
            "gemini-3.8-flash",
            "GOOGLE_GEMINI_BASE_URL",
            "/v1/v1beta/models/",
        ),
    ],
)
async def test_provider_does_not_follow_redirect(
    monkeypatch, provider_type, model, base_url_env, path
):
    requests = []

    async def redirect(_transport, request):
        requests.append(request.url)
        return httpx.Response(
            307, headers={"location": "https://other.example/destination"}
        )

    monkeypatch.setenv(base_url_env, "https://models.example/v1")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8080")
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", redirect)
    provider = provider_type(api_key="test-key")
    try:
        from google.genai.errors import APIError
        from openai import APIStatusError

        with pytest.raises((APIError, APIStatusError, ValueError)):
            await provider.complete(
                messages=[{"role": "user", "content": "ping"}], model=model
            )
    finally:
        await provider.close()

    assert len(requests) == 1
    assert requests[0].host == "models.example"
    assert requests[0].path.startswith(path)


def test_provider_adapters_do_not_import_http_clients_directly():
    providers = (
        Path(__file__).resolve().parents[2] / "backend" / "llm_gateway" / "providers"
    )
    forbidden = {"aiohttp", "http", "httpx", "requests", "urllib", "urllib3"}
    for file in providers.glob("*.py"):
        for node in ast.walk(
            ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        ):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            assert not forbidden.intersection(name.split(".")[0] for name in modules), (
                file
            )
