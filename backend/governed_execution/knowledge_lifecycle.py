"""Canonical KA ownership for governed truth, data, and knowledge lifecycles.

This module is deliberately a subsystem adapter, not a second product
orchestrator.  It reads the manifest-owned CP19-H registry and dispatches every
applicable operation through ``ManifestKASelector`` and ``KAPlanExecutor``.
Authoritative services remain the only owners of persistence and other effects.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.knowledge_algorithms.contracts import (
    KABudget,
    KAExecutionContext,
    KAExecutionMode,
)
from backend.knowledge_algorithms.controller import (
    CanonicalKAController,
    get_ka_controller,
)
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionReport,
    KAPlanExecutionStatus,
    KAPlanExecutor,
    KASelectionPlan,
    KASelectionRequest,
    KATraceState,
    ManifestKASelector,
)


class KnowledgeLifecycleError(RuntimeError):
    """Raised when a required canonical owner path cannot commit."""


@dataclass(slots=True)
class KnowledgeLifecycleExecution:
    owner: str
    operation: str
    plan: KASelectionPlan
    report: KAPlanExecutionReport
    executed_ids: list[str]
    results: dict[str, dict[str, Any]]

    @property
    def ok(self) -> bool:
        return self.report.status is KAPlanExecutionStatus.SUCCEEDED

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "dle.knowledge-lifecycle-execution.v1",
            "owner": self.owner,
            "operation": self.operation,
            "plan_id": self.plan.plan_id,
            "manifest_version": self.plan.manifest_version,
            "status": self.report.status.value,
            "selected_ids": list(self.plan.selected_ids),
            "executed_ids": list(self.executed_ids),
            "execution_order": list(self.plan.execution_order),
            "required_failure": self.report.required_failure,
            "results": dict(self.results),
        }


@dataclass(slots=True)
class StagedMemoryWrite:
    content: str
    session_id: str
    source_run_id: str
    source_ids: list[str]
    owner_user_id: int | None = None
    principal_id: str | None = None
    tenant_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    state: str = "staged"
    applied: bool = False
    receipt: dict[str, Any] | None = None
    checkpoint_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "dle.staged-memory-write.v1",
            "content": self.content,
            "session_id": self.session_id,
            "source_run_id": self.source_run_id,
            "source_ids": list(self.source_ids),
            "owner_user_id": self.owner_user_id,
            "principal_id": self.principal_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "state": self.state,
            "applied": self.applied,
            "receipt": self.receipt,
            "checkpoint_id": self.checkpoint_id,
        }


class KnowledgeLifecycleCoordinator:
    """Manifest-governed adapter for CP19-H subsystem owner operations."""

    def __init__(
        self,
        *,
        ka_controller: CanonicalKAController | None = None,
        memory_service: Any | None = None,
        registry_key: str = "subsystem_execution_registry",
        workflow_phase: str = "cp19h",
    ) -> None:
        self.ka_controller = ka_controller or get_ka_controller()
        self.ka_selector = ManifestKASelector(self.ka_controller.manifest)
        self.ka_executor = KAPlanExecutor(self.ka_controller)
        registry = self.ka_controller.manifest.authority.get(registry_key)
        if not isinstance(registry, dict):
            raise KnowledgeLifecycleError(
                f"Subsystem execution registry is unavailable: {registry_key}"
            )
        owners = registry.get("owners")
        if not isinstance(owners, dict):
            raise KnowledgeLifecycleError("CP19-H subsystem owner registry is invalid")
        self.registry = registry
        self.owners = owners
        self._memory_service = memory_service
        self._workflow_phase = str(workflow_phase)

    def operation_ids(self, owner: str, operation: str) -> list[str]:
        owner_registry = self.owners.get(owner)
        if not isinstance(owner_registry, dict):
            raise KnowledgeLifecycleError(f"Unknown lifecycle owner: {owner}")
        canonical_ids = owner_registry.get(operation)
        if not isinstance(canonical_ids, list) or not canonical_ids:
            raise KnowledgeLifecycleError(
                f"Unknown lifecycle operation: {owner}.{operation}"
            )
        return [str(value) for value in canonical_ids]

    async def execute_operation(
        self,
        *,
        owner: str,
        operation: str,
        requested_ids: list[str] | None,
        ka_inputs: dict[str, dict[str, Any]],
        request_id: str,
        run_id: str,
        max_effects: int,
        session_id: str | None = None,
        principal_id: str | None = None,
        tier: str | None = None,
        layer: str | None = None,
        prior_results: dict[str, Any] | None = None,
        service_capabilities: set[str] | None = None,
        policy_decisions: dict[str, Any] | None = None,
        deadline_ms: int = 20_000,
        required: bool = True,
    ) -> KnowledgeLifecycleExecution:
        authorized = self.operation_ids(owner, operation)
        selected = list(requested_ids or authorized)
        unauthorized = sorted(set(selected) - set(authorized))
        if unauthorized:
            raise KnowledgeLifecycleError(
                f"{owner}.{operation} does not own: {','.join(unauthorized)}"
            )
        request = KASelectionRequest(
            requested_ids=selected,
            ka_inputs=ka_inputs,
            prior_results=dict(prior_results or {}),
            service_capabilities=set(service_capabilities or set()),
            mode=KAExecutionMode.PRODUCTION,
            context=KAExecutionContext(
                request_id=request_id,
                run_id=run_id,
                session_id=session_id,
                principal_id=principal_id,
                workflow=(f"governed.{self._workflow_phase}.{owner}.{operation}"),
                tier=tier,
                layer=layer,
                policy_decisions=dict(policy_decisions or {}),
                budget=KABudget(
                    deadline_ms=max(1, min(int(deadline_ms), 60_000)),
                    max_dependency_executions=32,
                    max_recursion_depth=12,
                    max_selected_algorithms=48,
                    max_fan_out=16,
                    max_parallelism=4,
                    max_input_bytes=2_000_000,
                    max_output_bytes=10_000_000,
                    max_effects=max(0, min(int(max_effects), 1_000)),
                ),
            ),
        )
        plan = self.ka_selector.plan(request)
        if not plan.valid:
            raise KnowledgeLifecycleError(
                "; ".join(plan.validation_errors)
                or f"{owner}.{operation} produced an invalid KA plan"
            )
        report = await self.ka_executor.execute(plan, request)
        executed_ids = sorted(
            canonical_id
            for canonical_id, trace in report.traces.items()
            if any(event.state is KATraceState.EXECUTED for event in trace.events)
        )
        results = {
            canonical_id: report.results[canonical_id].model_dump(
                mode="json",
                exclude_none=True,
            )
            for canonical_id in executed_ids
            if canonical_id in report.results
        }
        execution = KnowledgeLifecycleExecution(
            owner=owner,
            operation=operation,
            plan=plan,
            report=report,
            executed_ids=executed_ids,
            results=results,
        )
        if required and not execution.ok:
            raise KnowledgeLifecycleError(
                f"{owner}.{operation} failed at "
                f"{report.required_failure or report.status.value}"
            )
        return execution

    def execute_operation_sync(
        self,
        **kwargs: Any,
    ) -> KnowledgeLifecycleExecution:
        """Run one owner operation from a synchronous authoritative service."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.execute_operation(**kwargs))
        raise KnowledgeLifecycleError(
            "synchronous lifecycle dispatch cannot run inside an active event loop"
        )

    def recall_authorized(
        self,
        query: str,
        *,
        session_id: str | None,
        owner_user_id: int | None,
        principal_id: str | None,
        tenant_id: str | None,
        limit: int,
    ) -> list[Any]:
        return self._memory().recall(
            query,
            context={
                "session_id": session_id,
                "owner_user_id": owner_user_id,
                "principal_id": principal_id,
                "tenant_id": tenant_id,
            },
            limit=limit,
        )

    @staticmethod
    def stage_validated_memory(
        *,
        content: str,
        session_id: str,
        source_run_id: str,
        source_ids: list[str],
        owner_user_id: int | None,
        principal_id: str | None,
        tenant_id: str | None,
    ) -> StagedMemoryWrite:
        return StagedMemoryWrite(
            content=str(content),
            session_id=str(session_id),
            source_run_id=str(source_run_id),
            source_ids=sorted({str(value) for value in source_ids if value}),
            owner_user_id=owner_user_id,
            principal_id=principal_id,
            tenant_id=tenant_id,
        )

    def commit_validated_memory(
        self,
        proposal: StagedMemoryWrite,
    ) -> StagedMemoryWrite:
        if proposal.state != "staged" or proposal.applied:
            raise KnowledgeLifecycleError("memory proposal is not staged")
        service = self._memory()
        checkpoint_id = f"cp19h:{proposal.source_run_id}"
        service.checkpoint(checkpoint_id)
        proposal.checkpoint_id = checkpoint_id
        try:
            vertex = service.consolidate(
                proposal.content,
                layer="L10",
                persona="global",
                metadata={
                    "session_id": proposal.session_id,
                    "source_ids": list(proposal.source_ids),
                    "owner_user_id": proposal.owner_user_id,
                    "principal_id": proposal.principal_id,
                    "tenant_id": proposal.tenant_id,
                    "quarantined": False,
                    "lifecycle_state": "validated",
                },
                importance=1.2,
                trusted=True,
                source_run_id=proposal.source_run_id,
                policy_result="release_authorized",
                retention_class="validated_reasoning_memory",
            )
        except Exception:
            service.restore(checkpoint_id)
            raise
        proposal.state = "committed"
        proposal.applied = True
        proposal.receipt = {
            "service": "UnifiedMemoryService",
            "vertex_id": vertex.vertex_id,
            "validation_state": vertex.metadata.get("validation_state"),
            "retention_class": vertex.metadata.get("retention_class"),
            "source_run_id": vertex.metadata.get("source_run_id"),
        }
        return proposal

    def rollback_validated_memory(
        self,
        proposal: StagedMemoryWrite | None,
    ) -> bool:
        if proposal is None or not proposal.checkpoint_id:
            return False
        restored = bool(self._memory().restore(proposal.checkpoint_id))
        if restored:
            proposal.state = "rolled_back"
            proposal.applied = False
            proposal.receipt = {
                "service": "UnifiedMemoryService",
                "status": "rolled_back",
                "checkpoint_id": proposal.checkpoint_id,
            }
        return restored

    def _memory(self) -> Any:
        if self._memory_service is None:
            from backend.memory import get_unified_memory_service

            self._memory_service = get_unified_memory_service()
        return self._memory_service

    @property
    def memory_service(self) -> Any:
        """Return the authoritative memory service used by this coordinator."""
        return self._memory()


class LifecycleTransitionPublisher:
    """Publish and snapshot real governed stage and KA transitions."""

    def __init__(
        self,
        *,
        truth_link: Any | None = None,
        frost: Any | None = None,
    ) -> None:
        if truth_link is None:
            from backend.truth_engine.truth_link.bus import TruthLinkBus

            truth_link = TruthLinkBus(enable_redis_streams=False)
        if frost is None:
            from core.system.frost_service import FROSTService

            frost = FROSTService(persist_objects=False)
        self.truth_link = truth_link
        self.frost = frost
        self._last_terminal_stage: dict[str, str] = {}
        self._stage_parents: dict[tuple[str, str], str | None] = {}

    def publish_stage(self, trace_id: str, stage: Any) -> dict[str, Any]:
        key = (trace_id, stage.stage_id)
        parent_id = self._stage_parents.setdefault(
            key,
            self._last_terminal_stage.get(trace_id),
        )
        payload = {
            "schema_version": "dle.lifecycle-transition.v1",
            "trace_id": trace_id,
            "transition_kind": "stage",
            "stage_id": stage.stage_id,
            "parent_stage_id": parent_id,
            "stage_name": stage.name,
            "stage_type": stage.stage_type,
            "status": stage.status.value,
            "selected_ka_ids": list(stage.outputs.get("selected_ka_ids") or []),
            "error_code": stage.error_code,
        }
        snapshot_id = self.frost.snapshot(
            payload,
            metadata={
                "run_id": trace_id,
                "stage_id": stage.stage_id,
                "parent_stage_id": parent_id,
                "transition_kind": "stage",
            },
        )
        if not self.frost.verify_snapshot(snapshot_id):
            raise KnowledgeLifecycleError("FROST stage snapshot verification failed")
        try:
            message = self.truth_link.publish(
                "truth_core",
                "stage_transition",
                {**payload, "snapshot_id": snapshot_id},
                session_id=trace_id,
            )
        except Exception as exc:
            raise KnowledgeLifecycleError("TruthLink stage publication failed") from exc
        if not isinstance(message, dict) or not message.get("message_id"):
            raise KnowledgeLifecycleError("TruthLink stage publication failed")
        if stage.status.value != "running":
            self._last_terminal_stage[trace_id] = stage.stage_id
        return {
            "message_id": message["message_id"],
            "snapshot_id": snapshot_id,
            "parent_stage_id": parent_id,
        }

    def publish_ka_results(self, trace_id: str, stage: Any) -> list[dict[str, Any]]:
        raw_results = stage.outputs.get("ka_results")
        if not isinstance(raw_results, dict):
            return []
        receipts = []
        for canonical_id, result in sorted(raw_results.items()):
            if not isinstance(result, dict):
                continue
            child_trace_id = result.get("trace_id")
            payload = {
                "schema_version": "dle.lifecycle-transition.v1",
                "trace_id": trace_id,
                "transition_kind": "ka",
                "stage_id": stage.stage_id,
                "parent_stage_id": stage.stage_id,
                "canonical_id": canonical_id,
                "child_trace_id": child_trace_id,
                "state": result.get("state"),
                "outcome_type": result.get("outcome_type"),
            }
            try:
                message = self.truth_link.publish(
                    "truth_core",
                    "ka_transition",
                    payload,
                    session_id=trace_id,
                )
            except Exception as exc:
                raise KnowledgeLifecycleError(
                    "TruthLink KA publication failed"
                ) from exc
            if not isinstance(message, dict) or not message.get("message_id"):
                raise KnowledgeLifecycleError("TruthLink KA publication failed")
            receipts.append(
                {
                    "canonical_id": canonical_id,
                    "child_trace_id": child_trace_id,
                    "message_id": message["message_id"],
                    "parent_stage_id": stage.stage_id,
                }
            )
        return receipts
