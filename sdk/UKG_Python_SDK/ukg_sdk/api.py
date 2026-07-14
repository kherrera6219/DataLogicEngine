"""Legacy API name backed by the canonical DataLogicEngine service."""

from __future__ import annotations

from typing import Any, Optional

from .api_client import UKGClient
from .truth_engine.core import TruthEngine, TruthEngineConfig


class TruthEngineAPI:
    """Source-compatible facade with no client-side orchestration."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:5000/api/v1",
        api_key: Optional[str] = None,
        timeout: float = 120.0,
        client: Optional[UKGClient] = None,
        memory_adapter: Optional[str] = None,
        ka_registry_path: Optional[str] = None,
    ) -> None:
        if memory_adapter is not None or ka_registry_path is not None:
            raise TypeError(
                "Client-side memory and KA execution were removed in SDK 0.6; "
                "configure them on the installed DataLogicEngine service"
            )
        self._engine = TruthEngine(
            TruthEngineConfig(base_url=base_url, api_key=api_key, timeout=timeout),
            client=client,
        )

    def query(
        self,
        query: str,
        *,
        context: Optional[dict[str, Any]] = None,
        tier: Optional[str] = None,
        mode: str = "standard",
    ) -> dict[str, Any]:
        """Return the governed gateway response payload."""

        result = self._engine.evaluate(
            query,
            {**(context or {}), "legacy_tier_hint": tier},
            mode=mode,
        )
        return result.raw

    def close(self) -> None:
        self._engine.close()
