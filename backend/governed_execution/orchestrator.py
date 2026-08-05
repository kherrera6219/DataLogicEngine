"""Single backend-owned governed request orchestrator."""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import time
from collections.abc import Callable
from contextlib import suppress
from contextvars import ContextVar
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from backend.dmrf.truth_integration.core_adapter import TruthCoreDMRFAdapter
from backend.governed_execution.cancellation import CANCELLATION_REGISTRY
from backend.governed_execution.contracts import (
    GovernedContext,
    GovernedFailure,
    GovernedFailureKind,
    GovernedMode,
    GovernedPolicyDecision,
    GovernedRequest,
    GovernedResult,
    GovernedStage,
    GovernedStageStatus,
)
from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
)
from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleCoordinator,
    KnowledgeLifecycleError,
    LifecycleTransitionPublisher,
)
from backend.governed_execution.prompt import build_refinement_messages
from backend.governed_execution.quality import (
    measure_evidence,
)
from backend.governed_execution.refinement import CanonicalRefinementWorkflow
from backend.governed_execution.retrieval import retrieve_evidence
from backend.governed_execution.ten_layers import (
    LAYER_NAMES,
    GovernedTenLayerStages,
    LayerExecution,
)
from backend.llm_gateway.latency_metrics import record_ai_request
from backend.llm_gateway.provider_budget import ProviderBudgetPolicy
from backend.llm_gateway.provider_errors import (
    ProviderFailureClass,
    classify_provider_failure,
)

logger = logging.getLogger(__name__)

_ACTIVE_TRACE: ContextVar[str | None] = ContextVar(
    "dle_active_governed_trace", default=None
)


class GovernedExecutionOrchestrator:
    """Own the only product request path from admission through persistence."""

    def __init__(
        self,
        gateway: Any,
        *,
        dmrf_factory: Callable[..., Any] | None = None,
        dsqp_factory: Callable[..., Any] | None = None,
        truthcore: TruthCoreDMRFAdapter | None = None,
        rag_service: Any | None = None,
        event_sink: Callable[[str, dict[str, Any]], None] | None = None,
        knowledge_lifecycle: KnowledgeLifecycleCoordinator | None = None,
        extended_subsystems: ExtendedSubsystemCoordinator | None = None,
        transition_publisher: LifecycleTransitionPublisher | None = None,
    ) -> None:
        self.gateway = gateway
        self.dmrf_factory = dmrf_factory
        self.dsqp_factory = dsqp_factory
        self.truthcore = truthcore or TruthCoreDMRFAdapter(
            db_session=getattr(gateway, "db", None)
        )
        self.layer_stages = GovernedTenLayerStages(self.truthcore)
        self.refinement_workflow = CanonicalRefinementWorkflow(
            ka_controller=self.layer_stages.ka_controller
        )
        self.knowledge_lifecycle = knowledge_lifecycle or KnowledgeLifecycleCoordinator(
            ka_controller=self.layer_stages.ka_controller
        )
        self.extended_subsystems = extended_subsystems or ExtendedSubsystemCoordinator(
            ka_controller=self.layer_stages.ka_controller
        )
        self.transition_publisher = (
            transition_publisher or LifecycleTransitionPublisher()
        )
        self.rag_service = rag_service
        self.event_sink = event_sink

    async def execute(self, request: GovernedRequest) -> GovernedResult:
        active_trace = _ACTIVE_TRACE.get()
        if active_trace is not None:
            context = GovernedContext(request=request)
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="GOVERNED_REENTRY_BLOCKED",
                message="Recursive governed execution is not allowed",
                stage="admission",
                details={"active_trace_id": active_trace},
            )

        context = GovernedContext(request=request)
        request.metadata["_trace_id"] = context.trace_id
        token = _ACTIVE_TRACE.set(context.trace_id)
        server_deadline = self._bounded_int(
            os.environ.get("GOVERNED_REQUEST_DEADLINE_SECONDS"), 120, 5, 300
        )
        requested_deadline = self._bounded_int(
            request.constraints.get("deadline_seconds"),
            server_deadline,
            1,
            server_deadline,
        )
        context.deadline_at_monotonic = time.monotonic() + requested_deadline
        request.metadata["deadline_seconds"] = requested_deadline
        context.cancellation_entry = CANCELLATION_REGISTRY.register(
            request.request_id, context.trace_id
        )
        execution_task: asyncio.Task[GovernedResult] | None = None
        cancellation_task: asyncio.Task[bool] | None = None
        try:
            execution_task = asyncio.create_task(self._execute(context))
            cancellation_task = asyncio.create_task(
                context.cancellation_entry.event.wait()
            )
            async with asyncio.timeout(requested_deadline):
                done, _ = await asyncio.wait(
                    {execution_task, cancellation_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if cancellation_task in done:
                    execution_task.cancel()
                    with suppress(asyncio.CancelledError):
                        await execution_task
                    return await self._failure(
                        context,
                        kind=GovernedFailureKind.CANCELLED,
                        code="REQUEST_CANCELLED",
                        message="Request cancelled",
                        stage=context.stages[-1].name
                        if context.stages
                        else "admission",
                    )
                cancellation_task.cancel()
                with suppress(asyncio.CancelledError):
                    await cancellation_task
                return await execution_task
        except TimeoutError:
            if execution_task is not None:
                execution_task.cancel()
                with suppress(asyncio.CancelledError):
                    await execution_task
            return await self._failure(
                context,
                kind=GovernedFailureKind.TIMEOUT,
                code="REQUEST_DEADLINE_EXCEEDED",
                message=f"Request exceeded its {requested_deadline}s deadline",
                stage=context.stages[-1].name if context.stages else "admission",
                details={"deadline_seconds": requested_deadline},
            )
        except asyncio.CancelledError:
            if execution_task is not None:
                execution_task.cancel()
            return await self._failure(
                context,
                kind=GovernedFailureKind.CANCELLED,
                code="REQUEST_CANCELLED",
                message="Request cancelled",
                stage=context.stages[-1].name if context.stages else "admission",
            )
        except Exception as exc:
            logger.exception("Governed execution failed")
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="GOVERNED_INTERNAL_FAILURE",
                message="Governed execution failed",
                stage=context.stages[-1].name if context.stages else "admission",
                details={"error_type": type(exc).__name__},
            )
        finally:
            if cancellation_task is not None:
                cancellation_task.cancel()
            CANCELLATION_REGISTRY.unregister(context.cancellation_entry)
            _ACTIVE_TRACE.reset(token)

    async def _execute(self, context: GovernedContext) -> GovernedResult:
        request = context.request

        admission = self._begin(
            context, "admission", "policy", {"request_id": request.request_id}
        )
        query = request.query_text()
        decision = self.gateway._governance.prepare_request(request, query)
        context.policy_decisions.append(
            GovernedPolicyDecision(
                policy_id="ai_governance_admission",
                decision="allow" if decision.ok else "block",
                rationale=decision.error,
                flags=list(decision.governance_flags),
                stage="admission",
            )
        )
        if not decision.ok:
            self._finish(
                context,
                admission,
                GovernedStageStatus.BLOCKED,
                outputs={"decision": "block", "flags": decision.governance_flags},
                error_code="GOVERNANCE_BLOCK",
            )
            self._audit_failure(context, "GOVERNANCE_BLOCK", decision.error)
            return await self._failure(
                context,
                kind=GovernedFailureKind.POLICY_BLOCK,
                code="GOVERNANCE_BLOCK",
                message=decision.error or "Request blocked by governance policy",
                stage="admission",
            )

        context.query = decision.query
        self._apply_governance_decision(request, decision)
        entry_policy = await self._execute_entry_truthgate(context)
        if entry_policy.blocked:
            self._finish(
                context,
                admission,
                GovernedStageStatus.BLOCKED,
                outputs={
                    "decision": "block",
                    "governance_flags": decision.governance_flags,
                    "truthgate": entry_policy.to_dict(),
                },
                error_code="TRUTHGATE_ENTRY_BLOCK",
            )
            return await self._failure(
                context,
                kind=GovernedFailureKind.POLICY_BLOCK,
                code="TRUTHGATE_ENTRY_BLOCK",
                message="Request blocked by the canonical entry policy gate",
                stage="admission",
            )
        self._finish(
            context,
            admission,
            GovernedStageStatus.COMPLETED,
            outputs={
                "decision": "allow",
                "governance_flags": decision.governance_flags,
                "estimated_request_tokens": decision.estimated_request_tokens,
                "truthgate": entry_policy.to_dict(),
            },
        )
        if self._cancel_requested(request):
            return await self._cancel(context, "admission")

        if request.mode is GovernedMode.SIMULATION:
            boundary = self._begin(
                context,
                "simulation_job_contract",
                "contract",
                {"successor": "/api/v1/simulations"},
            )
            self._finish(
                context,
                boundary,
                GovernedStageStatus.FAILED,
                outputs={
                    "available": True,
                    "requires_durable_session": True,
                    "successor": "/api/v1/simulations",
                },
                error_code="SIMULATION_DURABLE_JOB_REQUIRED",
            )
            return await self._failure(
                context,
                kind=GovernedFailureKind.VALIDATION_FAILURE,
                code="SIMULATION_DURABLE_JOB_REQUIRED",
                message=(
                    "Simulation execution requires the durable simulation session API "
                    "at /api/v1/simulations"
                ),
                stage="simulation_job_contract",
            )

        routing_stage = self._begin(
            context,
            "dmrf_routing",
            "control_plane",
            {"query": context.query, "mode": request.mode.value},
        )
        try:
            if self.dmrf_factory is None:
                from backend.dmrf import DMRFOrchestrator

                dmrf = DMRFOrchestrator(
                    desktop_mode=self.gateway._desktop_local_first_enabled(),
                    db_session=getattr(self.gateway, "db", None),
                    ka_controller=getattr(
                        getattr(self.truthcore, "engine", None),
                        "ka_controller",
                        None,
                    ),
                )
            else:
                dmrf = self.dmrf_factory(
                    desktop_mode=self.gateway._desktop_local_first_enabled(),
                    db_session=getattr(self.gateway, "db", None),
                )
            dmrf_result = await dmrf.process(
                context.query,
                context={
                    **request.metadata,
                    "constraints": request.constraints,
                    "_canonical_defer_dsqp": True,
                    "dsqp_llm_assisted": False,
                },
                offline=bool(
                    request.metadata.get("offline")
                    or request.metadata.get("providers_unreachable")
                ),
            )
        except Exception as exc:  # noqa: BLE001 - DMRF boundary fails closed
            self._finish(
                context,
                routing_stage,
                GovernedStageStatus.FAILED,
                outputs={"error_type": type(exc).__name__},
                error_code="DMRF_FAILURE",
            )
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="DMRF_FAILURE",
                message="Governed routing failed",
                stage="dmrf_routing",
            )

        context.routing = dmrf_result.export_bundle()
        request.metadata["dmrf"] = context.routing
        request.metadata["dmrf_tier"] = dmrf_result.tier
        request.metadata["axis_vector"] = context.routing.get("axis_vector", {})
        gate_result = (
            context.routing.get("gate_result")
            if isinstance(context.routing.get("gate_result"), dict)
            else {}
        )
        context.policy_decisions.append(
            GovernedPolicyDecision(
                policy_id="dmrf_truth_gate",
                decision="allow" if dmrf_result.ok else "block",
                rationale=gate_result.get("reason") or "; ".join(dmrf_result.warnings),
                stage="dmrf_routing",
                rule_id=gate_result.get("rule_id"),
            )
        )
        if not dmrf_result.ok:
            self._finish(
                context,
                routing_stage,
                GovernedStageStatus.BLOCKED,
                outputs={"decision": "block", "dmrf": context.routing},
                error_code="TRUTH_GATE_BLOCK",
            )
            return await self._failure(
                context,
                kind=GovernedFailureKind.POLICY_BLOCK,
                code="TRUTH_GATE_BLOCK",
                message="Request blocked by the governed policy gate",
                stage="dmrf_routing",
                details={"warnings": list(dmrf_result.warnings)},
            )
        self._finish(
            context,
            routing_stage,
            GovernedStageStatus.COMPLETED,
            outputs={
                "tier": dmrf_result.tier,
                "gate_result": dmrf_result.gate_result,
                "axis_vector": context.routing.get("axis_vector", {}),
                "dmrf_steps": context.routing.get("steps", []),
            },
        )
        axis_vector = context.routing.get("axis_vector", {})

        l1_stage = self._begin_layer(
            context,
            "L1",
            {
                "query": context.query,
                "tier": dmrf_result.tier,
                "axis_vector": context.routing.get("axis_vector", {}),
            },
        )
        axis17 = (
            ((axis_vector.get("axes") or {}).get("17") or {})
            if isinstance(axis_vector, dict)
            else {}
        )
        l1 = await self.layer_stages.l1(
            context,
            tier=dmrf_result.tier,
            axis17_context=axis17,
        )
        self._finish_layer(
            context,
            l1_stage,
            "L1",
            l1,
            terminal_status=(GovernedStageStatus.BLOCKED if not l1.ok else None),
        )
        if not l1.ok:
            return await self._failure(
                context,
                kind=GovernedFailureKind.POLICY_BLOCK,
                code=l1.error_code or "L1_INPUT_BLOCKED",
                message="The request did not pass governed L1 admission and routing",
                stage=l1_stage.name,
                details=l1.outputs,
            )
        if self._cancel_requested(request):
            return await self._cancel(context, l1_stage.name)

        retrieval_stage = self._begin_layer(
            context,
            "L2",
            {"query": context.query},
        )
        context.evidence, retrieval_warnings = await asyncio.to_thread(
            retrieve_evidence,
            request,
            context.query,
            rag_service=self.rag_service,
            memory_service=self.knowledge_lifecycle.memory_service,
        )
        await self._execute_retrieval_owners(context)
        for item in context.evidence:
            item.bind_to_trace(context.trace_id)
            measure_evidence(item)
        context.warnings.extend(retrieval_warnings)
        l2 = self.layer_stages.l2(context)
        l2.outputs.update(
            {
                "decisions": list(request.metadata.get("_retrieval_decisions") or []),
                "warnings": retrieval_warnings,
            }
        )
        self._finish_layer(
            context,
            retrieval_stage,
            "L2",
            l2,
            metrics={"retrieval_count": len(context.evidence)},
        )
        if self._cancel_requested(request):
            return await self._cancel(context, retrieval_stage.name)

        l3_stage = self._begin_layer(
            context,
            "L3",
            {
                "evidence_ids": [item.evidence_id for item in context.evidence],
                "external_research_requested": bool(
                    request.metadata.get("external_research_requested")
                ),
            },
        )
        l3 = self.layer_stages.l3(context)
        self._finish_layer(
            context,
            l3_stage,
            "L3",
            l3,
            terminal_status=(GovernedStageStatus.BLOCKED if not l3.ok else None),
        )
        if not l3.ok:
            return await self._failure(
                context,
                kind=GovernedFailureKind.POLICY_BLOCK,
                code=l3.error_code or "L3_EVIDENCE_PLAN_BLOCKED",
                message="The evidence acquisition plan was not authorized",
                stage=l3_stage.name,
                details=l3.outputs,
            )

        dsqp_stage = self._begin_layer(
            context,
            "L4",
            {
                "query": context.query,
                "source_ids": [item.source_id for item in context.evidence],
            },
        )
        if request.metadata.get("dsqp_llm_assisted"):
            context.warnings.append(
                "cloud_dsqp_not_authorized_without_accounted_subcall_budget"
            )
        if self.dsqp_factory is None:
            from backend.dsqp import DSQPOrchestrator

            dsqp = DSQPOrchestrator(timeout_seconds=30)
        else:
            dsqp = self.dsqp_factory(timeout_seconds=30)
        axis_vector = context.routing.get("axis_vector", {})
        risk_domain = (
            ((axis_vector.get("axes") or {}).get("15") or {}).get("value")
            if isinstance(axis_vector, dict)
            else None
        ) or "standard"
        context.dsqp = await dsqp.construct_all(
            context.query,
            axis_vector=axis_vector,
            context={
                **request.metadata,
                "risk_domain": risk_domain,
                "evidence_source_ids": [item.source_id for item in context.evidence],
                "dsqp_llm_assisted": False,
            },
        )
        expected_persona_axes = {"8", "9", "10", "11"}
        constructed_persona_axes = set((context.dsqp.get("profiles") or {}).keys())
        dsqp_failures = context.dsqp.get("failures") or {}
        dsqp_complete = (
            expected_persona_axes.issubset(constructed_persona_axes)
            and not dsqp_failures
            and not context.dsqp.get("partial")
        )
        dsqp_status = (
            GovernedStageStatus.COMPLETED
            if dsqp_complete
            else GovernedStageStatus.FAILED
        )
        l4 = await self._resolve_layer_execution(self.layer_stages.l4(context))
        l4.ok = l4.ok and dsqp_status is GovernedStageStatus.COMPLETED
        l4.outputs.update(
            {
                "dsqp": context.dsqp,
                "expected_persona_axes": sorted(expected_persona_axes),
                "constructed_persona_axes": sorted(constructed_persona_axes),
            }
        )
        if not l4.ok:
            l4.error_code = "L4_PERSONA_CONTEXT_FAILURE"
        self._finish_layer(
            context,
            dsqp_stage,
            "L4",
            l4,
        )
        if not l4.ok:
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="L4_PERSONA_CONTEXT_FAILURE",
                message="Deterministic persona construction failed",
                stage=dsqp_stage.name,
            )

        prompt_stage = self._begin_layer(
            context,
            "L5",
            {
                "source_ids": [item.source_id for item in context.evidence],
                "persona_ids": [
                    profile.get("persona_id")
                    for profile in (context.dsqp.get("profiles") or {}).values()
                    if isinstance(profile, dict)
                ],
                "ka_ids": [
                    item.get("ka_id")
                    for item in context.truthcore.get("steps_executed") or []
                    if isinstance(item, dict)
                ],
            },
        )
        l5 = await self._resolve_layer_execution(self.layer_stages.l5(context))
        self._finish_layer(
            context,
            prompt_stage,
            "L5",
            l5,
        )
        if not l5.ok:
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code=l5.error_code or "L5_CANDIDATE_PLAN_FAILURE",
                message="The governed candidate plan could not be constructed",
                stage=prompt_stage.name,
                details=l5.outputs,
            )
        if self._cancel_requested(request):
            return await self._cancel(context, prompt_stage.name)
        if request.mode is GovernedMode.LOCAL_REVIEW:
            return await self._complete_local_review(context)

        provider_stage = self._begin(
            context,
            "provider_execution",
            "provider",
            {"message_count": len(context.provider_messages)},
        )
        provider_result = await self._execute_provider(context)
        if not provider_result.get("ok"):
            self._finish(
                context,
                provider_stage,
                GovernedStageStatus.FAILED,
                outputs={
                    "attempts": provider_result.get("attempts", []),
                    "provider_call_count": context.provider_call_count,
                    "ka_lifecycle": provider_result.get("ka_lifecycle", {}),
                    "effect_receipt": provider_result.get("effect_receipt"),
                },
                metrics={"provider_call_count": context.provider_call_count},
                error_code="PROVIDER_FAILURE",
            )
            return await self._failure(
                context,
                kind=GovernedFailureKind.PROVIDER_FAILURE,
                code=str(
                    (provider_result.get("failure") or {}).get("code")
                    or "PROVIDER_FAILURE"
                ),
                message=self.gateway._public_error_message(
                    provider_result.get("error")
                ),
                stage="provider_execution",
                retryable=bool(provider_result.get("retryable")),
                details={"provider_failure": provider_result.get("failure") or {}},
            )
        self._finish(
            context,
            provider_stage,
            GovernedStageStatus.COMPLETED,
            outputs={
                "provider": provider_result.get("provider_used"),
                "model": provider_result.get("model_used"),
                "attempts": provider_result.get("attempts", []),
                "ka_lifecycle": provider_result.get("ka_lifecycle", {}),
                "effect_receipt": provider_result.get("effect_receipt"),
            },
            metrics={
                "provider_call_count": context.provider_call_count,
                "tokens_in": provider_result.get("usage", {}).get("prompt_tokens", 0),
                "tokens_out": provider_result.get("usage", {}).get(
                    "completion_tokens", 0
                ),
            },
        )
        if self._cancel_requested(request):
            return await self._cancel(context, "provider_execution")

        max_refinements = self._bounded_int(
            request.constraints.get("max_refinement_cycles"),
            1 if request.mode is GovernedMode.ENHANCED else 0,
            0,
            1,
        )
        requires_evidence = bool(request.constraints.get("requires_evidence")) or (
            request.mode is GovernedMode.ENHANCED
            or str(dmrf_result.tier).lower()
            in {"high", "high_stakes", "extreme", "autonomous"}
        )
        evaluation = await self._evaluate_candidate(
            context,
            answer=str(provider_result.get("answer") or ""),
            tier=dmrf_result.tier,
            iteration=0,
            max_iterations=max_refinements,
            requires_evidence=requires_evidence,
        )
        if evaluation["failure"]:
            failure = evaluation["failure"]
            return await self._failure(
                context,
                kind=failure["kind"],
                code=failure["code"],
                message=failure["message"],
                stage=failure["stage"],
                details=failure["details"],
            )
        validation = evaluation["validation"]
        convergence = evaluation["convergence"]

        if convergence.action == "refine":
            refinement_stage = self._begin(
                context,
                "refinement_1",
                "refinement",
                convergence.to_dict(),
            )
            context.refinement_cycles = 1
            refinement = await self.refinement_workflow.execute(
                context,
                prior_answer=validation["answer"],
                decision=convergence,
            )
            refinement_payload = refinement.to_dict()
            if not refinement.ok or not refinement.rewrite_authorized:
                self._finish(
                    context,
                    refinement_stage,
                    GovernedStageStatus.BLOCKED,
                    outputs={"refinement": refinement_payload},
                    metrics={
                        "step_count": len(refinement.steps),
                        "provider_subcalls_used": refinement.provider_subcalls_used,
                    },
                    error_code="REFINEMENT_WORKFLOW_BLOCKED",
                )
                return await self._failure(
                    context,
                    kind=GovernedFailureKind.VALIDATION_FAILURE,
                    code="REFINEMENT_WORKFLOW_BLOCKED",
                    message="The canonical refinement workflow did not authorize a rewrite",
                    stage="refinement_1",
                    details={
                        "blocked_by_step": refinement.blocked_by_step,
                        "step_status_counts": refinement_payload["step_status_counts"],
                    },
                )
            context.provider_messages = build_refinement_messages(
                context,
                validation["answer"],
                convergence,
                refinement_payload,
            )
            refined_result = await self._execute_provider(
                context, save_user_message=False
            )
            if not refined_result.get("ok"):
                self._finish(
                    context,
                    refinement_stage,
                    GovernedStageStatus.FAILED,
                    outputs={
                        "attempts": refined_result.get("attempts", []),
                        "refinement": refinement_payload,
                    },
                    error_code="PROVIDER_REFINEMENT_FAILURE",
                )
                return await self._failure(
                    context,
                    kind=GovernedFailureKind.PROVIDER_FAILURE,
                    code=str(
                        (refined_result.get("failure") or {}).get("code")
                        or "PROVIDER_REFINEMENT_FAILURE"
                    ),
                    message=self.gateway._public_error_message(
                        refined_result.get("error")
                    ),
                    stage="refinement_1",
                    retryable=bool(refined_result.get("retryable")),
                    details={"provider_failure": refined_result.get("failure") or {}},
                )
            self._finish(
                context,
                refinement_stage,
                GovernedStageStatus.COMPLETED,
                outputs={
                    "provider": refined_result.get("provider_used"),
                    "model": refined_result.get("model_used"),
                    "attempts": refined_result.get("attempts", []),
                    "refinement": refinement_payload,
                    "ka_lifecycle": refined_result.get("ka_lifecycle", {}),
                    "effect_receipt": refined_result.get("effect_receipt"),
                },
                metrics={
                    "provider_call_count": context.provider_call_count,
                    "provider_rewrites": 1,
                    "provider_subcalls_used": refinement.provider_subcalls_used,
                    "step_count": len(refinement.steps),
                },
            )
            refined_evaluation = await self._evaluate_candidate(
                context,
                answer=str(refined_result.get("answer") or ""),
                tier=dmrf_result.tier,
                iteration=1,
                max_iterations=max_refinements,
                requires_evidence=requires_evidence,
            )
            if refined_evaluation["failure"]:
                failure = refined_evaluation["failure"]
                return await self._failure(
                    context,
                    kind=failure["kind"],
                    code=failure["code"],
                    message=failure["message"],
                    stage=failure["stage"],
                    details=failure["details"],
                )
            provider_result = refined_result
            validation = refined_evaluation["validation"]
            convergence = refined_evaluation["convergence"]

        result_status = "completed"
        result_answer = validation["answer"]
        if convergence.action == "abstain":
            result_status = "abstained"
            result_answer = (
                "DataLogicEngine could not produce an evidence-supported answer from the "
                "available sources. Review the cited evidence or provide additional sources."
            )

        self._stage_memory_proposal(context, result_answer)
        l10_stage = self._begin_layer(
            context,
            "L10",
            {
                "convergence": convergence.to_dict(),
                "candidate_status": result_status,
            },
        )
        l10 = await self._resolve_layer_execution(
            self.layer_stages.l10(
                context,
                final_action=convergence.action,
            )
        )
        self._finish_layer(
            context,
            l10_stage,
            "L10",
            l10,
            terminal_status=(GovernedStageStatus.BLOCKED if not l10.ok else None),
        )
        if not l10.ok:
            return await self._failure(
                context,
                kind=GovernedFailureKind.POLICY_BLOCK,
                code=l10.error_code or "L10_RELEASE_BLOCK",
                message="The candidate did not pass the governed release gate",
                stage=l10_stage.name,
                details=l10.outputs,
            )
        if l10.outputs.get("release", {}).get("released_content_modified"):
            provider_result = self.layer_stages.redact_sensitive_value(provider_result)
            validation = self.layer_stages.redact_sensitive_value(validation)
        result_answer = str(l10.outputs.get("released_content") or result_answer)
        if context.lifecycle_failures:
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="LIFECYCLE_PUBLICATION_FAILURE",
                message="The governed result was not released because lifecycle publication failed",
                stage=l10_stage.name,
                details={"failure_count": len(context.lifecycle_failures)},
            )
        if context.memory_proposal is not None:
            context.memory_proposal.content = result_answer
        await self._qualify_and_commit_memory(context)

        result = GovernedResult(
            trace_id=context.trace_id,
            ok=True,
            status=result_status,
            mode=request.mode,
            answer=result_answer,
            provider_used=provider_result.get("provider_used"),
            model_used=provider_result.get("model_used"),
            usage=provider_result.get("usage", {}),
            confidence=context.confidence_measurement.value,
            coordinate=context.routing.get("axis_vector"),
            tier=context.routing.get("tier"),
            stages=context.stages,
            evidence=context.evidence,
            claims=context.claims,
            citations=context.citations,
            validators=context.validators,
            confidence_measurement=context.confidence_measurement,
            convergence=convergence,
            warnings=context.warnings,
            metadata=self._metadata(
                context, provider_result=provider_result, validation=validation
            ),
        )
        if not await self._persist(context, result):
            self.knowledge_lifecycle.rollback_validated_memory(context.memory_proposal)
            self._apply_persistence_failure(context, result)
        if request.session_id and result.ok:
            await self.gateway._save_chat_message(
                request.session_id,
                request.user_id,
                "assistant",
                result.answer,
                context.trace_id,
            )
        return result

    async def _evaluate_candidate(
        self,
        context: GovernedContext,
        *,
        answer: str,
        tier: str,
        iteration: int,
        max_iterations: int,
        requires_evidence: bool,
    ) -> dict[str, Any]:
        l6_stage = self._begin_layer(
            context,
            "L6",
            {
                "iteration": iteration,
                "source_ids": [item.source_id for item in context.evidence],
                "answer_length": len(answer),
            },
            iteration=iteration,
        )
        l6, validation = self.layer_stages.l6(
            context,
            answer=answer,
            governance_engine=self.gateway._governance,
        )
        self._finish_layer(
            context,
            l6_stage,
            "L6",
            l6,
            iteration=iteration,
            metrics={
                "claim_count": len(context.claims),
                "validation_score": validation["validation_score"],
            },
        )
        if not l6.ok:
            return {
                "validation": validation,
                "convergence": None,
                "failure": {
                    "kind": GovernedFailureKind.VALIDATION_FAILURE,
                    "code": l6.error_code or "L6_OUTPUT_VALIDATION_FAILURE",
                    "message": (
                        "Provider output did not pass governed evidence "
                        "and confidence validation"
                    ),
                    "stage": l6_stage.name,
                    "details": {
                        "checks": validation.get("checks") or {},
                    },
                },
            }

        l7_stage = self._begin_layer(
            context,
            "L7",
            {
                "iteration": iteration,
                "claim_ids": [claim.claim_id for claim in context.claims],
            },
            iteration=iteration,
        )
        l7 = self.layer_stages.l7(context)
        self._finish_layer(
            context,
            l7_stage,
            "L7",
            l7,
            iteration=iteration,
        )
        if not l7.ok:
            return {
                "validation": validation,
                "convergence": None,
                "failure": {
                    "kind": GovernedFailureKind.VALIDATION_FAILURE,
                    "code": l7.error_code or "L7_REASONING_BOUNDARY_FAILURE",
                    "message": "The candidate exceeded its governed reasoning boundary",
                    "stage": l7_stage.name,
                    "details": l7.outputs,
                },
            }

        l8_stage = self._begin_layer(
            context,
            "L8",
            {
                "iteration": iteration,
                "validator_ids": [
                    validator.validator_id for validator in context.validators
                ],
            },
            iteration=iteration,
        )
        l8 = await self.layer_stages.l8(context)
        self._finish_layer(
            context,
            l8_stage,
            "L8",
            l8,
            iteration=iteration,
            terminal_status=(GovernedStageStatus.BLOCKED if not l8.ok else None),
        )
        if not l8.ok:
            return {
                "validation": validation,
                "convergence": None,
                "failure": {
                    "kind": GovernedFailureKind.POLICY_BLOCK,
                    "code": l8.error_code or "L8_TRUST_POLICY_BLOCK",
                    "message": "The candidate was blocked by the governed trust and policy gate",
                    "stage": l8_stage.name,
                    "details": l8.outputs,
                },
            }

        l9_stage = self._begin_layer(
            context,
            "L9",
            {
                "iteration": iteration,
                "max_iterations": max_iterations,
                "requires_evidence": requires_evidence,
            },
            iteration=iteration,
        )
        l9, convergence = await self._resolve_layer_execution(
            self.layer_stages.l9(
                context,
                tier=tier,
                iteration=iteration,
                max_iterations=max_iterations,
                requires_evidence=requires_evidence,
            )
        )
        self._finish_layer(
            context,
            l9_stage,
            "L9",
            l9,
            iteration=iteration,
            terminal_status=(GovernedStageStatus.BLOCKED if not l9.ok else None),
        )
        if not l9.ok:
            return {
                "validation": validation,
                "convergence": convergence,
                "failure": {
                    "kind": GovernedFailureKind.POLICY_BLOCK,
                    "code": l9.error_code or "L9_CONVERGENCE_BLOCK",
                    "message": "The candidate was blocked by governed convergence policy",
                    "stage": l9_stage.name,
                    "details": convergence.to_dict(),
                },
            }
        return {
            "validation": validation,
            "convergence": convergence,
            "failure": None,
        }

    async def _execute_entry_truthgate(
        self,
        context: GovernedContext,
    ) -> GovernedPolicyDecision:
        request = context.request
        requested_ids = ["KA-022", "KA-172", "KA-174", "KA-176", "KA-177"]
        sensitive_values = request.metadata.get("sensitive_values")
        if isinstance(sensitive_values, list) and sensitive_values:
            requested_ids.append("KA-173")
        risk_level = str(request.metadata.get("safety_risk_level") or "low").lower()
        if risk_level not in {"low", "medium", "high", "critical"}:
            risk_level = "critical"
        inputs = {
            "KA-022": {
                "recommendation": context.query or request.query_text(),
                "impact_scores": dict(
                    request.metadata.get("impact_scores")
                    if isinstance(request.metadata.get("impact_scores"), dict)
                    else {}
                ),
            },
            "KA-172": {
                "candidates": [
                    {
                        "candidate_id": request.request_id,
                        "risk_level": risk_level,
                        "hazard_ids": list(
                            request.metadata.get("hazard_ids")
                            if isinstance(request.metadata.get("hazard_ids"), list)
                            else []
                        ),
                        "required_safeguard_ids": list(
                            request.metadata.get("required_safeguard_ids")
                            if isinstance(
                                request.metadata.get("required_safeguard_ids"), list
                            )
                            else []
                        ),
                        "verified_safeguard_ids": list(
                            request.metadata.get("verified_safeguard_ids")
                            if isinstance(
                                request.metadata.get("verified_safeguard_ids"), list
                            )
                            else []
                        ),
                        "human_reviewed": bool(request.metadata.get("human_reviewed")),
                    }
                ]
            },
            "KA-173": {
                "text": context.query or request.query_text(),
                "sensitive_values": sensitive_values or [],
            },
            "KA-174": {
                "controls": [
                    {
                        "control_id": "governed-entry-policy",
                        "applicability": "applicable",
                        "implementation_status": "implemented",
                        "required_evidence_types": ["policy_decision"],
                        "evidence": {"policy_decision": ["ai_governance_admission"]},
                    }
                ]
            },
            "KA-176": {
                "decisions": [
                    {
                        "decision_id": "ai_governance_admission",
                        "risk_class": risk_level,
                        "policy_refs": ["governed.v1"],
                        "evidence_refs": [context.trace_id],
                        "approval_roles": [],
                        "owner_recorded": True,
                    }
                ],
                "required_approval_roles": {},
            },
            "KA-177": {
                "attributes": {"gateway_admitted": True},
                "rules": [
                    {
                        "rule_id": "allow-governed-admission",
                        "attribute": "gateway_admitted",
                        "operator": "equals",
                        "expected": True,
                        "effect": "allow",
                    }
                ],
                "default_effect": "deny",
            },
        }
        try:
            execution = await self.knowledge_lifecycle.execute_operation(
                owner="truthgate",
                operation="entry",
                requested_ids=requested_ids,
                ka_inputs=inputs,
                request_id=request.request_id,
                run_id=context.trace_id,
                max_effects=8,
                session_id=request.session_id,
                principal_id=request.principal_id,
                tier="entry",
                layer="L1",
                service_capabilities={
                    "truthgate_policy_service",
                    "privacy_filter_service",
                    "policy_decision_service",
                },
                deadline_ms=self._remaining_deadline_ms(context),
            )
            outputs = {
                canonical_id: payload.get("output", {})
                for canonical_id, payload in execution.results.items()
            }
            blocked = (
                outputs.get("KA-022", {}).get("mitigation_required") is True
                or any(
                    row.get("decision") == "block"
                    for row in outputs.get("KA-172", {}).get("decisions", [])
                    if isinstance(row, dict)
                )
                or outputs.get("KA-174", {}).get("all_applicable_controls_pass")
                is not True
                or any(
                    row.get("valid") is not True
                    for row in outputs.get("KA-176", {}).get("assessments", [])
                    if isinstance(row, dict)
                )
                or outputs.get("KA-177", {}).get("decision") != "allow"
            )
            policy = GovernedPolicyDecision(
                policy_id="canonical_truthgate_entry",
                decision="block" if blocked else "allow",
                rationale=(
                    "canonical_entry_ka_block"
                    if blocked
                    else "canonical_entry_ka_plan_committed"
                ),
                stage="admission",
                flags=(["truthgate_entry_ka_block"] if blocked else []),
                ka_results=execution.results,
            )
        except KnowledgeLifecycleError as exc:
            policy = GovernedPolicyDecision(
                policy_id="canonical_truthgate_entry",
                decision="block",
                rationale=str(exc),
                stage="admission",
                flags=["truthgate_entry_execution_failure"],
            )
        context.policy_decisions.append(policy)
        return policy

    async def _execute_retrieval_owners(
        self,
        context: GovernedContext,
    ) -> None:
        records = [
            {
                "id": item.source_id,
                "content": item.text,
                "source_type": item.source_type,
                "score": item.score,
                "content_hash": item.content_hash,
            }
            for item in context.evidence
        ]
        known_ids = {item.source_id for item in context.evidence}
        dependency_edges = sorted(
            {
                (str(upstream), item.source_id)
                for item in context.evidence
                for upstream in item.metadata.get("depends_on_source_ids", [])
                if str(upstream) in known_ids and str(upstream) != item.source_id
            }
        )
        requested_ids = ["KA-079"]
        inputs: dict[str, dict[str, Any]] = {
            "KA-079": {
                "query": context.query,
                "records": records,
                "max_results": len(records) or 1,
            }
        }
        if records:
            first_source = context.evidence[0]
            requested_ids.extend(["KA-018", "KA-1077", "KA-1092"])
            inputs.update(
                {
                    "KA-018": {
                        "source_id": first_source.source_id,
                        "source_type": first_source.source_type,
                        "content_sha256": first_source.content_hash,
                        "provenance_checks": first_source.metadata.get(
                            "provenance_checks", []
                        ),
                    },
                    "KA-1077": {
                        "candidates": [
                            {
                                "knowledge_id": item.source_id,
                                "relevance": self._bounded_signal(item.score),
                                "confidence": self._bounded_signal(
                                    item.quality_score
                                    if item.quality_score is not None
                                    else item.provenance_completeness
                                ),
                                "freshness": self._bounded_signal(item.freshness_score),
                                "reuse_count": self._bounded_count(
                                    item.metadata.get("reuse_count")
                                ),
                                "dependent_count": self._bounded_count(
                                    item.metadata.get("dependent_count")
                                ),
                            }
                            for item in context.evidence
                        ]
                    },
                    "KA-025": {
                        "nodes": [
                            {
                                "id": item.source_id,
                                "deps": sorted(
                                    str(value)
                                    for value in item.metadata.get(
                                        "depends_on_source_ids", []
                                    )
                                    if str(value) in known_ids
                                ),
                            }
                            for item in context.evidence
                        ]
                    },
                    "KA-1092": {
                        "changed_knowledge_ids": sorted(known_ids),
                        "known_knowledge_ids": sorted(known_ids),
                        "dependencies": [
                            {"upstream_id": upstream, "downstream_id": downstream}
                            for upstream, downstream in dependency_edges
                        ],
                    },
                }
            )
            if len(records) >= 2:
                requested_ids.append("KA-1049")
                inputs["KA-1049"] = {
                    "knowledge_nodes": [
                        {"node_id": item.source_id, "content": item.text}
                        for item in context.evidence
                    ]
                }
        execution = await self.knowledge_lifecycle.execute_operation(
            owner="retrieval_graph_memory",
            operation="retrieval",
            requested_ids=requested_ids,
            ka_inputs=inputs,
            request_id=context.request.request_id,
            run_id=context.trace_id,
            max_effects=4,
            session_id=context.request.session_id,
            principal_id=context.request.principal_id,
            tier=context.reasoning.tier,
            layer="L2",
            service_capabilities={
                "authorized_retrieval_service",
                "provenance_service",
            },
            deadline_ms=self._remaining_deadline_ms(context),
        )
        retrieval_output = execution.results.get("KA-079", {}).get("output", {})
        ranked_ids = [
            str(row.get("id"))
            for row in retrieval_output.get("results", [])
            if isinstance(row, dict) and row.get("id")
        ]
        rank = {source_id: index for index, source_id in enumerate(ranked_ids)}
        context.evidence.sort(
            key=lambda item: (
                rank.get(item.source_id, len(rank)),
                -(item.score or 0.0),
                item.source_id,
            )
        )
        for index, item in enumerate(context.evidence, start=1):
            item.citation_label = f"S{index}"
        lifecycle_evidence = execution.to_dict()
        lifecycle_evidence["traces"] = {
            canonical_id: {
                "parent_ids": list(trace.parent_ids),
                "events": [
                    event.model_dump(mode="json", exclude_none=True)
                    for event in trace.events
                ],
            }
            for canonical_id, trace in execution.report.traces.items()
            if canonical_id in execution.executed_ids
        }
        context.request.metadata.setdefault("_knowledge_lifecycle", {})["retrieval"] = (
            lifecycle_evidence
        )
        context.request.metadata.setdefault("_retrieval_decisions", []).append(
            {
                "disposition": "selected",
                "reason": "canonical_ka_retrieval_order",
                "ka_id": "KA-079",
                "ranked_source_ids": ranked_ids,
            }
        )

    @staticmethod
    def _bounded_signal(value: Any) -> float:
        try:
            return round(max(0.0, min(1.0, float(value))), 8)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _bounded_count(value: Any) -> int:
        try:
            return max(0, min(1_000_000, int(value)))
        except (TypeError, ValueError):
            return 0

    def _stage_memory_proposal(
        self,
        context: GovernedContext,
        content: str,
    ) -> None:
        if not context.request.session_id:
            return
        context.memory_proposal = self.knowledge_lifecycle.stage_validated_memory(
            content=content,
            session_id=context.request.session_id,
            source_run_id=context.trace_id,
            source_ids=[item.source_id for item in context.evidence],
            owner_user_id=context.request.user_id,
            principal_id=context.request.principal_id,
            tenant_id=(
                str(context.request.metadata.get("tenant_id"))
                if context.request.metadata.get("tenant_id") is not None
                else None
            ),
        )

    async def _qualify_and_commit_memory(
        self,
        context: GovernedContext,
    ) -> None:
        proposal = context.memory_proposal
        if proposal is None:
            return
        confidence = (
            context.confidence_measurement.value
            if context.confidence_measurement
            and context.confidence_measurement.value is not None
            else 0.0
        )
        contradiction_count = sum(
            claim.status == "contradicted" for claim in context.claims
        )
        knowledge_id = context.trace_id
        snapshot = {
            "nodes": [
                {
                    "id": knowledge_id,
                    "confidence": confidence,
                    "content_hash": (
                        sha256(context.reasoning.candidate.encode("utf-8")).hexdigest()
                        if context.reasoning.candidate
                        else None
                    ),
                }
            ],
            "edges": [],
        }
        provenance_nodes = [
            {
                "node_id": f"source-{index}",
                "node_type": "source",
                "source_ref": item.source_id,
                "content_sha256": item.content_hash,
            }
            for index, item in enumerate(context.evidence, start=1)
        ]
        if provenance_nodes:
            provenance_nodes.append(
                {
                    "node_id": "released-knowledge",
                    "node_type": "claim",
                    "source_ref": knowledge_id,
                    "parent_node_ids": [item["node_id"] for item in provenance_nodes],
                }
            )
        else:
            provenance_nodes.append(
                {
                    "node_id": "request-source",
                    "node_type": "source",
                    "source_ref": context.request.source,
                }
            )
        risk_class = str(
            context.request.metadata.get("safety_risk_level") or "low"
        ).lower()
        if risk_class not in {"low", "medium", "high", "critical"}:
            risk_class = "critical"
        evidence_inputs = [
            {
                "source": item.source_type,
                "source_id": item.source_id,
                "content_hash": item.content_hash,
            }
            for item in context.evidence
        ]
        candidate = str(context.reasoning.candidate or proposal.content)
        inputs = {
            "KA-004": {"query": context.query},
            "KA-005": {"query": context.query},
            "KA-018": {
                "source_id": (
                    evidence_inputs[0]["source_id"]
                    if evidence_inputs
                    else "request-source"
                ),
                "source_type": (
                    evidence_inputs[0]["source"]
                    if evidence_inputs
                    else context.request.source
                ),
                "content_sha256": (
                    evidence_inputs[0]["content_hash"]
                    if evidence_inputs
                    else sha256(context.request.source.encode("utf-8")).hexdigest()
                ),
                "provenance_checks": [],
            },
            "KA-022": {
                "recommendation": candidate,
                "impact_scores": {"governed_risk": 0.0},
            },
            "KA-024": {"confidence": confidence, "risk_score": 0.0},
            "KA-062": {"evidence": evidence_inputs},
            "KA-065": {"snapshot": snapshot, "baseline": snapshot},
            "KA-1071": {
                "knowledge_id": knowledge_id,
                "nodes": provenance_nodes,
            },
            "KA-1074": {
                "fields": [
                    {
                        "field_id": "released_knowledge",
                        "value": candidate,
                        "classification": "public",
                        "strategy": "retain",
                    }
                ]
            },
            "KA-1094": {
                "candidates": [
                    {
                        "knowledge_id": knowledge_id,
                        "validation_status": "validated",
                        "confidence": confidence,
                        "contradiction_count": contradiction_count,
                        "integrity_valid": True,
                        "provenance_complete": bool(context.evidence),
                    }
                ]
            },
            "KA-1107": {
                "planned_steps": [
                    {
                        "step_id": "validated-memory-release",
                        "capability_id": "KA-1096",
                        "layer": "L10",
                        "query_class": "knowledge_release",
                    }
                ],
                "allowed_capability_ids": ["KA-1096"],
                "allowed_layers": ["L10"],
                "allowed_query_classes": ["knowledge_release"],
            },
            "KA-1109": {
                "candidates": [
                    {
                        "knowledge_id": knowledge_id,
                        "declared_sensitivity": "public",
                        "contains_personal_data": False,
                        "consent_verified": True,
                        "redistribution_allowed": True,
                        "risk_signals": [],
                    }
                ]
            },
            "KA-1079": {
                "knowledge_id": knowledge_id,
                "validation_status": "validated",
                "confidence": confidence,
                "evidence_count": len(context.evidence),
                "citation_count": len(context.citations),
                "contradiction_count": contradiction_count,
                "provenance_complete": bool(context.evidence),
                "risk_class": risk_class,
            },
            "KA-1096": {
                "candidates": [
                    {
                        "release_id": f"release-{knowledge_id}",
                        "knowledge_version_ids": [knowledge_id],
                        "validation_status": "passed",
                        "required_approvals": 0,
                        "recorded_approvals": 0,
                        "dependencies_ready": True,
                        "rollback_plan_ref": f"rollback-{knowledge_id}",
                        "rollout_percent": 100,
                    }
                ]
            },
            "KA-117": {"snapshot": snapshot},
        }
        try:
            execution = await self.knowledge_lifecycle.execute_operation(
                owner="truthmemory_truthlink_frost",
                operation="release",
                requested_ids=["KA-1096"],
                ka_inputs=inputs,
                request_id=context.request.request_id,
                run_id=context.trace_id,
                max_effects=8,
                session_id=context.request.session_id,
                principal_id=context.request.principal_id,
                tier=context.reasoning.tier,
                layer="L10",
                service_capabilities={"knowledge_lifecycle_service"},
                deadline_ms=self._remaining_deadline_ms(context),
            )
        except KnowledgeLifecycleError as exc:
            proposal.state = "qualification_failed"
            proposal.receipt = {
                "service": "KnowledgeLifecycleCoordinator",
                "status": "failed",
                "error_type": type(exc).__name__,
            }
            context.warnings.append("validated_memory_qualification_failed")
            return
        context.request.metadata.setdefault("_knowledge_lifecycle", {})["release"] = (
            execution.to_dict()
        )
        outputs = {
            canonical_id: payload.get("output", {})
            for canonical_id, payload in execution.results.items()
        }
        quarantine = any(
            item.get("decision") == "quarantine"
            for item in outputs.get("KA-1094", {}).get("decisions", [])
            if isinstance(item, dict)
        )
        never_persist = any(
            item.get("containment_class") == "never_persist"
            for item in outputs.get("KA-1109", {}).get("decisions", [])
            if isinstance(item, dict)
        )
        promotion = outputs.get("KA-1079", {}).get("decision")
        release_staged = all(
            item.get("decision") == "stage"
            for item in outputs.get("KA-1096", {}).get("release_plans", [])
            if isinstance(item, dict)
        )
        if quarantine or never_persist or promotion != "approve" or not release_staged:
            proposal.state = (
                "quarantined" if quarantine or never_persist else "not_promoted"
            )
            proposal.receipt = {
                "service": "KnowledgeLifecycleCoordinator",
                "status": proposal.state,
                "promotion_decision": promotion,
                "release_staged": release_staged,
            }
            return
        self.knowledge_lifecycle.commit_validated_memory(proposal)

    @staticmethod
    def _remaining_deadline_ms(context: GovernedContext) -> int:
        if context.deadline_at_monotonic is None:
            return 20_000
        return max(
            1,
            min(
                20_000,
                int((context.deadline_at_monotonic - time.monotonic()) * 1000),
            ),
        )

    async def _execute_provider(
        self,
        context: GovernedContext,
        *,
        save_user_message: bool = True,
    ) -> dict[str, Any]:
        request = context.request
        allowed_provider_types = self.gateway._normalize_allowlist(
            request.metadata.get("allowed_provider_types")
            or request.metadata.get("allowed_providers")
        )
        allowed_models = self.gateway._normalize_allowlist(
            request.metadata.get("allowed_models")
        )

        store_history = True
        if request.user_id:
            try:
                from models import UserAIPreferences

                preferences = UserAIPreferences.query.filter_by(
                    user_id=request.user_id
                ).first()
                if preferences:
                    if not preferences.ai_processing_enabled:
                        return {
                            "ok": False,
                            "error": "AI processing is disabled in your account settings.",
                        }
                    request.provider = (
                        request.provider or preferences.preferred_provider
                    )
                    request.model = request.model or preferences.preferred_model
                    store_history = bool(preferences.store_chat_history)
            except Exception:
                logger.debug(
                    "User AI preferences could not be loaded",
                    exc_info=True,
                )

        try:
            provider_plan = await self.extended_subsystems.plan_provider_request(
                request_id=request.request_id,
                trace_id=context.trace_id,
                principal_id=str(request.user_id or request.api_key_id or "") or None,
                messages=context.provider_messages,
                token_budget=self._bounded_int(
                    request.constraints.get("max_input_tokens"),
                    128_000,
                    1,
                    2_000_000,
                ),
            )
        except KnowledgeLifecycleError:
            logger.warning(
                "Canonical provider KA admission blocked request %s",
                request.request_id,
            )
            return {
                "ok": False,
                "error": "Provider request governance blocked the request",
                "retryable": False,
                "attempts": [],
                "failure": {
                    "class": ProviderFailureClass.POLICY_BLOCK.value,
                    "code": "PROVIDER_KA_ADMISSION_BLOCKED",
                    "replayable": False,
                },
            }

        providers = await self.gateway._get_eligible_providers(
            request.provider,
            request.metadata,
            allowed_provider_types=allowed_provider_types or None,
            allowed_models=allowed_models or None,
        )
        if not providers:
            return {"ok": False, "error": "No active providers found", "attempts": []}

        if request.session_id and store_history and save_user_message:
            await self.gateway._save_chat_message(
                request.session_id,
                request.user_id,
                "user",
                context.query,
            )

        budget_policy = ProviderBudgetPolicy(getattr(self.gateway, "db", None))
        max_calls = budget_policy.request_call_limit(request.mode, request.constraints)
        attempts: list[dict[str, Any]] = []
        last_error = "Provider failed to generate a response"
        last_failure = classify_provider_failure(last_error)
        started = datetime.now(UTC)
        purpose = "refinement" if context.refinement_cycles else "answer"
        disclosed_categories = self._disclosed_categories(context)

        for provider_record in providers:
            if context.provider_call_count >= max_calls:
                break
            model = self.gateway._resolve_model(request, provider_record)
            provider_type = str(getattr(provider_record, "provider_type", "unknown"))
            circuit = self.gateway._get_circuit_breaker(f"{provider_type}:{model}")
            if not circuit.can_execute():
                attempts.append(
                    {
                        "provider": provider_type,
                        "model": model,
                        "status": "circuit_open",
                    }
                )
                last_error = "Provider circuit is open"
                last_failure = classify_provider_failure(
                    "provider outage: circuit open"
                )
                continue
            if allowed_models and model.strip().lower() not in allowed_models:
                attempts.append(
                    {
                        "provider": provider_record.name,
                        "model": model,
                        "status": "policy_skipped",
                    }
                )
                continue
            request.metadata["last_provider_used"] = provider_type
            request.metadata["last_model_used"] = model
            timeout_seconds = self.gateway._provider_timeout_seconds(provider_record)
            max_attempts = min(
                self.gateway._provider_max_retries(provider_record),
                max_calls - context.provider_call_count,
            )
            for retry_index in range(max_attempts):
                estimated_input_tokens = max(
                    1,
                    sum(
                        len(str(message.get("content") or ""))
                        for message in context.provider_messages
                    )
                    // 4,
                )
                budget = budget_policy.evaluate(
                    context=context,
                    projected_input_tokens=estimated_input_tokens,
                    projected_output_tokens=request.max_tokens,
                    projected_cost_usd=self.gateway._governance.estimate_cost_usd(
                        model,
                        estimated_input_tokens,
                        request.max_tokens,
                    ),
                )
                request.metadata["provider_budget"] = {
                    "code": budget.code,
                    "usage": budget.usage,
                    "limits": budget.limits,
                    "warning_threshold_crossed": budget.warning_threshold_crossed,
                }
                if not budget.allowed:
                    return {
                        "ok": False,
                        "error": budget.message,
                        "retryable": False,
                        "attempts": attempts,
                        "failure": {
                            "class": ProviderFailureClass.POLICY_BLOCK.value,
                            "code": budget.code,
                            "replayable": False,
                        },
                    }

                context.provider_call_count += 1
                attempt_started = datetime.now(UTC)
                provider = None
                try:
                    provider = self.gateway._create_sdk_provider(provider_record)
                    remaining = self._remaining_seconds(context)
                    if remaining <= 0:
                        raise TimeoutError(
                            "Request deadline exceeded before provider call"
                        )
                    provider_output = await asyncio.wait_for(
                        self.gateway._direct_llm_call(
                            provider,
                            model,
                            context.provider_messages,
                            request.temperature,
                            request.max_tokens,
                        ),
                        timeout=min(float(timeout_seconds), remaining),
                    )
                except TimeoutError as exc:
                    provider_output = {
                        "ok": False,
                        "error": f"Provider request timed out after {timeout_seconds}s",
                        "exception": exc,
                    }
                except Exception as exc:  # noqa: BLE001 - provider boundary
                    provider_output = {"ok": False, "error": str(exc), "exception": exc}
                finally:
                    close_provider = getattr(provider, "close", None)
                    if callable(close_provider):
                        try:
                            await close_provider()
                        except Exception:
                            logger.debug("Provider client close failed", exc_info=True)

                duration_ms = max(
                    0, int((datetime.now(UTC) - attempt_started).total_seconds() * 1000)
                )
                context.provider_latency_ms += duration_ms
                if provider_output.get("ok"):
                    circuit.record_success()
                    usage = (
                        provider_output.get("usage")
                        if isinstance(provider_output.get("usage"), dict)
                        else {}
                    )
                    tokens_in = int(usage.get("prompt_tokens", 0) or 0)
                    tokens_out = int(usage.get("completion_tokens", 0) or 0)
                    cost = self.gateway._governance.estimate_cost_usd(
                        model, tokens_in, tokens_out
                    )
                    usage["estimated_cost_usd"] = cost
                    usage["pricing_status"] = (
                        "available" if cost is not None else "unknown"
                    )
                    usage["latency_ms"] = max(
                        0, int((datetime.now(UTC) - started).total_seconds() * 1000)
                    )
                    attempts.append(
                        {
                            "provider": provider_type,
                            "model": model,
                            "call_index": context.provider_call_count,
                            "retry_index": retry_index,
                            "status": "completed",
                            "duration_ms": duration_ms,
                        }
                    )
                    record_ai_request(
                        provider=provider_type,
                        duration_ms=duration_ms,
                        success=True,
                    )
                    persisted = await self.gateway._record_usage(
                        provider_record.id,
                        provider_type,
                        request.user_id,
                        request.api_key_id,
                        context.trace_id,
                        request.session_id,
                        model,
                        tokens_in,
                        tokens_out,
                        duration_ms,
                        True,
                        estimated_cost_usd=cost,
                        purpose=purpose,
                        request_stage="refinement_1"
                        if purpose == "refinement"
                        else "provider_execution",
                        attempt_number=context.provider_call_count,
                        retry_index=retry_index,
                        status="completed",
                        disclosed_categories=disclosed_categories,
                        idempotency_key=f"{request.request_id}:{purpose}:{context.provider_call_count}",
                        started_at=attempt_started,
                        ended_at=datetime.now(UTC),
                    )
                    if persisted is False:
                        return {
                            "ok": False,
                            "error": "Provider usage ledger persistence failed",
                            "retryable": False,
                            "attempts": attempts,
                            "failure": {
                                "class": ProviderFailureClass.PERSISTENCE.value,
                                "code": "PROVIDER_LEDGER_PERSISTENCE_FAILED",
                                "replayable": False,
                            },
                        }
                    effect_receipt = self.extended_subsystems.bind_effect_receipt(
                        service="ProviderGatewayService",
                        operation=f"{purpose}:provider_call",
                        resource_id=(
                            f"{context.trace_id}:{context.provider_call_count}"
                        ),
                        request_payload={
                            "provider": provider_type,
                            "model": model,
                            "message_sha256": (
                                self.extended_subsystems.sha256_payload(
                                    context.provider_messages
                                )
                            ),
                        },
                        result_payload={
                            "answer_sha256": sha256(
                                str(provider_output.get("answer") or "").encode("utf-8")
                            ).hexdigest(),
                            "usage": usage,
                            "ledger_persisted": True,
                        },
                        idempotency_key=(
                            f"{request.request_id}:{purpose}:"
                            f"{context.provider_call_count}"
                        ),
                        ka_execution=provider_plan,
                        proposal_ids=[],
                    )
                    try:
                        provider_monitor = (
                            await self.extended_subsystems.monitor_provider_result(
                                request_id=request.request_id,
                                trace_id=context.trace_id,
                                principal_id=str(
                                    request.user_id or request.api_key_id or ""
                                )
                                or None,
                                duration_ms=duration_ms,
                            )
                        )
                        provider_monitoring_decision = (
                            self.extended_subsystems.provider_monitoring_decision(
                                provider_monitor
                            )
                        )
                    except KnowledgeLifecycleError:
                        logger.exception(
                            "Provider result KA monitoring failed for request %s",
                            request.request_id,
                        )
                        return {
                            "ok": False,
                            "error": "Provider result governance failed",
                            "retryable": False,
                            "attempts": attempts,
                            "ka_lifecycle": {
                                "request_governance": (
                                    self.extended_subsystems.lifecycle_evidence(
                                        provider_plan
                                    )
                                ),
                            },
                            "effect_receipt": effect_receipt.to_dict(),
                            "failure": {
                                "class": ProviderFailureClass.POLICY_BLOCK.value,
                                "code": "PROVIDER_KA_RESULT_GOVERNANCE_FAILED",
                                "replayable": False,
                            },
                        }
                    self._audit_success(context, provider_record, model, usage)
                    return {
                        "ok": True,
                        "answer": provider_output.get("answer", ""),
                        "usage": usage,
                        "provider_used": provider_type,
                        "model_used": model,
                        "attempts": attempts,
                        "ka_lifecycle": {
                            "request_governance": (
                                self.extended_subsystems.lifecycle_evidence(
                                    provider_plan
                                )
                            ),
                            "response_monitoring": (
                                self.extended_subsystems.lifecycle_evidence(
                                    provider_monitor
                                )
                            ),
                            "response_monitoring_decision": (
                                provider_monitoring_decision
                            ),
                        },
                        "effect_receipt": effect_receipt.to_dict(),
                    }

                last_error = str(
                    provider_output.get("error") or "Provider request failed"
                )
                last_failure = classify_provider_failure(
                    provider_output.get("exception") or last_error
                )
                retryable = last_failure.retryable
                attempts.append(
                    {
                        "provider": provider_type,
                        "model": model,
                        "call_index": context.provider_call_count,
                        "retry_index": retry_index,
                        "status": "failed",
                        "retryable": retryable,
                        "failure_class": last_failure.failure_class.value,
                        "duration_ms": duration_ms,
                    }
                )
                if last_failure.failure_class in {
                    ProviderFailureClass.NETWORK,
                    ProviderFailureClass.PROVIDER_OUTAGE,
                    ProviderFailureClass.TIMEOUT,
                    ProviderFailureClass.UNKNOWN,
                }:
                    circuit.record_failure()
                record_ai_request(
                    provider=provider_type,
                    duration_ms=duration_ms,
                    success=False,
                )
                persisted = await self.gateway._record_usage(
                    provider_record.id,
                    provider_type,
                    request.user_id,
                    request.api_key_id,
                    context.trace_id,
                    request.session_id,
                    model,
                    0,
                    0,
                    duration_ms,
                    False,
                    purpose=purpose,
                    request_stage="refinement_1"
                    if purpose == "refinement"
                    else "provider_execution",
                    attempt_number=context.provider_call_count,
                    retry_index=retry_index,
                    status="failed",
                    error_class=last_failure.failure_class.value,
                    error_code="PROVIDER_FAILURE",
                    error_message=last_error,
                    disclosed_categories=disclosed_categories,
                    idempotency_key=f"{request.request_id}:{purpose}:{context.provider_call_count}",
                    started_at=attempt_started,
                    ended_at=datetime.now(UTC),
                )
                if persisted is False:
                    return {
                        "ok": False,
                        "error": "Provider usage ledger persistence failed",
                        "retryable": False,
                        "attempts": attempts,
                        "failure": {
                            "class": ProviderFailureClass.PERSISTENCE.value,
                            "code": "PROVIDER_LEDGER_PERSISTENCE_FAILED",
                            "replayable": False,
                        },
                    }
                if retry_index + 1 < max_attempts and retryable:
                    delay = last_failure.retry_after_seconds
                    if delay is None:
                        delay = min(4.0, 0.5 * (2**retry_index))
                    remaining = self._remaining_seconds(context)
                    if remaining > delay:
                        await asyncio.sleep(delay)
                        continue
                break

        self._audit_failure(context, "PROVIDER_FAILURE", last_error)
        return {
            "ok": False,
            "error": last_error,
            "retryable": last_failure.retryable,
            "attempts": attempts,
            "failure": last_failure.to_dict(),
        }

    async def _complete_local_review(self, context: GovernedContext) -> GovernedResult:
        for layer_id in ("L6", "L7", "L8", "L9"):
            skipped_stage = self._begin_layer(
                context,
                layer_id,
                {"mode": GovernedMode.LOCAL_REVIEW.value},
            )
            skipped = LayerExecution(
                ok=True,
                outputs={
                    "layer_id": layer_id,
                    "reason": "no_provider_candidate_in_local_review_mode",
                },
                ka_plan={
                    "schema_version": "dle.ka-stage-plan.v1",
                    "layer_id": layer_id,
                    "selected_ids": [],
                    "selection_state": "not_applicable",
                    "effects_authorized": False,
                },
            )
            self._finish_layer(
                context,
                skipped_stage,
                layer_id,
                skipped,
                terminal_status=GovernedStageStatus.SKIPPED,
            )
        if context.evidence:
            source_lines = "\n".join(
                f"- [{item.citation_label}] {item.title or item.source_id} "
                f"(source_id={item.source_id})"
                for item in context.evidence
            )
            answer = (
                "Local review completed without a provider answer. "
                "Retrieved sources:\n" + source_lines
            )
        else:
            answer = (
                "Local review completed without a provider answer. "
                "No matching local sources were retrieved."
            )
        context.reasoning.candidate = answer
        self._stage_memory_proposal(context, answer)
        l10_stage = self._begin_layer(
            context,
            "L10",
            {"mode": GovernedMode.LOCAL_REVIEW.value},
        )
        l10 = await self._resolve_layer_execution(
            self.layer_stages.l10(
                context,
                final_action="local_review",
            )
        )
        self._finish_layer(context, l10_stage, "L10", l10)
        if not l10.ok:
            return await self._failure(
                context,
                kind=GovernedFailureKind.POLICY_BLOCK,
                code=l10.error_code or "L10_RELEASE_BLOCK",
                message="The local review did not pass the release gate",
                stage=l10_stage.name,
                details=l10.outputs,
            )

        stage = self._begin(
            context,
            "local_review",
            "result",
            {"source_ids": [item.source_id for item in context.evidence]},
        )
        answer = str(l10.outputs.get("released_content") or answer)
        if context.lifecycle_failures:
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="LIFECYCLE_PUBLICATION_FAILURE",
                message="The local review was not released because lifecycle publication failed",
                stage=l10_stage.name,
                details={"failure_count": len(context.lifecycle_failures)},
            )
        if context.memory_proposal is not None:
            context.memory_proposal.content = answer
        await self._qualify_and_commit_memory(context)
        self._finish(
            context,
            stage,
            GovernedStageStatus.COMPLETED,
            outputs={"provider_called": False, "source_count": len(context.evidence)},
        )
        if context.lifecycle_failures:
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="LIFECYCLE_PUBLICATION_FAILURE",
                message="The local review was not released because lifecycle publication failed",
                stage=stage.name,
                details={"failure_count": len(context.lifecycle_failures)},
            )
        result = GovernedResult(
            trace_id=context.trace_id,
            ok=True,
            status="completed",
            mode=context.request.mode,
            answer=answer,
            usage={"provider_call_count": 0},
            coordinate=context.routing.get("axis_vector"),
            tier=context.routing.get("tier"),
            stages=context.stages,
            evidence=context.evidence,
            claims=[],
            warnings=context.warnings,
            metadata=self._metadata(context),
        )
        if not await self._persist(context, result):
            self.knowledge_lifecycle.rollback_validated_memory(context.memory_proposal)
            self._apply_persistence_failure(context, result)
        return result

    async def _cancel(self, context: GovernedContext, stage: str) -> GovernedResult:
        return await self._failure(
            context,
            kind=GovernedFailureKind.CANCELLED,
            code="REQUEST_CANCELLED",
            message="Request cancelled",
            stage=stage,
        )

    async def _failure(
        self,
        context: GovernedContext,
        *,
        kind: GovernedFailureKind,
        code: str,
        message: str,
        stage: str,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> GovernedResult:
        if context.stages and context.stages[-1].status is GovernedStageStatus.RUNNING:
            terminal_status = (
                GovernedStageStatus.CANCELLED
                if kind in {GovernedFailureKind.CANCELLED, GovernedFailureKind.TIMEOUT}
                else GovernedStageStatus.FAILED
            )
            self._finish(
                context,
                context.stages[-1],
                terminal_status,
                error_code=code,
            )
        failure = GovernedFailure(
            kind=kind,
            code=code,
            message=message,
            stage=stage,
            retryable=retryable,
            details=details or {},
        )
        result = GovernedResult(
            trace_id=context.trace_id,
            ok=False,
            status=kind.value,
            mode=context.request.mode,
            provider_used=context.request.metadata.get("last_provider_used"),
            model_used=context.request.metadata.get("last_model_used")
            or context.request.model,
            coordinate=context.routing.get("axis_vector") if context.routing else None,
            tier=context.routing.get("tier") if context.routing else None,
            stages=context.stages,
            evidence=context.evidence,
            claims=context.claims,
            citations=context.citations,
            validators=context.validators,
            confidence_measurement=context.confidence_measurement,
            convergence=context.convergence_decisions[-1]
            if context.convergence_decisions
            else None,
            warnings=context.warnings,
            failure=failure,
            metadata=self._metadata(context),
        )
        await self._persist(context, result)
        return result

    async def _persist(self, context: GovernedContext, result: GovernedResult) -> bool:
        persistence = self._begin(
            context,
            "persistence",
            "persistence",
            {
                "trace_id": context.trace_id,
                "stage_count_before_persistence": len(context.stages),
            },
        )
        try:
            # Finalize before writing so the durable row never captures this
            # stage as running. Emit the terminal event only after the same
            # terminal state has committed.
            persistence.finish(
                GovernedStageStatus.COMPLETED,
                outputs={"trace_id": context.trace_id},
            )
            payload = result.to_dict()
            payload["trace"] = [stage.to_dict() for stage in context.stages]
            payload["latency_ms"] = sum(
                stage.duration_ms or 0
                for stage in context.stages
                if stage is not persistence
            )
            payload["metadata"] = self._metadata(context, **result.metadata)
            persisted = await self.gateway._create_trace_run(
                payload,
                context.query or context.request.query_text(),
                context.trace_id,
                str(context.request.user_id)
                if context.request.user_id is not None
                else "anonymous",
                context.request.session_id,
                result.model_used or context.request.model or "unknown",
            )
            if not persisted:
                raise RuntimeError("governed trace transaction did not commit")
            self._emit(context, persistence)
            if context.lifecycle_failures:
                raise RuntimeError("lifecycle transition publication did not commit")
            result.stages = context.stages
            return True
        except Exception as exc:  # noqa: BLE001 - persistence boundary
            self._finish(
                context,
                persistence,
                GovernedStageStatus.FAILED,
                outputs={"error_type": type(exc).__name__},
                error_code="TRACE_PERSISTENCE_FAILURE",
            )
            context.warnings.append("trace_persistence_failed")
            result.stages = context.stages
            return False

    @staticmethod
    def _apply_persistence_failure(
        context: GovernedContext, result: GovernedResult
    ) -> None:
        result.ok = False
        result.status = GovernedFailureKind.INTERNAL_FAILURE.value
        result.answer = ""
        result.failure = GovernedFailure(
            kind=GovernedFailureKind.INTERNAL_FAILURE,
            code="TRACE_PERSISTENCE_FAILURE",
            message="Provider result was not released because its governed trace did not persist",
            stage="persistence",
            retryable=False,
            details={"provider_succeeded": True},
        )
        result.warnings = context.warnings

    def _begin(
        self,
        context: GovernedContext,
        name: str,
        stage_type: str,
        inputs: dict[str, Any],
    ) -> GovernedStage:
        stage = context.add_stage(name, stage_type, inputs)
        self._emit(context, stage)
        return stage

    def _begin_layer(
        self,
        context: GovernedContext,
        layer_id: str,
        inputs: dict[str, Any],
        *,
        iteration: int = 0,
    ) -> GovernedStage:
        layer_number = int(layer_id.removeprefix("L"))
        suffix = f"_{iteration}" if iteration else ""
        return self._begin(
            context,
            f"layer_{layer_number}_{LAYER_NAMES[layer_id]}{suffix}",
            "reasoning_layer",
            {
                "layer_id": layer_id,
                "iteration": iteration,
                **inputs,
            },
        )

    def _finish_layer(
        self,
        context: GovernedContext,
        stage: GovernedStage,
        layer_id: str,
        execution: LayerExecution,
        *,
        iteration: int = 0,
        metrics: dict[str, Any] | None = None,
        terminal_status: GovernedStageStatus | None = None,
    ) -> None:
        status = terminal_status or (
            GovernedStageStatus.COMPLETED
            if execution.ok
            else GovernedStageStatus.FAILED
        )
        outputs = {
            **execution.outputs,
            "ka_plan": execution.ka_plan,
            "selected_ka_ids": execution.selected_ka_ids,
            "ka_results": execution.ka_results,
        }
        self._finish(
            context,
            stage,
            status,
            outputs=outputs,
            metrics=metrics,
            error_code=execution.error_code,
        )
        context.reasoning.record_layer(
            layer_id=layer_id,
            name=LAYER_NAMES[layer_id],
            iteration=iteration,
            stage=stage,
            selected_ka_ids=execution.selected_ka_ids,
            ka_plan=execution.ka_plan,
            ka_results=execution.ka_results,
            decisions=execution.decisions,
            effects=execution.effects,
        )

    def _finish(
        self,
        context: GovernedContext,
        stage: GovernedStage,
        status: GovernedStageStatus,
        *,
        outputs: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        stage.finish(status, outputs=outputs, metrics=metrics, error_code=error_code)
        self._emit(context, stage)

    def _emit(self, context: GovernedContext, stage: GovernedStage) -> None:
        trace_id = context.trace_id
        payload = {"run_id": trace_id, **stage.to_dict()}
        try:
            transition = self.transition_publisher.publish_stage(trace_id, stage)
            context.lifecycle_transitions.append(
                {
                    "stage_id": stage.stage_id,
                    "status": stage.status.value,
                    **transition,
                }
            )
            if stage.status is not GovernedStageStatus.RUNNING:
                context.lifecycle_transitions.extend(
                    self.transition_publisher.publish_ka_results(trace_id, stage)
                )
        except Exception as exc:  # noqa: BLE001 - recorded release dependency
            failure = {
                "stage_id": stage.stage_id,
                "stage_name": stage.name,
                "status": stage.status.value,
                "error_type": type(exc).__name__,
            }
            if failure not in context.lifecycle_failures:
                context.lifecycle_failures.append(failure)
            if "lifecycle_transition_publication_failed" not in context.warnings:
                context.warnings.append("lifecycle_transition_publication_failed")
        if self.event_sink is not None:
            self.event_sink(trace_id, payload)
            return
        try:
            from backend.websocket import emit_trace_stage_update

            emit_trace_stage_update(trace_id, payload)
        except Exception:
            logger.debug(
                "Trace stage update could not be emitted",
                exc_info=True,
            )

    @staticmethod
    def _apply_governance_decision(request: GovernedRequest, decision: Any) -> None:
        request.metadata["governance_flags"] = list(decision.governance_flags)
        request.metadata["estimated_request_tokens"] = decision.estimated_request_tokens
        if decision.prompt_template_key:
            request.metadata["prompt_template_key"] = decision.prompt_template_key
            request.metadata["prompt_template_version"] = (
                decision.prompt_template_version
            )
        if decision.routing_policy_name:
            request.metadata["routing_policy_name"] = decision.routing_policy_name
            request.metadata["routing_policy_version"] = decision.routing_policy_version
        if decision.allowed_provider_types:
            requested = set(request.metadata.get("allowed_provider_types") or ())
            request.metadata["allowed_provider_types"] = sorted(
                requested & decision.allowed_provider_types
                if requested
                else decision.allowed_provider_types
            )
        if decision.allowed_models:
            requested = set(request.metadata.get("allowed_models") or ())
            request.metadata["allowed_models"] = sorted(
                requested & decision.allowed_models
                if requested
                else decision.allowed_models
            )

    def _audit_success(
        self, context: GovernedContext, provider: Any, model: str, usage: dict[str, Any]
    ) -> None:
        self.gateway._governance.record_audit_event(
            run_id=context.trace_id,
            user_id=context.request.user_id,
            api_key_id=context.request.api_key_id,
            provider=getattr(provider, "provider_type", "unknown"),
            model=model,
            model_version=getattr(provider, "api_version", None) or "unknown",
            governance_flags=context.request.metadata.get("governance_flags"),
            request_tokens_estimate=context.request.metadata.get(
                "estimated_request_tokens"
            ),
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            estimated_cost_usd=usage.get("estimated_cost_usd"),
            success=True,
            metadata={
                "timestamp": datetime.now(UTC).isoformat(),
                "contract_version": context.request.contract_version,
            },
        )

    def _audit_failure(
        self, context: GovernedContext, code: str, message: str | None
    ) -> None:
        self.gateway._governance.record_audit_event(
            run_id=context.trace_id,
            user_id=context.request.user_id,
            api_key_id=context.request.api_key_id,
            provider=context.request.metadata.get("last_provider_used")
            or context.request.provider,
            model=context.request.metadata.get("last_model_used")
            or context.request.model
            or "unknown",
            model_version="unknown",
            governance_flags=context.request.metadata.get("governance_flags"),
            request_tokens_estimate=context.request.metadata.get(
                "estimated_request_tokens"
            ),
            success=False,
            error_code=code,
            error_message=message,
            metadata={
                "timestamp": datetime.now(UTC).isoformat(),
                "contract_version": context.request.contract_version,
            },
        )

    @staticmethod
    async def _resolve_layer_execution(value: Any) -> Any:
        """Await production stages while retaining synchronous adapter compatibility."""
        if inspect.isawaitable(value):
            return await value
        return value

    @staticmethod
    def _metadata(context: GovernedContext, **extra: Any) -> dict[str, Any]:
        total_elapsed_ms = max(
            0, int((time.monotonic() - context.started_monotonic) * 1000)
        )
        return {
            "contract_version": context.request.contract_version,
            "request_id": context.request.request_id,
            "source": context.request.source,
            "principal_kind": context.request.principal_kind,
            "dmrf": context.routing,
            "dsqp": context.dsqp,
            "truthcore": context.truthcore,
            "reasoning_state": context.reasoning.to_dict(),
            "policy_decisions": [
                decision.to_dict() for decision in context.policy_decisions
            ],
            "knowledge_lifecycle": dict(
                context.request.metadata.get("_knowledge_lifecycle") or {}
            ),
            "lifecycle_transitions": list(context.lifecycle_transitions),
            "lifecycle_failures": list(context.lifecycle_failures),
            "memory_lifecycle": (
                context.memory_proposal.to_dict()
                if context.memory_proposal is not None
                else None
            ),
            "provider_call_count": context.provider_call_count,
            "provider_latency_ms": context.provider_latency_ms,
            "orchestration_overhead_ms": max(
                0, total_elapsed_ms - context.provider_latency_ms
            ),
            "deadline_seconds": context.request.metadata.get("deadline_seconds"),
            "provider_budget": context.request.metadata.get("provider_budget"),
            "refinement_cycles": context.refinement_cycles,
            "confidence_measurement": context.confidence_measurement.to_dict()
            if context.confidence_measurement
            else None,
            "convergence_decisions": [
                item.to_dict() for item in context.convergence_decisions
            ],
            "source_ids": [item.source_id for item in context.evidence],
            **extra,
        }

    @staticmethod
    def _cancel_requested(request: GovernedRequest) -> bool:
        value = request.metadata.get("cancel_requested")
        if callable(value):
            try:
                return bool(value())
            except Exception:  # noqa: BLE001 - callback is caller-owned
                return True
        return bool(value)

    @staticmethod
    def _remaining_seconds(context: GovernedContext) -> float:
        if context.deadline_at_monotonic is None:
            return 300.0
        return max(0.0, context.deadline_at_monotonic - time.monotonic())

    @staticmethod
    def _disclosed_categories(context: GovernedContext) -> list[str]:
        categories = ["user_prompt"]
        if context.evidence:
            categories.append("retrieved_text")
        if context.dsqp:
            categories.append("persona_content")
        if context.truthcore:
            categories.append("truthcore_results")
        if any(
            message.get("role") == "assistant" for message in context.provider_messages
        ):
            categories.append("prior_provider_output")
        return categories

    @staticmethod
    def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))
