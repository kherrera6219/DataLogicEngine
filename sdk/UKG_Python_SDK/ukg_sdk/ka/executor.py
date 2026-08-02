"""API-backed Knowledge Algorithm client.

The SDK no longer owns a private handler registry. All execution is sent to the
installed DataLogicEngine service, which applies the canonical manifest,
authorization, policy, trace, and effect contracts.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol


class KAAPITransport(Protocol):
    def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...

    def post(
        self, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


class AsyncKAAPITransport(Protocol):
    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...

    async def post(
        self, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


@dataclass
class KAExecutionContext:
    """Compatibility request model sent to the canonical service."""

    ka_id: str
    input: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def inputs(self) -> dict[str, Any]:
        return self.input


@dataclass
class KAExecutionResult:
    """Normalized SDK view of a canonical service execution."""

    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    error_code: str | None = None
    duration_ms: int = 0
    ka_id: str | None = None
    trace_id: str | None = None
    canonical_result: dict[str, Any] | None = None

    @property
    def outputs(self) -> dict[str, Any]:
        return self.output


@dataclass(frozen=True)
class KAProductPlan:
    """Reviewed server plan and its principal-owned durable run."""

    run: dict[str, Any]
    plan: dict[str, Any]
    confirmation_token: str | None


class KAExecutor:
    """Compatibility name for the authenticated KA API client."""

    def __init__(
        self,
        client: KAAPITransport | None = None,
        *,
        registry_path: str | None = None,
        registry: Any = None,
    ):
        if registry_path is not None or registry is not None:
            raise TypeError(
                "Client-side KA registries were removed; use the generated "
                "manifest and installed DataLogicEngine service"
            )
        if client is None:
            raise TypeError(
                "KAExecutor requires an authenticated UKGClient transport"
            )
        self.client = client

    def register(self, ka_id: str, handler: Any) -> None:
        del ka_id, handler
        raise TypeError(
            "Client-side KA handlers are not a production execution surface"
        )

    def list(self, **params: Any) -> dict[str, Any]:
        return self.client.get("ka/algorithms", params=params or None)

    def get(self, ka_id: str) -> dict[str, Any]:
        return self.client.get(f"ka/algorithms/{ka_id}")

    def plan(
        self,
        ka_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
        mode: str = "production",
        request_id: str | None = None,
        session_id: str | None = None,
        tier: str | None = None,
        layer: str | None = None,
        persona: str | None = None,
        metadata: dict[str, Any] | None = None,
        budget: dict[str, int] | None = None,
    ) -> KAProductPlan:
        payload = self.client.post(
            "ka/runs/plan",
            json=_plan_request(
                ka_id,
                inputs,
                idempotency_key=idempotency_key,
                mode=mode,
                request_id=request_id,
                session_id=session_id,
                tier=tier,
                layer=layer,
                persona=persona,
                metadata=metadata,
                budget=budget,
            ),
        )
        return _normalize_plan(payload)

    def execute_plan(
        self,
        run_id: str,
        *,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        return self.client.post(
            f"ka/runs/{run_id}/execute",
            json=(
                {"confirmation_token": confirmation_token}
                if confirmation_token
                else {}
            ),
        )

    def runs(self, *, limit: int = 50) -> dict[str, Any]:
        return self.client.get(
            "ka/runs",
            params={"limit": max(1, min(200, int(limit)))},
        )

    def run(self, run_id: str) -> dict[str, Any]:
        return self.client.get(f"ka/runs/{run_id}")

    def result(self, run_id: str) -> dict[str, Any]:
        return self.client.get(f"ka/runs/{run_id}/result")

    def trace(self, run_id: str) -> dict[str, Any]:
        return self.client.get(f"ka/runs/{run_id}/trace")

    def artifacts(self, run_id: str) -> dict[str, Any]:
        return self.client.get(f"ka/runs/{run_id}/artifacts")

    def effects(self, run_id: str) -> dict[str, Any]:
        return self.client.get(f"ka/runs/{run_id}/effects")

    def cancel(self, run_id: str) -> dict[str, Any]:
        return self.client.post(f"ka/runs/{run_id}/cancel", json={})

    def execute(
        self,
        ka_id: str,
        inputs: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> KAExecutionResult:
        started = time.perf_counter()
        actual_input = dict(inputs or kwargs.pop("input", {}) or {})
        metadata = dict(meta or {})
        metadata.update(kwargs)
        request: dict[str, Any] = {"input": actual_input}
        if metadata:
            request["context"] = metadata
        payload = self.client.post(
            f"ka/algorithms/{ka_id}/execute",
            json=request,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return _normalize_result(payload, ka_id=ka_id, duration_ms=duration_ms)

    def run_all(self, inputs: dict[str, Any], tier: str | None = None) -> dict[str, Any]:
        del inputs, tier
        raise TypeError(
            "Run-all is forbidden; the server selects an applicable bounded KA DAG"
        )


class AsyncKAExecutor:
    """Asynchronous authenticated client for the canonical KA service."""

    def __init__(self, client: AsyncKAAPITransport | None = None):
        if client is None:
            raise TypeError(
                "AsyncKAExecutor requires an authenticated UKGAsyncClient transport"
            )
        self.client = client

    async def list(self, **params: Any) -> dict[str, Any]:
        return await self.client.get("ka/algorithms", params=params or None)

    async def get(self, ka_id: str) -> dict[str, Any]:
        return await self.client.get(f"ka/algorithms/{ka_id}")

    async def plan(
        self,
        ka_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        idempotency_key: str | None = None,
        mode: str = "production",
        request_id: str | None = None,
        session_id: str | None = None,
        tier: str | None = None,
        layer: str | None = None,
        persona: str | None = None,
        metadata: dict[str, Any] | None = None,
        budget: dict[str, int] | None = None,
    ) -> KAProductPlan:
        payload = await self.client.post(
            "ka/runs/plan",
            json=_plan_request(
                ka_id,
                inputs,
                idempotency_key=idempotency_key,
                mode=mode,
                request_id=request_id,
                session_id=session_id,
                tier=tier,
                layer=layer,
                persona=persona,
                metadata=metadata,
                budget=budget,
            ),
        )
        return _normalize_plan(payload)

    async def execute_plan(
        self,
        run_id: str,
        *,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        return await self.client.post(
            f"ka/runs/{run_id}/execute",
            json=(
                {"confirmation_token": confirmation_token}
                if confirmation_token
                else {}
            ),
        )

    async def runs(self, *, limit: int = 50) -> dict[str, Any]:
        return await self.client.get(
            "ka/runs",
            params={"limit": max(1, min(200, int(limit)))},
        )

    async def run(self, run_id: str) -> dict[str, Any]:
        return await self.client.get(f"ka/runs/{run_id}")

    async def result(self, run_id: str) -> dict[str, Any]:
        return await self.client.get(f"ka/runs/{run_id}/result")

    async def trace(self, run_id: str) -> dict[str, Any]:
        return await self.client.get(f"ka/runs/{run_id}/trace")

    async def artifacts(self, run_id: str) -> dict[str, Any]:
        return await self.client.get(f"ka/runs/{run_id}/artifacts")

    async def effects(self, run_id: str) -> dict[str, Any]:
        return await self.client.get(f"ka/runs/{run_id}/effects")

    async def cancel(self, run_id: str) -> dict[str, Any]:
        return await self.client.post(f"ka/runs/{run_id}/cancel", json={})

    async def execute(
        self,
        ka_id: str,
        inputs: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> KAExecutionResult:
        started = time.perf_counter()
        actual_input = dict(inputs or kwargs.pop("input", {}) or {})
        metadata = dict(meta or {})
        metadata.update(kwargs)
        request: dict[str, Any] = {"input": actual_input}
        if metadata:
            request["context"] = metadata
        payload = await self.client.post(
            f"ka/algorithms/{ka_id}/execute",
            json=request,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return _normalize_result(payload, ka_id=ka_id, duration_ms=duration_ms)

    async def run_all(
        self, inputs: dict[str, Any], tier: str | None = None
    ) -> dict[str, Any]:
        del inputs, tier
        raise TypeError(
            "Run-all is forbidden; the server selects an applicable bounded KA DAG"
        )


def _normalize_result(
    payload: dict[str, Any],
    *,
    ka_id: str,
    duration_ms: int,
) -> KAExecutionResult:
    result = payload.get("result")
    if not isinstance(result, dict):
        result = {}
    canonical = result.get("canonical_result")
    if not isinstance(canonical, dict):
        canonical = payload.get("canonical_result")
    output = result.get("output", {})
    if not isinstance(output, dict):
        output = {}
    return KAExecutionResult(
        ok=bool(payload.get("success")),
        output=output,
        error=payload.get("error") or result.get("error"),
        error_code=payload.get("code") or result.get("error_code"),
        duration_ms=int(result.get("execution_time_ms", duration_ms)),
        ka_id=result.get("algorithm_id", ka_id),
        trace_id=result.get("trace_id"),
        canonical_result=canonical if isinstance(canonical, dict) else None,
    )


def _plan_request(
    ka_id: str,
    inputs: dict[str, Any] | None,
    *,
    idempotency_key: str | None,
    mode: str,
    request_id: str | None,
    session_id: str | None,
    tier: str | None,
    layer: str | None,
    persona: str | None,
    metadata: dict[str, Any] | None,
    budget: dict[str, int] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ka_id": ka_id,
        "input": dict(inputs or {}),
        "mode": mode,
        "idempotency_key": idempotency_key or str(uuid.uuid4()),
        "metadata": dict(metadata or {}),
        "budget": dict(budget or {}),
    }
    optional = {
        "request_id": request_id,
        "session_id": session_id,
        "tier": tier,
        "layer": layer,
        "persona": persona,
    }
    payload.update({
        key: value
        for key, value in optional.items()
        if value is not None
    })
    return payload


def _normalize_plan(payload: dict[str, Any]) -> KAProductPlan:
    run = payload.get("run")
    plan = payload.get("plan")
    if not isinstance(run, dict) or not isinstance(plan, dict):
        raise TypeError("KA plan response did not contain run and plan records")
    token = payload.get("confirmation_token")
    return KAProductPlan(
        run=run,
        plan=plan,
        confirmation_token=token if isinstance(token, str) else None,
    )
