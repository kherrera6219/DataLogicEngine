"""TruthGate adapter for DMRF."""

from __future__ import annotations

from typing import Any

from backend.truth_engine.truth_gate.gateway import TruthGateGateway


class TruthGateDMRFAdapter:
    """Run the existing TruthGate gateway as the DMRF entry gate."""

    def __init__(self, gateway: TruthGateGateway | None = None):
        self.gateway = gateway or TruthGateGateway()

    def evaluate(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        return self.gateway.evaluate(
            {
                "query": query,
                "tenant_id": context.get("tenant_id", "default"),
                "user_context": context.get("user_context", {}),
                "budget_limit": context.get("budget_limit", 100.0),
            }
        )

