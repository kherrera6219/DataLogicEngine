"""Compatibility client for the backend-owned governed execution path.

Before SDK 0.6 this module assembled a second TruthGate/TruthCore/KA pipeline in
the client process.  Direct imports are retained for source compatibility, but
execution now crosses the installed DataLogicEngine service boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..api_client import UKGClient


@dataclass
class TruthEngineConfig:
    """Connection and governed-mode settings for the compatibility client."""

    base_url: str = "http://localhost:5000/api/v1"
    api_key: Optional[str] = None
    timeout: float = 120.0
    mode: str = "standard"
    provider: Optional[str] = None
    model: Optional[str] = None
    specs: dict[str, Any] = field(default_factory=dict)


@dataclass
class TruthResult:
    """Measured result returned by the canonical governed gateway."""

    ok: bool
    verdict: str
    answer: str = ""
    confidence: Optional[float] = None
    run_id: Optional[str] = None
    contract_version: Optional[str] = None
    failure: Optional[dict[str, Any]] = None
    raw: dict[str, Any] = field(default_factory=dict)


class TruthEngine:
    """Deprecated name for a thin client to ``/api/v1/gateway/chat``.

    The class owns no TruthGate, KA, DSQP, retrieval, provider, validation, or
    persistence logic.  Those responsibilities belong to the backend canonical
    orchestrator so SDK and desktop callers receive the same governed result.
    """

    def __init__(
        self,
        config: Optional[TruthEngineConfig] = None,
        *,
        client: Optional[UKGClient] = None,
        **legacy_execution_components: Any,
    ) -> None:
        if legacy_execution_components:
            names = ", ".join(sorted(legacy_execution_components))
            raise TypeError(
                "Client-side TruthEngine components were removed in SDK 0.6; "
                f"configure the installed service instead (received: {names})"
            )
        self.config = config or TruthEngineConfig()
        self._client = client or UKGClient(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout,
        )
        self._owns_client = client is None

    def evaluate(
        self,
        claim: str,
        context: Optional[dict[str, Any]] = None,
        *,
        mode: Optional[str] = None,
    ) -> TruthResult:
        """Evaluate a claim through the canonical installed service."""

        if not str(claim or "").strip():
            raise ValueError("claim is required")
        body = self._client.post(
            "/gateway/chat",
            json={
                "messages": [{"role": "user", "content": claim}],
                "mode": mode or self.config.mode,
                "provider": self.config.provider,
                "model": self.config.model,
                "meta": {"source": "python_sdk_truth_engine", **(context or {})},
            },
        )
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        status = str(data.get("status") or "unavailable")
        failure = data.get("failure") if isinstance(data.get("failure"), dict) else None
        return TruthResult(
            ok=status == "completed" and failure is None,
            verdict=status,
            answer=str(data.get("response") or ""),
            confidence=data.get("confidence_score"),
            run_id=data.get("run_id"),
            contract_version=data.get("contract_version"),
            failure=failure,
            raw=data,
        )

    def summarize(self) -> dict[str, Any]:
        """Return non-secret client configuration for compatibility diagnostics."""

        return {
            "execution_owner": "installed_backend",
            "contract": "governed.v1",
            "base_url": self.config.base_url,
            "mode": self.config.mode,
            "provider": self.config.provider,
            "model": self.config.model,
            "spec_count": len(self.config.specs),
        }

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @classmethod
    def load_default(cls) -> "TruthEngine":
        return cls()
