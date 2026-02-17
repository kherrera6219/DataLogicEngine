# ruff: noqa: E402
"""
UKG API Client - Sync and Async implementations.
"""

from __future__ import annotations

import time
from typing import Any, Optional, TypeVar

import httpx
import logging

logger = logging.getLogger("ukg_sdk")

from ukg_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    UKGError,
    ValidationError,
)
from ukg_sdk.api_models import (
    AxisVector,
    ChatSession,
    Claim,
    ComplianceMapping,
    ComplianceResponse,
    Evidence,
    Export,
    KAInvocation,
    MemoryEvent,
    Persona,
    PolicyDecision,
    Run,
    RunsResponse,
    SessionsResponse,
    Stage,
    StageLog,
    TraceSpan,
)


T = TypeVar("T")


class BaseClient:
    """Base client with shared configuration."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:5000/api/v1",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ukg-sdk-python/0.3.1",
            "X-API-Version": "1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        if path.startswith("/"):
            path = path[1:]
        return f"{self.base_url}/{path}"
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}
        
        message = body.get("message", body.get("error", "Unknown error"))
        
        if response.status_code == 401:
            raise AuthenticationError(message, response.status_code, body)
        elif response.status_code == 403:
            raise AuthorizationError(message, response.status_code, body)
        elif response.status_code == 404:
            raise NotFoundError(message, response.status_code, body)
        elif response.status_code == 400:
            raise ValidationError(message, body.get("errors"), status_code=response.status_code)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
                status_code=response.status_code,
            )
        elif response.status_code >= 500:
            raise ServerError(message, response.status_code, body)
        else:
            raise UKGError(message, response.status_code, body)


class UKGClient(BaseClient):
    """Synchronous UKG API client."""
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = httpx.Client(timeout=self.timeout)
        
        # Initialize sub-clients
        self.sessions = SessionsClient(self)
        self.runs = RunsClient(self)
        self.exports = ExportsClient(self)
        self.compliance = ComplianceClient(self)
    
    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self) -> "UKGClient":
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic."""
        url = self._build_url(path)
        headers = self._get_headers()
        
        # Filter out None params
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{method} {url}")
                start_time = time.time()
                response = self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                )
                duration = time.time() - start_time
                logger.info(f"{method} {url} {response.status_code} ({duration:.3f}s)")
                
                if response.status_code >= 400:
                    self._handle_error(response)
                
                return response.json()
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except RateLimitError as e:
                last_error = e
                if e.retry_after and attempt < self.max_retries - 1:
                    time.sleep(e.retry_after)
                    continue
                raise
        
        raise UKGError(f"Request failed after {self.max_retries} attempts: {last_error}")
    
    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """GET request."""
        return self._request("GET", path, params=params)
    
    def post(
        self, path: str, json: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """POST request."""
        return self._request("POST", path, json=json)
    
    def patch(
        self, path: str, json: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """PATCH request."""
        return self._request("PATCH", path, json=json)
    
    def delete(self, path: str) -> dict[str, Any]:
        """DELETE request."""
        return self._request("DELETE", path)


class UKGAsyncClient(BaseClient):
    """Asynchronous UKG API client."""
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = httpx.AsyncClient(timeout=self.timeout)
        
        # Initialize sub-clients
        self.sessions = AsyncSessionsClient(self)
        self.runs = AsyncRunsClient(self)
        self.exports = AsyncExportsClient(self)
        self.compliance = AsyncComplianceClient(self)
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self) -> "UKGAsyncClient":
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.close()
    
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make async HTTP request with retry logic."""
        import asyncio
        
        url = self._build_url(path)
        headers = self._get_headers()
        
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{method} {url}")
                start_time = time.time()
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                )
                duration = time.time() - start_time
                logger.info(f"{method} {url} {response.status_code} ({duration:.3f}s)")
                
                if response.status_code >= 400:
                    self._handle_error(response)
                
                return response.json()
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                continue
            except RateLimitError as e:
                last_error = e
                if e.retry_after and attempt < self.max_retries - 1:
                    await asyncio.sleep(e.retry_after)
                    continue
                raise
        
        raise UKGError(f"Request failed after {self.max_retries} attempts: {last_error}")
    
    async def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)
    
    async def post(self, path: str, json: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return await self._request("POST", path, json=json)
    
    async def patch(self, path: str, json: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return await self._request("PATCH", path, json=json)
    
    async def delete(self, path: str) -> dict[str, Any]:
        return await self._request("DELETE", path)


# ============== Sub-Clients (Sync) ==============

class SessionsClient:
    """Sessions API client."""
    
    def __init__(self, client: UKGClient):
        self._client = client
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20,
    ) -> SessionsResponse:
        """List chat sessions."""
        data = self._client.get("/trace/sessions", params={
            "page": page,
            "per_page": per_page,
        })
        return SessionsResponse(**data)
    
    def create(
        self,
        title: Optional[str] = None,
        mode: str = "chat",
        constraints: Optional[dict[str, Any]] = None,
    ) -> ChatSession:
        """Create a new chat session."""
        data = self._client.post("/trace/sessions", json={
            "title": title,
            "mode": mode,
            "constraints": constraints,
        })
        return ChatSession(**data)
    
    def get(self, session_id: str) -> ChatSession:
        """Get session by ID."""
        data = self._client.get(f"/trace/sessions/{session_id}")
        return ChatSession(**data)
    
    def update(
        self,
        session_id: str,
        title: Optional[str] = None,
        mode: Optional[str] = None,
        constraints: Optional[dict[str, Any]] = None,
    ) -> ChatSession:
        """Update a session."""
        body = {}
        if title is not None:
            body["title"] = title
        if mode is not None:
            body["mode"] = mode
        if constraints is not None:
            body["constraints"] = constraints
        
        data = self._client.patch(f"/trace/sessions/{session_id}", json=body)
        return ChatSession(**data)


class RunsClient:
    """Runs API client."""
    
    def __init__(self, client: UKGClient):
        self._client = client
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
    ) -> RunsResponse:
        """List runs."""
        data = self._client.get("/trace/runs", params={
            "page": page,
            "per_page": per_page,
            "status": status,
        })
        return RunsResponse(**data)
    
    def get(self, run_id: str) -> Run:
        """Get run by ID."""
        data = self._client.get(f"/trace/runs/{run_id}")
        return Run(**data)
    
    def stages(self, run_id: str) -> list[Stage]:
        """Get stages for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/stages")
        return [Stage(**s) for s in data.get("stages", [])]
    
    def evidence(self, run_id: str) -> list[Evidence]:
        """Get evidence for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/evidence")
        return [Evidence(**e) for e in data.get("evidence", [])]
    
    def claims(self, run_id: str) -> list[Claim]:
        """Get claims for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/claims")
        return [Claim(**c) for c in data.get("claims", [])]
    
    def axes(self, run_id: str) -> AxisVector:
        """Get axis vector for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/axes")
        return AxisVector(**data.get("axes", data))
    
    def personas(self, run_id: str) -> list[Persona]:
        """Get personas for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/personas")
        return [Persona(**p) for p in data.get("personas", [])]
    
    def kas(self, run_id: str) -> list[KAInvocation]:
        """Get KA invocations for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/kas")
        return [KAInvocation(**k) for k in data.get("kas", [])]
    
    def policy(self, run_id: str) -> list[PolicyDecision]:
        """Get policy decisions for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/policy")
        return [PolicyDecision(**p) for p in data.get("policy_decisions", [])]
    
    def memory(self, run_id: str) -> list[MemoryEvent]:
        """Get memory events for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/memory")
        return [MemoryEvent(**m) for m in data.get("memory_events", [])]
    
    def metrics(self, run_id: str) -> dict[str, Any]:
        """Get metrics for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/metrics")
        return data.get("metrics", {})
    
    def spans(self, run_id: str) -> list[TraceSpan]:
        """Get trace spans for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/spans")
        return [TraceSpan(**s) for s in data.get("spans", [])]
    
    def logs(
        self,
        run_id: str,
        stage_id: Optional[str] = None,
        level: Optional[str] = None,
    ) -> list[StageLog]:
        """Get logs for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/logs", params={
            "stage_id": stage_id,
            "level": level,
        })
        return [StageLog(**log_entry) for log_entry in data.get("logs", [])]
    
    def export(self, run_id: str) -> dict[str, Any]:
        """Export a run."""
        return self._client.post(f"/trace/runs/{run_id}/export")
    
    def replay(
        self,
        run_id: str,
        same_seed: bool = True,
        from_stage: Optional[str] = None,
    ) -> dict[str, Any]:
        """Replay a run."""
        return self._client.post(f"/trace/runs/{run_id}/replay", json={
            "same_seed": same_seed,
            "from_stage": from_stage,
        })


class ExportsClient:
    """Exports API client."""
    
    def __init__(self, client: UKGClient):
        self._client = client
    
    def list(self) -> list[Export]:
        """List exports."""
        data = self._client.get("/trace/exports")
        return [Export(**e) for e in data.get("exports", [])]
    
    def get(self, export_id: str) -> Export:
        """Get export by ID."""
        data = self._client.get(f"/trace/exports/{export_id}")
        return Export(**data)
    
    def download_info(self, export_id: str) -> dict[str, Any]:
        """Get download info for an export."""
        return self._client.get(f"/trace/exports/{export_id}/download")


class ComplianceClient:
    """Compliance API client."""
    
    def __init__(self, client: UKGClient):
        self._client = client
    
    def get(
        self,
        run_id: str,
        framework: Optional[str] = None,
    ) -> ComplianceResponse:
        """Get compliance mappings for a run."""
        data = self._client.get(f"/trace/runs/{run_id}/compliance", params={
            "framework": framework,
        })
        return ComplianceResponse(**data)
    
    def add(
        self,
        run_id: str,
        framework: str,
        control_id: str,
        relevance_reason: Optional[str] = None,
        evidence_ids: Optional[list[str]] = None,
    ) -> ComplianceMapping:
        """Add a compliance mapping."""
        data = self._client.post(f"/trace/runs/{run_id}/compliance", json={
            "framework": framework,
            "control_id": control_id,
            "relevance_reason": relevance_reason,
            "evidence_ids": evidence_ids,
        })
        return ComplianceMapping(**data)


# ============== Sub-Clients (Async) ==============

class AsyncSessionsClient:
    """Async Sessions API client."""
    
    def __init__(self, client: UKGAsyncClient):
        self._client = client
    
    async def list(self, page: int = 1, per_page: int = 20) -> SessionsResponse:
        data = await self._client.get("/trace/sessions", params={"page": page, "per_page": per_page})
        return SessionsResponse(**data)
    
    async def create(
        self, title: Optional[str] = None, mode: str = "chat", constraints: Optional[dict[str, Any]] = None
    ) -> ChatSession:
        data = await self._client.post("/trace/sessions", json={"title": title, "mode": mode, "constraints": constraints})
        return ChatSession(**data)
    
    async def get(self, session_id: str) -> ChatSession:
        data = await self._client.get(f"/trace/sessions/{session_id}")
        return ChatSession(**data)
    
    async def update(
        self, session_id: str, title: Optional[str] = None, mode: Optional[str] = None, constraints: Optional[dict[str, Any]] = None
    ) -> ChatSession:
        body = {k: v for k, v in {"title": title, "mode": mode, "constraints": constraints}.items() if v is not None}
        data = await self._client.patch(f"/trace/sessions/{session_id}", json=body)
        return ChatSession(**data)


class AsyncRunsClient:
    """Async Runs API client."""
    
    def __init__(self, client: UKGAsyncClient):
        self._client = client
    
    async def list(self, page: int = 1, per_page: int = 20, status: Optional[str] = None) -> RunsResponse:
        data = await self._client.get("/trace/runs", params={"page": page, "per_page": per_page, "status": status})
        return RunsResponse(**data)
    
    async def get(self, run_id: str) -> Run:
        data = await self._client.get(f"/trace/runs/{run_id}")
        return Run(**data)
    
    async def stages(self, run_id: str) -> list[Stage]:
        data = await self._client.get(f"/trace/runs/{run_id}/stages")
        return [Stage(**s) for s in data.get("stages", [])]
    
    async def evidence(self, run_id: str) -> list[Evidence]:
        data = await self._client.get(f"/trace/runs/{run_id}/evidence")
        return [Evidence(**e) for e in data.get("evidence", [])]
    
    async def claims(self, run_id: str) -> list[Claim]:
        data = await self._client.get(f"/trace/runs/{run_id}/claims")
        return [Claim(**c) for c in data.get("claims", [])]
    
    async def axes(self, run_id: str) -> AxisVector:
        data = await self._client.get(f"/trace/runs/{run_id}/axes")
        return AxisVector(**data.get("axes", data))
    
    async def personas(self, run_id: str) -> list[Persona]:
        data = await self._client.get(f"/trace/runs/{run_id}/personas")
        return [Persona(**p) for p in data.get("personas", [])]
    
    async def kas(self, run_id: str) -> list[KAInvocation]:
        data = await self._client.get(f"/trace/runs/{run_id}/kas")
        return [KAInvocation(**k) for k in data.get("kas", [])]
    
    async def policy(self, run_id: str) -> list[PolicyDecision]:
        data = await self._client.get(f"/trace/runs/{run_id}/policy")
        return [PolicyDecision(**p) for p in data.get("policy_decisions", [])]
    
    async def memory(self, run_id: str) -> list[MemoryEvent]:
        data = await self._client.get(f"/trace/runs/{run_id}/memory")
        return [MemoryEvent(**m) for m in data.get("memory_events", [])]
    
    async def metrics(self, run_id: str) -> dict[str, Any]:
        data = await self._client.get(f"/trace/runs/{run_id}/metrics")
        return data.get("metrics", {})
    
    async def spans(self, run_id: str) -> list[TraceSpan]:
        data = await self._client.get(f"/trace/runs/{run_id}/spans")
        return [TraceSpan(**s) for s in data.get("spans", [])]
    
    async def logs(self, run_id: str, stage_id: Optional[str] = None, level: Optional[str] = None) -> list[StageLog]:
        data = await self._client.get(f"/trace/runs/{run_id}/logs", params={"stage_id": stage_id, "level": level})
        return [StageLog(**log_entry) for log_entry in data.get("logs", [])]
    
    async def export(self, run_id: str) -> dict[str, Any]:
        return await self._client.post(f"/trace/runs/{run_id}/export")
    
    async def replay(self, run_id: str, same_seed: bool = True, from_stage: Optional[str] = None) -> dict[str, Any]:
        return await self._client.post(f"/trace/runs/{run_id}/replay", json={"same_seed": same_seed, "from_stage": from_stage})


class AsyncExportsClient:
    """Async Exports API client."""
    
    def __init__(self, client: UKGAsyncClient):
        self._client = client
    
    async def list(self) -> list[Export]:
        data = await self._client.get("/trace/exports")
        return [Export(**e) for e in data.get("exports", [])]
    
    async def get(self, export_id: str) -> Export:
        data = await self._client.get(f"/trace/exports/{export_id}")
        return Export(**data)
    
    async def download_info(self, export_id: str) -> dict[str, Any]:
        return await self._client.get(f"/trace/exports/{export_id}/download")


class AsyncComplianceClient:
    """Async Compliance API client."""
    
    def __init__(self, client: UKGAsyncClient):
        self._client = client
    
    async def get(self, run_id: str, framework: Optional[str] = None) -> ComplianceResponse:
        data = await self._client.get(f"/trace/runs/{run_id}/compliance", params={"framework": framework})
        return ComplianceResponse(**data)
    
    async def add(
        self, run_id: str, framework: str, control_id: str, relevance_reason: Optional[str] = None, evidence_ids: Optional[list[str]] = None
    ) -> ComplianceMapping:
        data = await self._client.post(f"/trace/runs/{run_id}/compliance", json={
            "framework": framework, "control_id": control_id, "relevance_reason": relevance_reason, "evidence_ids": evidence_ids
        })
        return ComplianceMapping(**data)
