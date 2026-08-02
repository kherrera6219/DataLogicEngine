"""
backend/dmrf/orchestrator.py — DMRF control-plane orchestrator.

Routes incoming requests through the Dynamic Multi-Route Framework (DMRF):
selects the appropriate processing chain (truth engine, simulation, DSQP, etc.)
based on query classification scores.

DISTINCT FROM core/simulation/orchestrator.py, which orchestrates the three
in-memory simulation layers (FROST, graph, memory). The two handle completely
different domains; the filename overlap is coincidental.
"""

from __future__ import annotations

import os
from typing import Any

from backend.dsqp.dsqp_orchestrator import DSQPOrchestrator
from backend.knowledge_algorithms.contracts import (
    KABudget,
    KAExecutionContext,
    KAExecutionMode,
)
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionStatus,
    KASelectionRequest,
)

from .desktop_config import DMRFDesktopConfig
from .frost_bridge import FROSTBridge
from .injection_defense import InjectionDefense
from .mlflow_tracker import DMRFMLflowTracker
from .models import DMRFResult, DMRFStep, TIER_ORDER, TierClassification
from .observability import DMRFObservability
from .router import DMRFRouter
from .tier_classifier import DMRFTierClassifier
from .truth_integration.gate_adapter import TruthGateDMRFAdapter
from .truth_integration.link_adapter import TruthLinkDMRFAdapter
from .truth_integration.memory_adapter import TruthMemoryDMRFAdapter


class DMRFOrchestrator:
    """Phase F DMRF control plane wrapping TruthCore inputs and telemetry."""

    _observability = DMRFObservability()

    def __init__(
        self,
        *,
        desktop_mode: bool | None = None,
        db_session=None,
        router: DMRFRouter | None = None,
        classifier: DMRFTierClassifier | None = None,
        frost_bridge: FROSTBridge | None = None,
        dsqp: DSQPOrchestrator | None = None,
        config: dict[str, Any] | None = None,
        ka_controller: Any | None = None,
    ):
        self.desktop_mode = self._desktop_mode() if desktop_mode is None else desktop_mode
        self.db_session = db_session
        # Operator-tunable DMRF settings (dmrf_config.json under AppData); the
        # loader returns deterministic defaults when no file is present.
        self.config = config if config is not None else DMRFDesktopConfig().load()
        self.max_refinement_iterations = int(self.config.get("max_refinement_iterations", 3) or 3)
        self.router = router or DMRFRouter()
        self.classifier = classifier or DMRFTierClassifier(
            desktop_mode=self.desktop_mode,
            offline_tier_cap=str(self.config.get("offline_tier_cap", "high_stakes")),
        )
        self.injection_defense = InjectionDefense()
        self.gate = TruthGateDMRFAdapter()
        self.link = TruthLinkDMRFAdapter(desktop_mode=self.desktop_mode)
        self.memory = TruthMemoryDMRFAdapter(db_session=db_session)
        self.tracker = DMRFMLflowTracker()
        self.frost_bridge = frost_bridge or FROSTBridge()
        self.dsqp = dsqp or DSQPOrchestrator(timeout_seconds=30)
        self.ka_controller = ka_controller

    async def process(
        self,
        query: str,
        *,
        context: dict[str, Any] | None = None,
        offline: bool = False,
    ) -> DMRFResult:
        context = context or {}
        result = DMRFResult(query=query)

        defense = self.injection_defense.detect(query)
        self._record_step(result, "injection_defense", {"defense": defense})
        if not defense["safe"]:
            result.ok = False
            result.warnings.append(f"blocked:{defense['category']}")
            return result

        gate_result = self.gate.evaluate(query, context)
        result.gate_result = gate_result
        self._record_step(result, "truth_gate", {"gate": gate_result})
        if not gate_result.get("passed", False):
            result.ok = False
            result.warnings.append(str(gate_result.get("block_reason", "truth_gate_block")))
            return result

        tier = self.classifier.classify(query, context=context, offline=offline)
        if self.ka_controller is not None:
            tier = await self._apply_canonical_complexity_routing(
                result,
                query=query,
                context=context,
                offline=offline,
                heuristic=tier,
            )
            if tier is None:
                result.ok = False
                result.warnings.append("ka_complexity_routing_failed")
                return result
        result.tier = tier.tier
        self._record_step(result, "tier_classifier", {"classification": tier.to_dict()})

        axis_vector = self.router.route(query, tier=tier.tier, context=context)
        result.axis_vector = axis_vector
        self._record_step(result, "axis_router", {"axis_vector": axis_vector.to_dict()})

        # The canonical orchestrator retrieves source-identified context before
        # constructing personas. Standalone DMRF callers retain the deterministic
        # compatibility behavior, while the product path defers this stage.
        if not context.get("_canonical_defer_dsqp"):
            dsqp_result = await self.dsqp.construct_all(
                query,
                axis_vector=axis_vector.to_dict(),
                context={
                    **context,
                    "risk_domain": axis_vector.axes["15"]["value"],
                    "coordinate_path": f"dmrf.{axis_vector.axes['1']['value']}.{axis_vector.axes['2']['value']}",
                },
            )
            result.dsqp_chain = dsqp_result
            self._record_step(result, "dsqp_personas", {"dsqp_chain": dsqp_result})

        if self.db_session is not None:
            try:
                self.memory.persist(result, session_id=context.get("truth_session_id"))
            except Exception as exc:
                result.warnings.append(f"dmrf_memory_persist_failed:{type(exc).__name__}")

        tracking = self.tracker.record(result)
        self._record_step(result, "mlflow_tracking", {"tracking": tracking})

        link_result = self.link.publish("routed", result.export_bundle())
        self._record_step(result, "truthlink_publish", {"truthlink": link_result})
        self._observability.record(
            tier=result.tier,
            frost_depth=axis_vector.frost_layer_depth,
            run_id=result.run_id,
        )
        return result

    async def _apply_canonical_complexity_routing(
        self,
        result: DMRFResult,
        *,
        query: str,
        context: dict[str, Any],
        offline: bool,
        heuristic: TierClassification,
    ) -> TierClassification | None:
        """Run the production-admitted KA-113 plan and merge it fail closed."""
        request = KASelectionRequest(
            requested_ids=["KA-005", "KA-113"],
            shared_input={"query": query},
            context=KAExecutionContext(
                request_id=str(context.get("request_id") or result.run_id),
                run_id=result.run_id,
                session_id=context.get("session_id"),
                principal_id=context.get("principal_id"),
                workflow="governed_dmrf_routing",
                tier=heuristic.tier,
                layer="L1",
                budget=KABudget(
                    deadline_ms=5_000,
                    max_selected_algorithms=8,
                    max_dependency_executions=8,
                    max_recursion_depth=4,
                    max_fan_out=8,
                    max_parallelism=2,
                    max_provider_calls=0,
                    max_effects=0,
                ),
            ),
            mode=KAExecutionMode.PRODUCTION,
        )
        plan = self.ka_controller.plan_algorithms(request)
        if not plan.valid:
            self._record_step(
                result,
                "ka_complexity_router",
                {
                    "status": "failed",
                    "selected_ids": list(plan.selected_ids),
                    "validation_errors": list(plan.validation_errors),
                },
            )
            return None

        report = await self.ka_controller.execute_algorithm_plan(plan, request)
        traces = {
            canonical_id: {
                "parent_ids": list(trace.parent_ids),
                "events": [
                    event.model_dump(mode="json", exclude_none=True)
                    for event in trace.events
                ],
            }
            for canonical_id, trace in sorted(report.traces.items())
            if canonical_id in plan.selected_ids
        }
        outputs = {
            canonical_id: execution.output
            for canonical_id, execution in report.results.items()
            if execution.success
        }
        self._record_step(
            result,
            "ka_complexity_router",
            {
                "status": report.status.value,
                "plan_id": plan.plan_id,
                "selected_ids": list(plan.selected_ids),
                "execution_order": list(plan.execution_order),
                "required_failure": report.required_failure,
                "outputs": outputs,
                "traces": traces,
            },
        )
        ka_output = outputs.get("KA-113")
        if (
            report.status != KAPlanExecutionStatus.SUCCEEDED
            or not isinstance(ka_output, dict)
        ):
            return None

        routed_tier = {
            "low": "trivial",
            "medium": "moderate",
            "high": "high_stakes",
        }.get(str(ka_output.get("complexity_tier") or "").lower())
        if routed_tier is None:
            return None

        merged_tier = max(
            (heuristic.tier, routed_tier),
            key=lambda value: TIER_ORDER[value],
        )
        capped_from = heuristic.capped_from
        if (
            self.desktop_mode
            and offline
            and TIER_ORDER[merged_tier]
            > TIER_ORDER[self.classifier.offline_tier_cap]
        ):
            capped_from = merged_tier
            merged_tier = self.classifier.offline_tier_cap
        return TierClassification(
            tier=merged_tier,
            confidence=max(
                float(heuristic.confidence),
                float(ka_output.get("complexity_score") or 0),
            ),
            rationale=[
                *heuristic.rationale,
                f"ka_113_complexity={ka_output['complexity_tier']}",
                "ka_113_may_raise_but_never_lower_tier",
            ],
            raw={
                **dict(heuristic.raw),
                "heuristic_tier": heuristic.tier,
                "ka_113": ka_output,
            },
            capped_from=capped_from,
        )

    @classmethod
    def status(cls) -> dict[str, Any]:
        return cls._observability.status()

    @classmethod
    def prometheus_lines(cls, prefix: str = "datalogicengine") -> list[str]:
        return cls._observability.prometheus_lines(prefix=prefix)

    def _record_step(self, result: DMRFResult, name: str, outputs: dict[str, Any]) -> None:
        step = DMRFStep(name=name, outputs=outputs)
        snapshot = self.frost_bridge.snapshot_step(
            name,
            {"run_id": result.run_id, "step": name, "outputs": outputs},
        )
        step.snapshot_id = snapshot["snapshot_id"]
        if not snapshot["verified"]:
            step.status = "snapshot_failed"
            result.warnings.append(f"snapshot_failed:{name}")
        step.complete()
        result.add_step(step)

    @staticmethod
    def _desktop_mode() -> bool:
        return os.environ.get("IS_DESKTOP_APP", "false").lower() in {"1", "true", "yes", "on"}
