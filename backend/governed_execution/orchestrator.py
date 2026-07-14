"""Single backend-owned governed request orchestrator."""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from datetime import UTC, datetime
import logging
from typing import Any, Callable

from backend.dmrf.truth_integration.core_adapter import TruthCoreDMRFAdapter
from backend.governed_execution.contracts import (
    GovernedContext,
    GovernedFailure,
    GovernedFailureKind,
    GovernedMode,
    GovernedRequest,
    GovernedResult,
    GovernedStage,
    GovernedStageStatus,
)
from backend.governed_execution.prompt import build_provider_messages
from backend.governed_execution.retrieval import retrieve_evidence
from backend.governed_execution.validation import validate_output
from backend.llm_gateway.latency_metrics import record_ai_request


logger = logging.getLogger(__name__)

_ACTIVE_TRACE: ContextVar[str | None] = ContextVar("dle_active_governed_trace", default=None)


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
    ) -> None:
        self.gateway = gateway
        self.dmrf_factory = dmrf_factory
        self.dsqp_factory = dsqp_factory
        self.truthcore = truthcore or TruthCoreDMRFAdapter(db_session=getattr(gateway, "db", None))
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
        token = _ACTIVE_TRACE.set(context.trace_id)
        try:
            return await self._execute(context)
        except asyncio.CancelledError:
            return await self._failure(
                context,
                kind=GovernedFailureKind.CANCELLED,
                code="REQUEST_CANCELLED",
                message="Request cancelled",
                stage=context.stages[-1].name if context.stages else "admission",
            )
        except Exception as exc:  # fail closed at the single product boundary
            logger.error("Governed execution failed", exc_info=True)
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="GOVERNED_INTERNAL_FAILURE",
                message="Governed execution failed",
                stage=context.stages[-1].name if context.stages else "admission",
                details={"error_type": type(exc).__name__},
            )
        finally:
            _ACTIVE_TRACE.reset(token)

    async def _execute(self, context: GovernedContext) -> GovernedResult:
        request = context.request

        admission = self._begin(context, "admission", "policy", {"request_id": request.request_id})
        query = request.query_text()
        decision = self.gateway._governance.prepare_request(request, query)
        context.policy_decisions.append(
            {
                "policy_id": "ai_governance_admission",
                "decision": "allow" if decision.ok else "block",
                "rationale": decision.error,
                "flags": decision.governance_flags,
                "stage": "admission",
            }
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
        self._finish(
            context,
            admission,
            GovernedStageStatus.COMPLETED,
            outputs={
                "decision": "allow",
                "governance_flags": decision.governance_flags,
                "estimated_request_tokens": decision.estimated_request_tokens,
            },
        )
        if self._cancel_requested(request):
            return await self._cancel(context, "admission")

        if request.mode is GovernedMode.SIMULATION:
            boundary = self._begin(
                context,
                "simulation_boundary",
                "capability",
                {"required_phase": 10},
            )
            self._finish(
                context,
                boundary,
                GovernedStageStatus.FAILED,
                outputs={"available": False, "required_phase": 10},
                error_code="SIMULATION_PHASE10_BOUNDARY",
            )
            return await self._failure(
                context,
                kind=GovernedFailureKind.CAPABILITY_UNAVAILABLE,
                code="SIMULATION_PHASE10_BOUNDARY",
                message="Simulation execution remains disabled until the Phase 10 bounded workflow is connected",
                stage="simulation_boundary",
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
        except Exception as exc:
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
            {
                "policy_id": "dmrf_truth_gate",
                "decision": "allow" if dmrf_result.ok else "block",
                "rationale": gate_result.get("reason") or "; ".join(dmrf_result.warnings),
                "stage": "dmrf_routing",
                "rule_id": gate_result.get("rule_id"),
            }
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

        retrieval_stage = self._begin(
            context,
            "retrieval",
            "retrieval",
            {"query": context.query},
        )
        context.evidence, retrieval_warnings = await asyncio.to_thread(
            retrieve_evidence,
            request,
            context.query,
            rag_service=self.rag_service,
        )
        context.warnings.extend(retrieval_warnings)
        self._finish(
            context,
            retrieval_stage,
            GovernedStageStatus.COMPLETED,
            outputs={
                "source_ids": [item.source_id for item in context.evidence],
                "citation_labels": [item.citation_label for item in context.evidence],
                "warnings": retrieval_warnings,
            },
            metrics={"retrieval_count": len(context.evidence)},
        )
        if self._cancel_requested(request):
            return await self._cancel(context, "retrieval")

        dsqp_stage = self._begin(
            context,
            "dsqp_personas",
            "persona",
            {
                "query": context.query,
                "source_ids": [item.source_id for item in context.evidence],
            },
        )
        if request.metadata.get("dsqp_llm_assisted"):
            context.warnings.append("cloud_dsqp_not_authorized_without_accounted_subcall_budget")
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
        self._finish(
            context,
            dsqp_stage,
            dsqp_status,
            outputs={
                **context.dsqp,
                "expected_persona_axes": sorted(expected_persona_axes),
                "constructed_persona_axes": sorted(constructed_persona_axes),
            },
            error_code="DSQP_FAILURE" if dsqp_status is GovernedStageStatus.FAILED else None,
        )
        if dsqp_status is GovernedStageStatus.FAILED:
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="DSQP_FAILURE",
                message="Deterministic persona construction failed",
                stage="dsqp_personas",
            )

        truthcore_stage = self._begin(
            context,
            "truthcore_preflight",
            "workflow",
            {
                "query": context.query,
                "tier": dmrf_result.tier,
                "mode": request.mode.value,
            },
        )
        axis17 = ((axis_vector.get("axes") or {}).get("17") or {}) if isinstance(axis_vector, dict) else {}
        context.truthcore = await self.truthcore.execute(
            context.query,
            tier=dmrf_result.tier,
            axis17_context=axis17,
            context={
                **request.metadata,
                "evidence": [item.to_dict() for item in context.evidence],
                "dsqp": context.dsqp,
            },
            mode=request.mode.value,
        )
        self._finish(
            context,
            truthcore_stage,
            GovernedStageStatus.COMPLETED if context.truthcore.get("ok") else GovernedStageStatus.FAILED,
            outputs=context.truthcore,
            metrics={"ka_count": len(context.truthcore.get("steps_executed") or [])},
            error_code="TRUTHCORE_PREFLIGHT_FAILURE" if not context.truthcore.get("ok") else None,
        )
        if not context.truthcore.get("ok"):
            return await self._failure(
                context,
                kind=GovernedFailureKind.INTERNAL_FAILURE,
                code="TRUTHCORE_PREFLIGHT_FAILURE",
                message="TruthCore preflight failed",
                stage="truthcore_preflight",
            )

        if request.mode is GovernedMode.LOCAL_REVIEW:
            return await self._complete_local_review(context)
        prompt_stage = self._begin(
            context,
            "provider_request_construction",
            "provider",
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
        context.provider_messages = build_provider_messages(context)
        system_text = str(context.provider_messages[0].get("content") or "")
        self._finish(
            context,
            prompt_stage,
            GovernedStageStatus.COMPLETED,
            outputs={
                "message_count": len(context.provider_messages),
                "contains_source_ids": all(
                    item.source_id in system_text for item in context.evidence
                ),
                "contains_dsqp": "Deterministic persona context" in system_text,
                "contains_truthcore": "Executed TruthCore/KA context" in system_text,
            },
        )
        if self._cancel_requested(request):
            return await self._cancel(context, "provider_request_construction")

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
                },
                metrics={"provider_call_count": context.provider_call_count},
                error_code="PROVIDER_FAILURE",
            )
            return await self._failure(
                context,
                kind=GovernedFailureKind.PROVIDER_FAILURE,
                code="PROVIDER_FAILURE",
                message=self.gateway._public_error_message(provider_result.get("error")),
                stage="provider_execution",
                retryable=bool(provider_result.get("retryable")),
            )
        self._finish(
            context,
            provider_stage,
            GovernedStageStatus.COMPLETED,
            outputs={
                "provider": provider_result.get("provider_used"),
                "model": provider_result.get("model_used"),
                "attempts": provider_result.get("attempts", []),
            },
            metrics={
                "provider_call_count": context.provider_call_count,
                "tokens_in": provider_result.get("usage", {}).get("prompt_tokens", 0),
                "tokens_out": provider_result.get("usage", {}).get("completion_tokens", 0),
            },
        )
        if self._cancel_requested(request):
            return await self._cancel(context, "provider_execution")

        validation_stage = self._begin(
            context,
            "output_validation",
            "validation",
            {
                "source_ids": [item.source_id for item in context.evidence],
                "answer_length": len(str(provider_result.get("answer") or "")),
            },
        )
        validation = validate_output(
            str(provider_result.get("answer") or ""),
            context.evidence,
            mode=request.mode,
            governance_engine=self.gateway._governance,
        )
        context.claims = validation.pop("claims")
        context.warnings.extend(validation.get("warnings") or [])
        self._finish(
            context,
            validation_stage,
            GovernedStageStatus.COMPLETED if validation["ok"] else GovernedStageStatus.FAILED,
            outputs=validation,
            metrics={
                "claim_count": len(context.claims),
                "validation_score": validation["validation_score"],
            },
            error_code="OUTPUT_VALIDATION_FAILURE" if not validation["ok"] else None,
        )
        if not validation["ok"]:
            return await self._failure(
                context,
                kind=GovernedFailureKind.VALIDATION_FAILURE,
                code="OUTPUT_VALIDATION_FAILURE",
                message="Provider output did not pass governed validation",
                stage="output_validation",
                details={"checks": validation["checks"]},
            )

        result = GovernedResult(
            trace_id=context.trace_id,
            ok=True,
            status="completed",
            mode=request.mode,
            answer=validation["answer"],
            provider_used=provider_result.get("provider_used"),
            model_used=provider_result.get("model_used"),
            usage=provider_result.get("usage", {}),
            # Output-check completion is not an evidence confidence formula.
            # Keep this unmeasured until the Phase 6 contract is implemented.
            confidence=None,
            coordinate=context.routing.get("axis_vector"),
            tier=context.routing.get("tier"),
            stages=context.stages,
            evidence=context.evidence,
            claims=context.claims,
            warnings=context.warnings,
            metadata=self._metadata(context, provider_result=provider_result, validation=validation),
        )
        await self._persist(context, result)
        if request.session_id:
            await self.gateway._save_chat_message(
                request.session_id,
                request.user_id,
                "assistant",
                result.answer,
                context.trace_id,
            )
        return result

    async def _execute_provider(self, context: GovernedContext) -> dict[str, Any]:
        request = context.request
        allowed_provider_types = self.gateway._normalize_allowlist(
            request.metadata.get("allowed_provider_types")
            or request.metadata.get("allowed_providers")
        )
        allowed_models = self.gateway._normalize_allowlist(request.metadata.get("allowed_models"))

        operator_default = self.gateway._preferred_env_provider()
        if operator_default and str(request.provider or "").lower() in {"local_slm", "ollama", "vllm"}:
            request.provider = operator_default
            request.model = None
        if operator_default and not request.provider:
            request.provider = operator_default

        store_history = True
        if request.user_id:
            try:
                from models import UserAIPreferences

                preferences = UserAIPreferences.query.filter_by(user_id=request.user_id).first()
                if preferences:
                    if not preferences.ai_processing_enabled:
                        return {"ok": False, "error": "AI processing is disabled in your account settings."}
                    request.provider = request.provider or preferences.preferred_provider
                    request.model = request.model or preferences.preferred_model
                    store_history = bool(preferences.store_chat_history)
            except Exception:
                pass

        providers = await self.gateway._get_eligible_providers(
            request.provider,
            request.metadata,
            allowed_provider_types=allowed_provider_types or None,
            allowed_models=allowed_models or None,
        )
        if not providers:
            return {"ok": False, "error": "No active providers found", "attempts": []}

        if request.session_id and store_history:
            await self.gateway._save_chat_message(
                request.session_id,
                request.user_id,
                "user",
                context.query,
            )

        max_calls = self._bounded_int(request.constraints.get("max_provider_calls"), 4, 1, 10)
        attempts: list[dict[str, Any]] = []
        last_error = "All providers failed to generate a response"
        started = datetime.now(UTC)

        for provider_record in providers:
            if context.provider_call_count >= max_calls:
                break
            circuit = self.gateway._get_circuit_breaker(str(provider_record.id))
            if not circuit.can_execute():
                attempts.append({"provider": provider_record.name, "status": "circuit_open"})
                continue
            model = self.gateway._resolve_model(request, provider_record)
            if allowed_models and model.strip().lower() not in allowed_models:
                attempts.append({"provider": provider_record.name, "model": model, "status": "policy_skipped"})
                continue
            request.metadata["last_provider_used"] = getattr(provider_record, "provider_type", None)
            request.metadata["last_model_used"] = model
            timeout_seconds = self.gateway._provider_timeout_seconds(provider_record)
            max_retries = min(
                self.gateway._provider_max_retries(provider_record),
                max_calls - context.provider_call_count,
            )
            for retry_index in range(max_retries):
                context.provider_call_count += 1
                attempt_started = datetime.now(UTC)
                try:
                    provider = self.gateway._create_sdk_provider(provider_record)
                    provider_output = await asyncio.wait_for(
                        self.gateway._direct_llm_call(
                            provider,
                            model,
                            context.provider_messages,
                            request.temperature,
                            request.max_tokens,
                        ),
                        timeout=timeout_seconds,
                    )
                except TimeoutError:
                    provider_output = {"ok": False, "error": f"Provider request timed out after {timeout_seconds}s", "retryable": True}
                except Exception as exc:
                    provider_output = {"ok": False, "error": str(exc), "retryable": True}

                duration_ms = max(0, int((datetime.now(UTC) - attempt_started).total_seconds() * 1000))
                if provider_output.get("ok"):
                    circuit.record_success()
                    usage = provider_output.get("usage") if isinstance(provider_output.get("usage"), dict) else {}
                    tokens_in = int(usage.get("prompt_tokens", 0) or 0)
                    tokens_out = int(usage.get("completion_tokens", 0) or 0)
                    cost = self.gateway._governance.estimate_cost_usd(model, tokens_in, tokens_out)
                    usage["estimated_cost_usd"] = cost
                    usage["latency_ms"] = max(0, int((datetime.now(UTC) - started).total_seconds() * 1000))
                    attempts.append(
                        {
                            "provider": getattr(provider_record, "provider_type", "unknown"),
                            "model": model,
                            "call_index": context.provider_call_count,
                            "retry_index": retry_index,
                            "status": "completed",
                            "duration_ms": duration_ms,
                        }
                    )
                    record_ai_request(
                        provider=getattr(provider_record, "provider_type", "unknown"),
                        duration_ms=duration_ms,
                        success=True,
                    )
                    await self.gateway._record_usage(
                        provider_record.id,
                        request.user_id,
                        request.api_key_id,
                        context.trace_id,
                        model,
                        tokens_in,
                        tokens_out,
                        duration_ms,
                        True,
                        estimated_cost_usd=cost,
                    )
                    self._audit_success(context, provider_record, model, usage)
                    return {
                        "ok": True,
                        "answer": provider_output.get("answer", ""),
                        "usage": usage,
                        "provider_used": getattr(provider_record, "provider_type", "unknown"),
                        "model_used": model,
                        "attempts": attempts,
                    }

                last_error = str(provider_output.get("error") or "Provider request failed")
                rate_limited = self.gateway._is_rate_limit_error(last_error)
                retryable = not rate_limited and (
                    bool(provider_output.get("retryable"))
                    or self.gateway._is_retryable_error(last_error)
                )
                attempts.append(
                    {
                        "provider": getattr(provider_record, "provider_type", "unknown"),
                        "model": model,
                        "call_index": context.provider_call_count,
                        "retry_index": retry_index,
                        "status": "failed",
                        "retryable": retryable,
                        "rate_limited": rate_limited,
                        "duration_ms": duration_ms,
                    }
                )
                if not rate_limited:
                    circuit.record_failure()
                record_ai_request(
                    provider=getattr(provider_record, "provider_type", "unknown"),
                    duration_ms=duration_ms,
                    success=False,
                )
                if retry_index + 1 < max_retries and retryable:
                    await self.gateway._retry_backoff_sleep(retry_index)
                    continue
                await self.gateway._record_usage(
                    provider_record.id,
                    request.user_id,
                    request.api_key_id,
                    context.trace_id,
                    model,
                    0,
                    0,
                    duration_ms,
                    False,
                    error_code="PROVIDER_FAILURE",
                    error_message=last_error,
                )
                if rate_limited:
                    return {
                        "ok": False,
                        "error": last_error,
                        "retryable": False,
                        "attempts": attempts,
                    }
                break

        self._audit_failure(context, "PROVIDER_FAILURE", last_error)
        return {"ok": False, "error": last_error, "retryable": False, "attempts": attempts}

    async def _complete_local_review(self, context: GovernedContext) -> GovernedResult:
        stage = self._begin(
            context,
            "local_review",
            "result",
            {"source_ids": [item.source_id for item in context.evidence]},
        )
        if context.evidence:
            source_lines = "\n".join(
                f"- [{item.citation_label}] {item.title or item.source_id} (source_id={item.source_id})"
                for item in context.evidence
            )
            answer = "Local review completed without a provider answer. Retrieved sources:\n" + source_lines
        else:
            answer = "Local review completed without a provider answer. No matching local sources were retrieved."
        self._finish(
            context,
            stage,
            GovernedStageStatus.COMPLETED,
            outputs={"provider_called": False, "source_count": len(context.evidence)},
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
        await self._persist(context, result)
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
            model_used=context.request.metadata.get("last_model_used") or context.request.model,
            coordinate=context.routing.get("axis_vector") if context.routing else None,
            tier=context.routing.get("tier") if context.routing else None,
            stages=context.stages,
            evidence=context.evidence,
            claims=context.claims,
            warnings=context.warnings,
            failure=failure,
            metadata=self._metadata(context),
        )
        await self._persist(context, result)
        return result

    async def _persist(self, context: GovernedContext, result: GovernedResult) -> None:
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
                str(context.request.user_id) if context.request.user_id is not None else "anonymous",
                context.request.session_id,
                result.model_used or context.request.model or "unknown",
            )
            if not persisted:
                raise RuntimeError("governed trace transaction did not commit")
            self._emit(context.trace_id, persistence)
        except Exception as exc:
            self._finish(
                context,
                persistence,
                GovernedStageStatus.FAILED,
                outputs={"error_type": type(exc).__name__},
                error_code="TRACE_PERSISTENCE_FAILURE",
            )
            context.warnings.append("trace_persistence_failed")
        result.stages = context.stages

    def _begin(
        self,
        context: GovernedContext,
        name: str,
        stage_type: str,
        inputs: dict[str, Any],
    ) -> GovernedStage:
        stage = context.add_stage(name, stage_type, inputs)
        self._emit(context.trace_id, stage)
        return stage

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
        self._emit(context.trace_id, stage)

    def _emit(self, trace_id: str, stage: GovernedStage) -> None:
        payload = {"run_id": trace_id, **stage.to_dict()}
        if self.event_sink is not None:
            self.event_sink(trace_id, payload)
            return
        try:
            from backend.websocket import emit_trace_stage_update

            emit_trace_stage_update(trace_id, payload)
        except Exception:
            pass

    @staticmethod
    def _apply_governance_decision(request: GovernedRequest, decision: Any) -> None:
        request.metadata["governance_flags"] = list(decision.governance_flags)
        request.metadata["estimated_request_tokens"] = decision.estimated_request_tokens
        if decision.prompt_template_key:
            request.metadata["prompt_template_key"] = decision.prompt_template_key
            request.metadata["prompt_template_version"] = decision.prompt_template_version
        if decision.routing_policy_name:
            request.metadata["routing_policy_name"] = decision.routing_policy_name
            request.metadata["routing_policy_version"] = decision.routing_policy_version
        if decision.allowed_provider_types:
            requested = set(request.metadata.get("allowed_provider_types") or ())
            request.metadata["allowed_provider_types"] = sorted(
                requested & decision.allowed_provider_types if requested else decision.allowed_provider_types
            )
        if decision.allowed_models:
            requested = set(request.metadata.get("allowed_models") or ())
            request.metadata["allowed_models"] = sorted(
                requested & decision.allowed_models if requested else decision.allowed_models
            )

    def _audit_success(self, context: GovernedContext, provider: Any, model: str, usage: dict[str, Any]) -> None:
        self.gateway._governance.record_audit_event(
            run_id=context.trace_id,
            user_id=context.request.user_id,
            api_key_id=context.request.api_key_id,
            provider=getattr(provider, "provider_type", "unknown"),
            model=model,
            model_version=getattr(provider, "api_version", None) or "unknown",
            governance_flags=context.request.metadata.get("governance_flags"),
            request_tokens_estimate=context.request.metadata.get("estimated_request_tokens"),
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            estimated_cost_usd=usage.get("estimated_cost_usd"),
            success=True,
            metadata={"timestamp": datetime.now(UTC).isoformat(), "contract_version": context.request.contract_version},
        )

    def _audit_failure(self, context: GovernedContext, code: str, message: str | None) -> None:
        self.gateway._governance.record_audit_event(
            run_id=context.trace_id,
            user_id=context.request.user_id,
            api_key_id=context.request.api_key_id,
            provider=context.request.metadata.get("last_provider_used") or context.request.provider,
            model=context.request.metadata.get("last_model_used") or context.request.model or "unknown",
            model_version="unknown",
            governance_flags=context.request.metadata.get("governance_flags"),
            request_tokens_estimate=context.request.metadata.get("estimated_request_tokens"),
            success=False,
            error_code=code,
            error_message=message,
            metadata={"timestamp": datetime.now(UTC).isoformat(), "contract_version": context.request.contract_version},
        )

    @staticmethod
    def _metadata(context: GovernedContext, **extra: Any) -> dict[str, Any]:
        return {
            "contract_version": context.request.contract_version,
            "request_id": context.request.request_id,
            "source": context.request.source,
            "principal_kind": context.request.principal_kind,
            "dmrf": context.routing,
            "dsqp": context.dsqp,
            "truthcore": context.truthcore,
            "policy_decisions": context.policy_decisions,
            "provider_call_count": context.provider_call_count,
            "source_ids": [item.source_id for item in context.evidence],
            **extra,
        }

    @staticmethod
    def _cancel_requested(request: GovernedRequest) -> bool:
        value = request.metadata.get("cancel_requested")
        if callable(value):
            try:
                return bool(value())
            except Exception:
                return True
        return bool(value)

    @staticmethod
    def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))
