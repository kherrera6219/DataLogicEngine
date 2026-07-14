"""TruthCore adapter for DMRF."""

from __future__ import annotations

from typing import Any

from backend.truth_engine.truth_core.engine import TruthCoreEngine


class TruthCoreDMRFAdapter:
    """Execute the TruthCore portion selected by canonical DMRF routing."""

    def __init__(self, engine: TruthCoreEngine | None = None, *, db_session=None):
        if engine is None:
            from backend.knowledge_algorithms.ka_master_controller import KAMasterController

            controller = KAMasterController({"llm_gateway": None})
            engine = TruthCoreEngine(db_session=db_session, ka_controller=controller)
        self.engine = engine

    def workflow_steps(self, tier: str, axis17_context: dict[str, Any]) -> list[str]:
        return self.engine.get_workflow_steps(tier, axis17_context=axis17_context)

    async def execute(
        self,
        query: str,
        *,
        tier: str,
        axis17_context: dict[str, Any],
        context: dict[str, Any],
        mode: str,
    ) -> dict[str, Any]:
        return await self.engine.execute_governed_preflight(
            query,
            {
                **context,
                "dmrf_tier": tier,
                "axis17_context": axis17_context,
            },
            mode=mode,
        )
