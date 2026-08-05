"""TruthCore L1-L5 owner for bounded context-dependency preparation."""

from __future__ import annotations

from typing import Any

from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleCoordinator,
    KnowledgeLifecycleError,
)

BATCH_13_IDS = (
    "KA-003",
    "KA-011",
    "KA-015",
    "KA-017",
    "KA-025",
    "KA-040",
)


class TruthCoreContextDependencyError(RuntimeError):
    """Raised when the required TruthCore context plan cannot complete."""


class TruthCoreContextDependencyService:
    """Execute the exact pure Batch 13 context bundle through its owner registry."""

    def __init__(
        self,
        *,
        coordinator: KnowledgeLifecycleCoordinator | None = None,
    ) -> None:
        self.coordinator = coordinator or KnowledgeLifecycleCoordinator(
            workflow_phase="cp19k"
        )

    def prepare(
        self,
        *,
        ka_inputs: dict[str, dict[str, Any]],
        request_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        if set(ka_inputs) != set(BATCH_13_IDS):
            raise TruthCoreContextDependencyError(
                "TruthCore context preparation requires the exact Batch 13 inputs"
            )
        try:
            execution = self.coordinator.execute_operation_sync(
                owner="truthcore_l1_l5",
                operation="context_dependencies",
                requested_ids=list(BATCH_13_IDS),
                ka_inputs=ka_inputs,
                request_id=request_id,
                run_id=f"truthcore-context:{request_id}",
                max_effects=0,
                session_id=request_id,
                principal_id=principal_id,
                tier="context_preparation",
                layer="L1-L5",
                service_capabilities={"truthcore_context_service"},
                required=True,
            )
        except KnowledgeLifecycleError as exc:
            raise TruthCoreContextDependencyError(str(exc)) from exc
        if set(execution.executed_ids) != set(BATCH_13_IDS):
            raise TruthCoreContextDependencyError(
                "TruthCore context preparation did not execute the exact Batch 13 set"
            )
        outputs = {
            canonical_id: dict(result.get("output") or {})
            for canonical_id, result in execution.results.items()
        }
        return {
            "schema_version": "dle.truthcore-context-dependencies.v1",
            "status": "prepared",
            "owner": execution.owner,
            "operation": execution.operation,
            "plan_id": execution.plan.plan_id,
            "manifest_version": execution.plan.manifest_version,
            "selected_ids": list(execution.plan.selected_ids),
            "executed_ids": list(execution.executed_ids),
            "execution_order": list(execution.plan.execution_order),
            "outputs": outputs,
            "traces": {
                canonical_id: {
                    "parent_ids": list(trace.parent_ids),
                    "events": [
                        event.model_dump(mode="json", exclude_none=True)
                        for event in trace.events
                    ],
                }
                for canonical_id, trace in execution.report.traces.items()
                if canonical_id in BATCH_13_IDS
            },
            "external_effects_applied": 0,
            "persistence_applied": False,
            "provider_calls": 0,
        }
