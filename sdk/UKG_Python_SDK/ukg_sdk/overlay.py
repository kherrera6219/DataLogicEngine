"""Thin async client for the installed governed execution boundary.

The pre-Phase-5 SDK overlay owned a second KA/DSQP/provider pipeline. That made
SDK results materially different from built-in chat and allowed the SDK to
bypass the backend's policy, retrieval, trace, and persistence lifecycle. The
public name is retained for source compatibility, but it now calls the one
backend-owned `/api/v1/gateway/chat` contract.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import os

import httpx


class UKGOverlay:
    """Compatibility facade over the canonical DataLogicEngine gateway."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_s: float = 120.0,
        verify_tls: bool = True,
        client: httpx.AsyncClient | None = None,
        # Accepted only so older construction code fails at execution with a
        # useful migration path instead of a Python signature error. Direct
        # provider ownership is intentionally ignored.
        provider: Any | None = None,
        model: str | None = None,
        **_: Any,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get("DATALOGICENGINE_API_URL")
            or "http://127.0.0.1:5000/api/v1"
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("DATALOGICENGINE_API_KEY")
        self.timeout_s = timeout_s
        self.verify_tls = verify_tls
        self._client = client
        self._owns_client = client is None
        self._legacy_provider_supplied = provider is not None
        self.default_model = model

    async def run(
        self,
        *,
        query: str,
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        tier_override: Optional[str] = None,
        mode: str = "standard",
        provider: str | None = None,
        model: str | None = None,
    ) -> Dict[str, Any]:
        """Execute through the installed backend and return the compatibility shape."""

        if not str(query or "").strip():
            raise ValueError("query is required")
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "messages": [{"role": "user", "content": query}],
            "mode": mode,
            "provider": provider,
            "model": model or self.default_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "session_id": session_id,
            "meta": {
                **(meta or {}),
                "source": "python_sdk",
                "sdk_user_id": user_id,
                "correlation_id": correlation_id,
                "tier_override": tier_override,
                "legacy_provider_argument_ignored": self._legacy_provider_supplied,
            },
        }
        client = self._client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_s,
            verify=self.verify_tls,
        )
        try:
            response = await client.post("/gateway/chat", json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
        finally:
            if self._owns_client:
                await client.aclose()

        data = body.get("data") if isinstance(body, dict) and isinstance(body.get("data"), dict) else body
        if not isinstance(data, dict):
            raise RuntimeError("Governed gateway returned an invalid response")
        return {
            "ok": True,
            "answer": data.get("response", ""),
            "run_id": data.get("run_id"),
            "trace_id": data.get("run_id"),
            "contract_version": data.get("contract_version", "governed.v1"),
            "status": data.get("status", "completed"),
            "provider_used": data.get("provider_used"),
            "model_used": data.get("model_used"),
            "usage": data.get("usage", {}),
            "coordinate": data.get("coordinates"),
            "confidence": data.get("confidence_score"),
            "claims": data.get("claims", []),
            "evidence_count": data.get("evidence_count", 0),
            "trace": (data.get("trace_summary") or {}).get("steps", [])
            if isinstance(data.get("trace_summary"), dict)
            else [],
            "warnings": data.get("warnings", []),
        }
