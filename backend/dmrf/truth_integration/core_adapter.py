"""TruthCore adapter for DMRF."""

from __future__ import annotations

from typing import Any

from backend.knowledge_algorithms.contracts import (
    KABudget,
    KAExecutionContext,
    KAExecutionMode,
)
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionStatus,
    KASelectionRequest,
)
from backend.truth_engine.truth_core.engine import TruthCoreEngine


class TruthCoreDMRFAdapter:
    """Execute the TruthCore portion selected by canonical DMRF routing."""

    def __init__(self, engine: TruthCoreEngine | None = None, *, db_session=None):
        if engine is None:
            from backend.knowledge_algorithms.ka_master_controller import (
                KAMasterController,
            )

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
        """Execute the manifest-selected L1 KA plan for the governed lifecycle.

        DMRF already owns tier selection. This adapter therefore selects only
        the production-qualified normalization, adversarial-input, and
        candidate-planning KAs whose outputs are consumed by L1/L5. It does not
        invoke the private TruthCore workflow.
        """

        controller = self.engine.ka_controller
        if controller is None or not all(
            hasattr(controller, attribute)
            for attribute in ("plan_algorithms", "execute_algorithm_plan")
        ):
            return {
                "contract_version": "truthcore-layer-plan.v1",
                "ok": False,
                "state": "failed",
                "mode": mode,
                "steps_executed": [],
                "selection_plan": {},
                "failure": {
                    "kind": "ka_controller_unavailable",
                    "code": "TRUTHCORE_KA_CONTROLLER_UNAVAILABLE",
                },
            }

        requested_ids = ["KA-004", "KA-061"]
        normalized_tier = str(tier).strip().lower()
        normalized_risk = str(
            context.get("risk_domain") or "standard"
        ).strip().lower()
        if (
            mode == "enhanced"
            or normalized_tier
            in {"high", "high_stakes", "extreme", "autonomous"}
            or normalized_risk
            not in {"", "standard", "low", "routine"}
        ):
            requested_ids.append("KA-001")
        deadline_ms = max(
            1_000,
            min(int(context.get("ka_deadline_ms") or 10_000), 30_000),
        )
        selection_request = KASelectionRequest(
            requested_ids=requested_ids,
            shared_input={
                "query": query,
                "text": query,
                "input": query,
            },
            context=KAExecutionContext(
                request_id=str(context.get("request_id") or ""),
                run_id=str(context.get("trace_id") or ""),
                session_id=context.get("session_id"),
                principal_id=context.get("principal_id"),
                workflow="governed_execution",
                tier=tier,
                layer="L1",
                policy_decisions={
                    "denied_ka_ids": list(
                        context.get("denied_ka_ids") or []
                    ),
                    "allowed_ka_ids": list(
                        context.get("allowed_ka_ids") or []
                    ),
                },
                budget=KABudget(
                    deadline_ms=deadline_ms,
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
        plan = controller.plan_algorithms(selection_request)
        plan_summary = {
            "schema_version": plan.schema_version,
            "plan_id": plan.plan_id,
            "manifest_version": plan.manifest_version,
            "request_id": plan.request_id,
            "run_id": plan.run_id,
            "mode": plan.mode.value,
            "requested_ids": requested_ids,
            "selected_ids": plan.selected_ids,
            "execution_order": plan.execution_order,
            "estimated_critical_path_ms": plan.estimated_critical_path_ms,
            "valid": plan.valid,
            "validation_errors": plan.validation_errors,
            "effects_authorized": False,
        }
        if not plan.valid:
            return {
                "contract_version": "truthcore-layer-plan.v1",
                "ok": False,
                "state": "failed",
                "mode": mode,
                "steps_executed": [],
                "selection_plan": plan_summary,
                "failure": {
                    "kind": "ka_plan_validation_failure",
                    "code": "TRUTHCORE_KA_PLAN_INVALID",
                    "validation_errors": plan.validation_errors,
                },
            }

        report = await controller.execute_algorithm_plan(
            plan,
            selection_request,
        )
        steps_executed: list[dict[str, Any]] = []
        for batch in plan.execution_order:
            for canonical_id in batch:
                result = report.results.get(canonical_id)
                if result is None:
                    continue
                steps_executed.append(
                    {
                        "step": plan.entries[canonical_id].stage,
                        "ka_id": result.canonical_id,
                        "status": (
                            "completed" if result.success else "failed"
                        ),
                        "input": dict(selection_request.shared_input),
                        "output": result.output,
                        "trace_id": result.trace_id,
                        "started_at": result.started_at.isoformat(),
                        "completed_at": result.completed_at.isoformat(),
                        "duration_ms": result.duration_ms,
                        "outcome_type": result.outcome_type.value,
                        "error": (
                            result.error.message if result.error else None
                        ),
                    }
                )
        ok = (
            report.status == KAPlanExecutionStatus.SUCCEEDED
            and len(steps_executed) == len(plan.selected_ids)
            and all(
                item["status"] == "completed"
                for item in steps_executed
            )
        )
        return {
            "contract_version": "truthcore-layer-plan.v1",
            "ok": ok,
            "state": "completed" if ok else "failed",
            "mode": mode,
            "input_contract": {
                "query": query,
                "tier": tier,
                "axis17_context": axis17_context,
                "context_keys": sorted(context),
            },
            "steps_executed": steps_executed,
            "selection_plan": plan_summary,
            "execution_report": {
                "schema_version": report.schema_version,
                "status": report.status.value,
                "duration_ms": report.duration_ms,
                "required_failure": report.required_failure,
                "traces": {
                    canonical_id: {
                        "parent_ids": list(trace.parent_ids),
                        "events": [
                            event.model_dump(mode="json", exclude_none=True)
                            for event in trace.events
                        ],
                    }
                    for canonical_id, trace in sorted(report.traces.items())
                    if canonical_id in plan.selected_ids
                },
            },
            "failure": (
                None
                if ok
                else {
                    "kind": "ka_execution_failure",
                    "code": "TRUTHCORE_KA_PLAN_FAILURE",
                    "required_failure": report.required_failure,
                }
            ),
        }
