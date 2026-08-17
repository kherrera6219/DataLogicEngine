from __future__ import annotations

import json

import httpx
import pytest

from ukg_sdk import UKGAsyncClient, UKGClient
from ukg_sdk.exceptions import ConflictError, UKGError


def _result_payload() -> dict:
    return {
        "success": True,
        "data": {
            "request_id": "request-123",
            "response": "governed answer",
            "run_id": "run-123",
            "provider_used": "openai",
            "model_used": "gpt-5.6-sol",
            "virtual_model": "dle-standard",
            "gateway_contract_version": "dle-gateway.v1",
            "contract_version": "governed.v1",
            "status": "completed",
            "usage": {"tokens_in": 2, "tokens_out": 3},
            "confidence_score": None,
            "citations": [],
        },
    }


def _job_payload(status: str = "queued") -> dict:
    return {
        "job_id": "job-123",
        "request_id": "request-123",
        "status": status,
        "virtual_model": "dle-standard",
        "run_id": None,
        "response_status": None,
        "error_code": None,
        "error_message": None,
        "gateway_contract_version": "dle-gateway.v1",
        "status_url": "/api/v1/gateway/runs/job-123",
        "result_url": "/api/v1/gateway/runs/job-123/result",
        "cancel_url": "/api/v1/gateway/runs/job-123/cancel",
    }


def test_sync_gateway_chat_is_typed_and_automatically_idempotent() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=_result_payload())

    client = UKGClient(base_url="http://test/api/v1", api_key="ukg_secret")
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        result = client.gateway.chat(
            [{"role": "user", "content": "hello"}],
            request_id="request-123",
        )
    finally:
        client.close()

    assert result.response == "governed answer"
    assert result.gateway_contract_version == "dle-gateway.v1"
    assert seen[0]["virtual_model"] == "dle-standard"
    assert len(seen[0]["idempotency_key"]) >= 8


def test_gateway_stream_parses_typed_sse_objects_without_idempotency_field() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            headers={"Content-Type": "text/event-stream"},
            text=(
                'data: {"type":"stage","stage":"admission"}\n\n'
                'data: {"type":"done","request_id":"request-stream"}\n\n'
            ),
        )

    client = UKGClient(base_url="http://test/api/v1", api_key="ukg_secret")
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        events = list(client.gateway.stream(
            [{"role": "user", "content": "hello"}],
            request_id="request-stream",
        ))
    finally:
        client.close()

    assert [event["type"] for event in events] == ["stage", "done"]
    assert "idempotency_key" not in seen[0]


def test_gateway_async_run_methods_are_typed_and_retry_safe() -> None:
    seen: list[tuple[str, str, dict | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        seen.append((request.method, request.url.path, body))
        if request.url.path.endswith("/result"):
            return httpx.Response(200, json={"response": "governed job result"})
        if request.url.path.endswith("/cancel"):
            return httpx.Response(202, json=_job_payload("cancelled"))
        if request.method == "POST":
            return httpx.Response(202, json=_job_payload())
        if request.url.path.endswith("/runs"):
            return httpx.Response(200, json={"jobs": [_job_payload()]})
        return httpx.Response(200, json=_job_payload("running"))

    client = UKGClient(base_url="http://test/api/v1", api_key="ukg_secret")
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        created = client.gateway.create_run([{"role": "user", "content": "hello"}])
        listed = client.gateway.runs()
        status = client.gateway.run(created.job_id)
        result = client.gateway.run_result(created.job_id)
        cancelled = client.gateway.cancel_run(created.job_id)
    finally:
        client.close()

    assert created.status == "queued"
    assert listed[0].job_id == "job-123"
    assert status.status == "running"
    assert result["response"] == "governed job result"
    assert cancelled.status == "cancelled"
    create_body = seen[0][2]
    assert create_body is not None
    assert len(create_body["idempotency_key"]) >= 8


def test_sdk_retries_only_idempotent_writes_and_preserves_typed_conflict() -> None:
    calls = 0

    def transient_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("temporary", request=request)
        return httpx.Response(200, json=_result_payload())

    client = UKGClient(
        base_url="http://test/api/v1",
        api_key="ukg_secret",
        max_retries=2,
        retry_delay=0,
    )
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(transient_handler))
    try:
        result = client.gateway.chat([{"role": "user", "content": "hello"}])
    finally:
        client.close()
    assert result.response == "governed answer"
    assert calls == 2

    unsafe_calls = 0

    def unsafe_handler(request: httpx.Request) -> httpx.Response:
        nonlocal unsafe_calls
        unsafe_calls += 1
        raise httpx.ConnectError("temporary", request=request)

    client = UKGClient(base_url="http://test/api/v1", max_retries=3, retry_delay=0)
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(unsafe_handler))
    with pytest.raises(UKGError, match="1 attempt"):
        client.post("/unsafe-write", json={"value": 1})
    client.close()
    assert unsafe_calls == 1

    def conflict_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={"error": "changed request", "code": "IDEMPOTENCY_CONFLICT"},
        )

    client = UKGClient(base_url="http://test/api/v1")
    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(conflict_handler))
    with pytest.raises(ConflictError) as raised:
        client.gateway.chat([{"role": "user", "content": "hello"}])
    client.close()
    assert raised.value.code == "IDEMPOTENCY_CONFLICT"


@pytest.mark.asyncio
async def test_async_gateway_chat_uses_the_same_contract() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_result_payload())

    client = UKGAsyncClient(base_url="http://test/api/v1", api_key="ukg_secret")
    await client._client.aclose()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await client.gateway.chat(
            [{"role": "user", "content": "hello"}],
            request_id="request-123",
        )
    finally:
        await client.close()
    assert result.run_id == "run-123"
