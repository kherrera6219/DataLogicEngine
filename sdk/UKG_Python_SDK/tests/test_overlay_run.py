"""The SDK overlay must be transport-only after Phase 5."""

from __future__ import annotations

import json

import httpx
import pytest

from ukg_sdk.overlay import UKGOverlay


def _client(seen: list[dict]) -> httpx.AsyncClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            {
                "path": request.url.path,
                "body": json.loads(request.content),
                "authorization": request.headers.get("authorization"),
            }
        )
        return httpx.Response(
            200,
            json={
                "data": {
                    "contract_version": "governed.v1",
                    "status": "completed",
                    "response": "service answer",
                    "run_id": "run-123",
                    "confidence_score": None,
                    "claims": [],
                    "evidence_count": 0,
                    "trace_summary": {"steps": ["admission", "provider"]},
                }
            },
        )

    return httpx.AsyncClient(
        base_url="http://test/api/v1", transport=httpx.MockTransport(handler)
    )


@pytest.mark.asyncio
async def test_run_uses_canonical_gateway_and_preserves_unmeasured_confidence():
    seen: list[dict] = []
    client = _client(seen)
    overlay = UKGOverlay(client=client, api_key="secret")

    result = await overlay.run(query="What is governed execution?", mode="enhanced")

    assert result["answer"] == "service answer"
    assert result["contract_version"] == "governed.v1"
    assert result["confidence"] is None
    assert result["trace"] == ["admission", "provider"]
    assert seen == [
        {
            "path": "/api/v1/gateway/chat",
            "body": {
                "messages": [
                    {"role": "user", "content": "What is governed execution?"}
                ],
                "mode": "enhanced",
                "provider": None,
                "model": None,
                "temperature": 0.2,
                "max_tokens": 1024,
                "session_id": None,
                "meta": {
                    "source": "python_sdk",
                    "sdk_user_id": "anonymous",
                    "correlation_id": None,
                    "tier_override": None,
                    "legacy_provider_argument_ignored": False,
                },
            },
            "authorization": "Bearer secret",
        }
    ]
    await client.aclose()


@pytest.mark.asyncio
async def test_legacy_provider_is_never_called_or_owned_by_overlay():
    class ExplodingProvider:
        async def complete(self, *_args, **_kwargs):
            raise AssertionError("SDK must not invoke a provider")

    seen: list[dict] = []
    client = _client(seen)
    overlay = UKGOverlay(client=client, provider=ExplodingProvider())

    result = await overlay.run(query="Use the service")

    assert result["ok"] is True
    assert seen[0]["body"]["meta"]["legacy_provider_argument_ignored"] is True
    await client.aclose()


@pytest.mark.asyncio
async def test_empty_query_is_rejected_before_transport():
    seen: list[dict] = []
    client = _client(seen)
    overlay = UKGOverlay(client=client)

    with pytest.raises(ValueError, match="query is required"):
        await overlay.run(query="  ")

    assert seen == []
    await client.aclose()
