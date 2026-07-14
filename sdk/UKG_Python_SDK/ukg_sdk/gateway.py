"""Typed thin clients for the versioned DataLogicEngine gateway contract."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Iterator, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


GATEWAY_CONTRACT_VERSION = "dle-gateway.v1"


class GatewayResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    request_id: str
    response: str
    run_id: str | None = None
    provider_used: str | None = None
    model_used: str | None = None
    virtual_model: str
    gateway_contract_version: str
    contract_version: str
    status: str
    usage: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)


class GatewayCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str
    profile: Literal["desktop_loopback", "same_host_gateway"]
    virtual_models: dict[str, dict[str, Any]]
    scopes: list[str]
    provider_credentials_exposed: Literal[False]


class GatewayJob(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_id: str
    request_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled", "expired"]
    virtual_model: str
    run_id: str | None = None
    response_status: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    result_storage: Literal["postgresql_ciphertext", "minio_ciphertext"] = "postgresql_ciphertext"
    result_size_bytes: int | None = None
    gateway_contract_version: str
    status_url: str
    result_url: str
    cancel_url: str


def _chat_payload(
    messages: list[dict[str, Any]],
    *,
    virtual_model: str,
    request_id: str | None,
    idempotency_key: str | None,
    session_id: str | None,
    constraints: dict[str, Any] | None,
    max_tokens: int | None,
    meta: dict[str, Any] | None,
) -> dict[str, Any]:
    if not messages:
        raise ValueError("messages are required")
    payload: dict[str, Any] = {
        "messages": messages,
        "virtual_model": virtual_model,
        "request_id": request_id or str(uuid.uuid4()),
        "idempotency_key": idempotency_key or str(uuid.uuid4()),
        "session_id": session_id,
        "constraints": constraints or {},
        "max_tokens": max_tokens,
        "meta": meta or {},
    }
    return {key: value for key, value in payload.items() if value is not None}


def _unwrap_result(payload: dict[str, Any]) -> GatewayResult:
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise ValueError("Gateway returned a non-object result")
    result = GatewayResult.model_validate(data)
    if result.gateway_contract_version != GATEWAY_CONTRACT_VERSION:
        raise ValueError("Gateway contract version is not supported by this SDK")
    return result


def _parse_sse_line(line: str) -> dict[str, Any] | None:
    if not line.startswith("data:"):
        return None
    payload = json.loads(line.removeprefix("data:").strip())
    if not isinstance(payload, dict):
        raise ValueError("Gateway SSE event must be an object")
    return payload


class GatewayClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        virtual_model: str = "dle-standard",
        request_id: str | None = None,
        idempotency_key: str | None = None,
        session_id: str | None = None,
        constraints: dict[str, Any] | None = None,
        max_tokens: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> GatewayResult:
        payload = _chat_payload(
            messages,
            virtual_model=virtual_model,
            request_id=request_id,
            idempotency_key=idempotency_key,
            session_id=session_id,
            constraints=constraints,
            max_tokens=max_tokens,
            meta=meta,
        )
        return _unwrap_result(self._client.post("/gateway/chat", json=payload))

    def capabilities(self) -> GatewayCapabilities:
        return GatewayCapabilities.model_validate(
            self._client.get("/gateway/capabilities")
        )

    def cancel(self, request_id: str) -> dict[str, Any]:
        return self._client.post(f"/gateway/requests/{request_id}/cancel")

    def create_run(self, messages: list[dict[str, Any]], **kwargs: Any) -> GatewayJob:
        payload = _chat_payload(
            messages,
            virtual_model=kwargs.pop("virtual_model", "dle-standard"),
            request_id=kwargs.pop("request_id", None),
            idempotency_key=kwargs.pop("idempotency_key", None),
            session_id=kwargs.pop("session_id", None),
            constraints=kwargs.pop("constraints", None),
            max_tokens=kwargs.pop("max_tokens", None),
            meta=kwargs.pop("meta", None),
        )
        if kwargs:
            raise TypeError(f"Unsupported gateway run arguments: {', '.join(sorted(kwargs))}")
        return GatewayJob.model_validate(self._client.post("/gateway/runs", json=payload))

    def runs(self, *, limit: int = 50) -> list[GatewayJob]:
        payload = self._client.get(f"/gateway/runs?limit={max(1, min(limit, 200))}")
        return [GatewayJob.model_validate(item) for item in payload.get("jobs", [])]

    def run(self, job_id: str) -> GatewayJob:
        return GatewayJob.model_validate(self._client.get(f"/gateway/runs/{job_id}"))

    def run_result(self, job_id: str) -> dict[str, Any]:
        return self._client.get(f"/gateway/runs/{job_id}/result")

    def cancel_run(self, job_id: str) -> GatewayJob:
        return GatewayJob.model_validate(
            self._client.post(f"/gateway/runs/{job_id}/cancel")
        )

    def trace(self, run_id: str) -> dict[str, Any]:
        return self._client.get(f"/gateway/traces/{run_id}")

    def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        virtual_model: str = "dle-standard",
        request_id: str | None = None,
        session_id: str | None = None,
        constraints: dict[str, Any] | None = None,
        max_tokens: int | None = None,
        meta: dict[str, Any] | None = None,
    ) -> Iterator[dict[str, Any]]:
        payload = _chat_payload(
            messages,
            virtual_model=virtual_model,
            request_id=request_id,
            idempotency_key="stream-placeholder",
            session_id=session_id,
            constraints=constraints,
            max_tokens=max_tokens,
            meta=meta,
        )
        payload.pop("idempotency_key", None)
        with self._client._client.stream(
            "POST",
            self._client._build_url("/gateway/chat/stream"),
            headers=self._client._get_headers(),
            json=payload,
        ) as response:
            if response.status_code >= 400:
                response.read()
                self._client._handle_error(response)
            for line in response.iter_lines():
                event = _parse_sse_line(line)
                if event is not None:
                    yield event


class AsyncGatewayClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> GatewayResult:
        payload = _chat_payload(
            messages,
            virtual_model=kwargs.pop("virtual_model", "dle-standard"),
            request_id=kwargs.pop("request_id", None),
            idempotency_key=kwargs.pop("idempotency_key", None),
            session_id=kwargs.pop("session_id", None),
            constraints=kwargs.pop("constraints", None),
            max_tokens=kwargs.pop("max_tokens", None),
            meta=kwargs.pop("meta", None),
        )
        if kwargs:
            raise TypeError(f"Unsupported gateway chat arguments: {', '.join(sorted(kwargs))}")
        return _unwrap_result(await self._client.post("/gateway/chat", json=payload))

    async def capabilities(self) -> GatewayCapabilities:
        return GatewayCapabilities.model_validate(
            await self._client.get("/gateway/capabilities")
        )

    async def cancel(self, request_id: str) -> dict[str, Any]:
        return await self._client.post(f"/gateway/requests/{request_id}/cancel")

    async def create_run(self, messages: list[dict[str, Any]], **kwargs: Any) -> GatewayJob:
        payload = _chat_payload(
            messages,
            virtual_model=kwargs.pop("virtual_model", "dle-standard"),
            request_id=kwargs.pop("request_id", None),
            idempotency_key=kwargs.pop("idempotency_key", None),
            session_id=kwargs.pop("session_id", None),
            constraints=kwargs.pop("constraints", None),
            max_tokens=kwargs.pop("max_tokens", None),
            meta=kwargs.pop("meta", None),
        )
        if kwargs:
            raise TypeError(f"Unsupported gateway run arguments: {', '.join(sorted(kwargs))}")
        return GatewayJob.model_validate(await self._client.post("/gateway/runs", json=payload))

    async def runs(self, *, limit: int = 50) -> list[GatewayJob]:
        payload = await self._client.get(f"/gateway/runs?limit={max(1, min(limit, 200))}")
        return [GatewayJob.model_validate(item) for item in payload.get("jobs", [])]

    async def run(self, job_id: str) -> GatewayJob:
        return GatewayJob.model_validate(await self._client.get(f"/gateway/runs/{job_id}"))

    async def run_result(self, job_id: str) -> dict[str, Any]:
        return await self._client.get(f"/gateway/runs/{job_id}/result")

    async def cancel_run(self, job_id: str) -> GatewayJob:
        return GatewayJob.model_validate(
            await self._client.post(f"/gateway/runs/{job_id}/cancel")
        )

    async def trace(self, run_id: str) -> dict[str, Any]:
        return await self._client.get(f"/gateway/traces/{run_id}")

    async def stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
        payload = _chat_payload(
            messages,
            virtual_model=kwargs.pop("virtual_model", "dle-standard"),
            request_id=kwargs.pop("request_id", None),
            idempotency_key="stream-placeholder",
            session_id=kwargs.pop("session_id", None),
            constraints=kwargs.pop("constraints", None),
            max_tokens=kwargs.pop("max_tokens", None),
            meta=kwargs.pop("meta", None),
        )
        payload.pop("idempotency_key", None)
        if kwargs:
            raise TypeError(f"Unsupported gateway stream arguments: {', '.join(sorted(kwargs))}")
        async with self._client._client.stream(
            "POST",
            self._client._build_url("/gateway/chat/stream"),
            headers=self._client._get_headers(),
            json=payload,
        ) as response:
            if response.status_code >= 400:
                await response.aread()
                self._client._handle_error(response)
            async for line in response.aiter_lines():
                event = _parse_sse_line(line)
                if event is not None:
                    yield event
