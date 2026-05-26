"""TruthCore adapter for DMRF."""

from __future__ import annotations

from typing import Any

from backend.truth_engine.truth_core.engine import TruthCoreEngine


class TruthCoreDMRFAdapter:
    """Map DMRF tier and Axis 17 routing to TruthCore workflow steps."""

    def __init__(self, engine: TruthCoreEngine | None = None):
        self.engine = engine or TruthCoreEngine()

    def workflow_steps(self, tier: str, axis17_context: dict[str, Any]) -> list[str]:
        return self.engine.get_workflow_steps(tier, axis17_context=axis17_context)

