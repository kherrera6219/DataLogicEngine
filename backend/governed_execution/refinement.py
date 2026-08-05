"""Canonical manifest-defined 12-step post-candidate refinement workflow.

This module owns no provider, persistence, memory, graph, or release authority.
It consumes committed governed state, executes only production-admitted KAs
through the canonical selector/DAG, and returns constraints for at most one
orchestrator-owned provider rewrite.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Any

from backend.governed_execution.contracts import (
    ConvergenceDecision,
    GovernedContext,
    GovernedStageStatus,
)
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
    KAPlanExecutionStatus,
    KAPlanExecutor,
    KASelectionRequest,
    KATraceState,
    ManifestKASelector,
)


class RefinementStepStatus(StrEnum):
    EXECUTED = "executed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass(slots=True)
class RefinementStepRecord:
    step: int
    step_id: str
    name: str
    status: RefinementStepStatus
    reason: str
    candidate_ka_ids: list[str] = field(default_factory=list)
    selected_ka_ids: list[str] = field(default_factory=list)
    executed_ka_ids: list[str] = field(default_factory=list)
    reused_ka_ids: list[str] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    ka_plan: dict[str, Any] = field(default_factory=dict)
    ka_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    effects: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(slots=True)
class CanonicalRefinementResult:
    registry_version: str
    status: str
    steps: list[RefinementStepRecord]
    rewrite_authorized: bool
    rewrite_constraints: list[str]
    provider_subcalls_used: int
    max_provider_rewrites: int
    effects: list[dict[str, Any]]
    blocked_by_step: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "dle.canonical-refinement-result.v1",
            "registry_version": self.registry_version,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "step_count": len(self.steps),
            "step_status_counts": {
                status.value: sum(step.status is status for step in self.steps)
                for status in RefinementStepStatus
            },
            "rewrite_authorized": self.rewrite_authorized,
            "rewrite_constraints": list(self.rewrite_constraints),
            "provider_subcalls_used": self.provider_subcalls_used,
            "max_provider_rewrites": self.max_provider_rewrites,
            "effects": list(self.effects),
            "blocked_by_step": self.blocked_by_step,
        }


class CanonicalRefinementWorkflow:
    """Execute the one versioned 12-step refinement registry."""

    def __init__(
        self,
        *,
        ka_controller: CanonicalKAController | None = None,
    ) -> None:
        self.ka_controller = ka_controller or get_ka_controller()
        self.ka_selector = ManifestKASelector(self.ka_controller.manifest)
        self.ka_executor = KAPlanExecutor(self.ka_controller)
        registry = self.ka_controller.manifest.authority.get("refinement_workflow")
        if not isinstance(registry, dict):
            raise TypeError("Canonical refinement registry is missing")
        steps = registry.get("steps")
        if not isinstance(steps, list) or len(steps) != 12:
            raise ValueError("Canonical refinement registry must contain 12 steps")
        ordered = sorted(steps, key=lambda item: int(item.get("step") or 0))
        step_numbers = [int(item.get("step") or 0) for item in ordered]
        step_ids = [str(item.get("step_id") or "") for item in ordered]
        if step_numbers != list(range(1, 13)) or len(set(step_ids)) != 12:
            raise ValueError("Canonical refinement registry order/IDs are invalid")
        self.registry = registry
        self.steps = ordered

    async def execute(
        self,
        context: GovernedContext,
        *,
        prior_answer: str,
        decision: ConvergenceDecision,
    ) -> CanonicalRefinementResult:
        """Collect all step findings before authorizing one provider rewrite."""

        records: list[RefinementStepRecord] = []
        constraints: list[str] = []
        effects: list[dict[str, Any]] = []
        blocked_by: str | None = None

        for spec in self.steps:
            if blocked_by is not None:
                record = self._record(
                    spec,
                    RefinementStepStatus.SKIPPED,
                    f"workflow_blocked_by:{blocked_by}",
                )
            else:
                try:
                    record = await self._execute_step(
                        spec,
                        context=context,
                        prior_answer=prior_answer,
                        decision=decision,
                        prior_constraints=constraints,
                    )
                except Exception as exc:  # noqa: BLE001 - typed workflow boundary
                    record = self._record(
                        spec,
                        RefinementStepStatus.FAILED,
                        f"step_execution_error:{type(exc).__name__}",
                    )
            records.append(record)
            constraints.extend(record.constraints)
            effects.extend(record.effects)
            if record.status in {
                RefinementStepStatus.BLOCKED,
                RefinementStepStatus.FAILED,
            }:
                blocked_by = record.step_id

        constraints = list(dict.fromkeys(item for item in constraints if item))
        completed = (
            blocked_by is None
            and len(records) == 12
            and all(
                record.status
                in {
                    RefinementStepStatus.EXECUTED,
                    RefinementStepStatus.SKIPPED,
                }
                for record in records
            )
        )
        rewrite_authorized = completed and decision.action == "refine"
        result = CanonicalRefinementResult(
            registry_version=str(self.registry["registry_version"]),
            status="completed" if completed else "blocked",
            steps=records,
            rewrite_authorized=rewrite_authorized,
            rewrite_constraints=constraints,
            provider_subcalls_used=0,
            max_provider_rewrites=int(self.registry.get("max_provider_rewrites") or 0),
            effects=effects,
            blocked_by_step=blocked_by,
        )
        context.reasoning.refinement = result.to_dict()
        if effects:
            context.reasoning.effects.extend(effects)
        return result

    async def _execute_step(
        self,
        spec: dict[str, Any],
        *,
        context: GovernedContext,
        prior_answer: str,
        decision: ConvergenceDecision,
        prior_constraints: list[str],
    ) -> RefinementStepRecord:
        step_id = str(spec["step_id"])
        handlers = {
            "structured_decomposition": self._structured_decomposition,
            "alternative_branches": self._alternative_branches,
            "missing_information": self._missing_information,
            "input_source_evidence_validation": self._evidence_validation,
            "deep_causal_analytical_review": self._deep_review,
            "self_critique_contradiction_review": self._self_critique,
            "policy_safety_review": self._policy_review,
            "recursive_learning_decision": self._recursion_decision,
            "semantic_intent_alignment": self._semantic_alignment,
            "authorized_external_validation": self._external_validation,
            "synthesis_measured_scoring": self._synthesis,
            "memory_lifecycle_proposal": self._lifecycle_proposal,
        }
        return await handlers[step_id](
            spec=spec,
            context=context,
            prior_answer=prior_answer,
            decision=decision,
            prior_constraints=prior_constraints,
        )

    async def _structured_decomposition(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        committed = self._committed_ka_ids(context)
        if "KA-001" in committed:
            return self._record(
                spec,
                RefinementStepStatus.EXECUTED,
                "committed_ka_result_reused",
                reused_ka_ids=["KA-001"],
                findings=[
                    {
                        "type": "structured_decomposition",
                        "source": "committed_governed_layer",
                    }
                ],
            )
        return await self._execute_required(
            spec,
            context,
            ["KA-001"],
            {
                "KA-001": {"query": context.query},
                "KA-004": {"query": context.query},
            },
        )

    async def _alternative_branches(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        admitted = [
            canonical_id
            for canonical_id in spec["candidate_ka_ids"]
            if self.ka_controller.manifest.entries[
                canonical_id
            ].admission.production_enabled
        ]
        if not admitted:
            return self._record(
                spec,
                RefinementStepStatus.SKIPPED,
                "alternative_branch_ka_not_production_qualified",
                constraints=[
                    "Do not create unaccounted provider branches during refinement."
                ],
            )
        return await self._execute_required(
            spec,
            context,
            admitted,
            {
                canonical_id: {
                    "initial_state": context.reasoning.candidate or context.query,
                    "goal": context.query,
                }
                for canonical_id in admitted
            },
        )

    async def _missing_information(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        decision: ConvergenceDecision,
        **_: Any,
    ) -> RefinementStepRecord:
        current_state = {
            "unsupported_claim_ids": sorted(decision.unsupported_claim_ids),
            "contradicted_claim_ids": sorted(decision.contradicted_claim_ids),
            "failed_validator_ids": sorted(decision.failed_validator_ids),
        }
        record = await self._execute_required(
            spec,
            context,
            ["KA-003"],
            {
                "KA-003": {
                    "current_state": current_state,
                    "desired_state": {
                        "unsupported_claim_ids": [],
                        "contradicted_claim_ids": [],
                        "failed_validator_ids": [],
                    },
                }
            },
        )
        record.constraints.extend(
            [
                f"Remove or explicitly qualify unsupported claim {claim_id}."
                for claim_id in decision.unsupported_claim_ids
            ]
        )
        record.constraints.extend(
            [
                f"Do not release contradicted claim {claim_id} as fact."
                for claim_id in decision.contradicted_claim_ids
            ]
        )
        return record

    async def _evidence_validation(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        l6 = self._layer(context, "L6", iteration=0)
        if l6 is None:
            return self._record(
                spec,
                RefinementStepStatus.BLOCKED,
                "committed_l6_validation_missing",
            )
        labels = sorted(item.citation_label for item in context.evidence)
        findings = [
            {
                "type": "committed_evidence_validation",
                "evidence_count": len(context.evidence),
                "validator_count": len(context.validators),
                "known_citation_labels": labels,
            }
        ]
        constraints = [
            (
                "Use only these known citation labels: " + ", ".join(labels)
                if labels
                else "Do not invent citations; no evidence label is available."
            )
        ]
        return self._record(
            spec,
            RefinementStepStatus.EXECUTED,
            "committed_l1_l6_validation_consumed",
            reused_ka_ids=sorted(
                self._committed_ka_ids(context) & {"KA-004", "KA-009", "KA-018"}
            ),
            findings=findings,
            constraints=constraints,
        )

    async def _deep_review(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        nodes = [
            {
                "id": evidence.evidence_id,
                "type": "evidence",
                "deps": [],
            }
            for evidence in context.evidence
            if evidence.evidence_id
        ]
        nodes.extend(
            {
                "id": claim.claim_id,
                "type": "claim",
                "deps": list(claim.evidence_ids),
            }
            for claim in context.claims
        )
        record = await self._execute_required(
            spec,
            context,
            ["KA-011", "KA-025"],
            {
                "KA-011": {
                    "data": [
                        {
                            "claim_id": claim.claim_id,
                            "status": claim.status,
                            "evidence_ids": list(claim.evidence_ids),
                        }
                        for claim in context.claims
                    ],
                    "model_type": "structural",
                },
                "KA-025": {"nodes": nodes},
            },
        )
        dependency = (
            record.ka_results.get("KA-025", {}).get("output", {}).get("meta", {})
        )
        if dependency.get("is_dag") is False:
            record.status = RefinementStepStatus.BLOCKED
            record.reason = "claim_dependency_cycle_detected"
            record.constraints.append(
                "Do not rewrite across a cyclic claim dependency graph."
            )
        return record

    async def _self_critique(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        l9 = self._layer(context, "L9", iteration=0)
        if l9 is None:
            return self._record(
                spec,
                RefinementStepStatus.BLOCKED,
                "committed_l9_meta_evaluation_missing",
            )
        failed = [
            validator.validator_id
            for validator in context.validators
            if validator.status in {"failed", "blocked"}
        ]
        constraints = [
            f"Resolve validator finding {validator_id}." for validator_id in failed
        ]
        return self._record(
            spec,
            RefinementStepStatus.EXECUTED,
            "committed_contradiction_and_meta_evaluation_consumed",
            reused_ka_ids=sorted(
                self._committed_ka_ids(context) & {"KA-026", "L9-KA-004"}
            ),
            findings=[
                {
                    "type": "validator_self_critique",
                    "failed_validator_ids": failed,
                }
            ],
            constraints=constraints,
        )

    async def _policy_review(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        l8 = self._layer(context, "L8", iteration=0)
        if l8 is None or l8.status is not GovernedStageStatus.COMPLETED:
            return self._record(
                spec,
                RefinementStepStatus.BLOCKED,
                "committed_l8_policy_gate_missing",
            )
        decision = l8.outputs.get("trust_policy_decision") or {}
        if decision.get("decision") != "allow":
            return self._record(
                spec,
                RefinementStepStatus.BLOCKED,
                "committed_l8_policy_gate_blocked",
                findings=[dict(decision)],
            )
        return self._record(
            spec,
            RefinementStepStatus.EXECUTED,
            "committed_l8_constraints_consumed_l10_deferred",
            reused_ka_ids=sorted(
                self._committed_ka_ids(context) & {"KA-024", "L10-KA-003", "L10-KA-004"}
            ),
            findings=[dict(decision)],
            constraints=[
                "Preserve all L8 policy, privacy, security, risk, and compliance constraints."
            ],
        )

    async def _recursion_decision(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        decision: ConvergenceDecision,
        **_: Any,
    ) -> RefinementStepRecord:
        l9 = self._layer(context, "L9", iteration=0)
        required = {"L9-KA-005", "L9-KA-006", "L9-KA-007"}
        committed = self._committed_ka_ids(context)
        if l9 is None or not required.issubset(committed):
            return self._record(
                spec,
                RefinementStepStatus.BLOCKED,
                "committed_l9_recursion_suite_missing",
                reused_ka_ids=sorted(required & committed),
            )
        if decision.action != "refine" or decision.iteration != 0:
            return self._record(
                spec,
                RefinementStepStatus.BLOCKED,
                "l9_did_not_authorize_initial_refinement",
                reused_ka_ids=sorted(required),
            )
        return self._record(
            spec,
            RefinementStepStatus.EXECUTED,
            "committed_l9_refinement_decision_consumed",
            reused_ka_ids=sorted(required),
            findings=[decision.to_dict()],
            constraints=[
                "Perform at most one provider rewrite and do not start another refinement cycle."
            ],
        )

    async def _semantic_alignment(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        record = await self._execute_required(
            spec,
            context,
            ["KA-005"],
            {
                "KA-004": {"query": context.query},
                "KA-005": {"query": context.query},
            },
        )
        persona = context.dsqp.get("persona_synthesis")
        conflict = (
            persona.get("conflict_resolution")
            if isinstance(persona, dict)
            and isinstance(persona.get("conflict_resolution"), dict)
            else {}
        )
        record.reused_ka_ids = sorted(
            self._committed_ka_ids(context) & {"KA-012", "KA-013", "KA-030"}
        )
        record.constraints.extend(
            str(item)
            for item in conflict.get("prompt_constraints") or []
            if str(item).strip()
        )
        return record

    async def _external_validation(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        authorized = bool(
            context.request.metadata.get("external_refinement_validation_authorized")
        )
        candidate_id = str(spec["candidate_ka_ids"][0])
        qualified = self.ka_controller.manifest.entries[
            candidate_id
        ].admission.production_enabled
        reason = (
            "external_validation_not_authorized"
            if not authorized
            else "external_validation_service_not_production_qualified"
            if not qualified
            else "external_validation_owned_by_cp19_i_service_port"
        )
        return self._record(
            spec,
            RefinementStepStatus.SKIPPED,
            reason,
            constraints=[
                "Do not claim external validation that was not executed through an authorized service."
            ],
        )

    async def _synthesis(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        prior_constraints: list[str],
        **_: Any,
    ) -> RefinementStepRecord:
        confidence = (
            context.confidence_measurement.to_dict()
            if context.confidence_measurement
            else None
        )
        return self._record(
            spec,
            RefinementStepStatus.EXECUTED,
            "committed_synthesis_and_measurements_consumed",
            reused_ka_ids=sorted(
                self._committed_ka_ids(context) & {"KA-030", "L9-KA-006"}
            ),
            findings=[
                {
                    "type": "measured_synthesis",
                    "confidence_measurement": confidence,
                    "constraint_count": len(set(prior_constraints)),
                }
            ],
            constraints=[
                "Revise only the measured defects and preserve supported content."
            ],
        )

    async def _lifecycle_proposal(
        self,
        *,
        spec: dict[str, Any],
        context: GovernedContext,
        **_: Any,
    ) -> RefinementStepRecord:
        proposal = {
            "schema_version": "dle.effect-proposal.v1",
            "proposal_id": "proposal_"
            + sha256(
                f"{context.trace_id}:cp19g-refinement-lifecycle".encode()
            ).hexdigest()[:16],
            "effect_class": "memory_lifecycle",
            "action": "consider_post_release_refinement_trace",
            "applied": False,
            "receipt": None,
            "authorization": "requires_l10_release_and_authoritative_service",
        }
        return self._record(
            spec,
            RefinementStepStatus.EXECUTED,
            "proposal_created_effect_not_applied",
            effects=[proposal],
            findings=[
                {
                    "type": "lifecycle_proposal",
                    "applied": False,
                    "receipt_present": False,
                }
            ],
        )

    async def _execute_required(
        self,
        spec: dict[str, Any],
        context: GovernedContext,
        requested_ids: list[str],
        ka_inputs: dict[str, dict[str, Any]],
    ) -> RefinementStepRecord:
        request = self._selection_request(
            context,
            requested_ids=requested_ids,
            ka_inputs=ka_inputs,
        )
        plan = self.ka_selector.plan(request)
        if not plan.valid:
            return self._record(
                spec,
                RefinementStepStatus.BLOCKED,
                "required_refinement_plan_invalid",
                selected_ka_ids=list(plan.selected_ids),
                ka_plan=self._plan_summary(plan),
                findings=[
                    {
                        "type": "plan_validation_failure",
                        "errors": list(plan.validation_errors),
                    }
                ],
            )
        report = await self.ka_executor.execute(plan, request)
        executed_ids = sorted(
            canonical_id
            for canonical_id, trace in report.traces.items()
            if any(event.state is KATraceState.EXECUTED for event in trace.events)
        )
        ka_results = {
            canonical_id: result.model_dump(mode="json", exclude_none=True)
            for canonical_id, result in report.results.items()
            if canonical_id in executed_ids
        }
        for canonical_id in executed_ids:
            context.ka_result_cache[canonical_id] = report.results[canonical_id]
        required_complete = report.status is KAPlanExecutionStatus.SUCCEEDED and set(
            requested_ids
        ).issubset(executed_ids)
        return self._record(
            spec,
            (
                RefinementStepStatus.EXECUTED
                if required_complete
                else RefinementStepStatus.BLOCKED
            ),
            (
                "required_refinement_kas_executed"
                if required_complete
                else "required_refinement_ka_failed"
            ),
            selected_ka_ids=list(plan.selected_ids),
            executed_ka_ids=executed_ids,
            ka_plan=self._plan_summary(plan, report),
            ka_results=ka_results,
        )

    def _selection_request(
        self,
        context: GovernedContext,
        *,
        requested_ids: list[str],
        ka_inputs: dict[str, dict[str, Any]],
    ) -> KASelectionRequest:
        remaining_ms = 10_000
        if context.deadline_at_monotonic is not None:
            remaining_ms = max(
                1,
                int((context.deadline_at_monotonic - time.monotonic()) * 1000),
            )
        return KASelectionRequest(
            requested_ids=requested_ids,
            ka_inputs=ka_inputs,
            service_capabilities={"governed_execution_service"},
            mode=KAExecutionMode.PRODUCTION,
            context=KAExecutionContext(
                request_id=context.request.request_id,
                run_id=context.trace_id,
                session_id=context.request.session_id,
                principal_id=context.request.principal_id,
                workflow="governed.v1.refinement",
                tier=context.reasoning.tier or "standard",
                layer="R12",
                budget=KABudget(
                    deadline_ms=min(remaining_ms, 10_000),
                    max_dependency_executions=8,
                    max_recursion_depth=4,
                    max_selected_algorithms=8,
                    max_fan_out=4,
                    max_parallelism=2,
                    max_input_bytes=1_000_000,
                    max_output_bytes=5_000_000,
                    max_provider_calls=0,
                    max_effects=1,
                ),
            ),
        )

    @staticmethod
    def _record(
        spec: dict[str, Any],
        status: RefinementStepStatus,
        reason: str,
        **kwargs: Any,
    ) -> RefinementStepRecord:
        return RefinementStepRecord(
            step=int(spec["step"]),
            step_id=str(spec["step_id"]),
            name=str(spec["name"]),
            status=status,
            reason=reason,
            candidate_ka_ids=list(spec.get("candidate_ka_ids") or []),
            **kwargs,
        )

    @staticmethod
    def _layer(
        context: GovernedContext,
        layer_id: str,
        *,
        iteration: int,
    ) -> Any | None:
        return next(
            (
                layer
                for layer in reversed(context.reasoning.layers)
                if layer.layer_id == layer_id and layer.iteration == iteration
            ),
            None,
        )

    @staticmethod
    def _committed_ka_ids(context: GovernedContext) -> set[str]:
        return {
            canonical_id
            for layer in context.reasoning.layers
            if layer.status is GovernedStageStatus.COMPLETED
            for canonical_id in layer.ka_results
        }

    @staticmethod
    def _plan_summary(
        plan: Any,
        report: Any | None = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": "dle.ka-stage-plan.v1",
            "plan_id": plan.plan_id,
            "manifest_version": plan.manifest_version,
            "selected_ids": list(plan.selected_ids),
            "execution_order": list(plan.execution_order),
            "selection_state": (
                report.status.value if report is not None else "planned"
            ),
            "required_failure": (
                report.required_failure if report is not None else None
            ),
            "effects_authorized": False,
        }
