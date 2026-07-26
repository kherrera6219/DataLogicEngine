"""Transport-neutral L1-L10 stage executors for governed product requests.

The executors in this module transform the one shared
``GovernedReasoningState``. They never call an answer provider, persist a final
result, or create a second public request lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.governed_execution.contracts import (
    ConvergenceDecision,
    GovernedContext,
)
from backend.governed_execution.prompt import build_provider_messages
from backend.governed_execution.quality import (
    calculate_confidence,
    decide_convergence,
)
from backend.governed_execution.validation import validate_output

LAYER_NAMES = {
    "L1": "normalize_route",
    "L2": "retrieve_context",
    "L3": "evidence_plan",
    "L4": "persona_context",
    "L5": "candidate_plan",
    "L6": "evidence_validation",
    "L7": "reasoning_boundary",
    "L8": "trust_policy_gate",
    "L9": "convergence",
    "L10": "release_gate",
}


@dataclass(slots=True)
class LayerExecution:
    """Result returned to the owning orchestrator for one layer attempt."""

    ok: bool
    outputs: dict[str, Any]
    selected_ka_ids: list[str] = field(default_factory=list)
    ka_plan: dict[str, Any] = field(default_factory=dict)
    ka_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    effects: list[dict[str, Any]] = field(default_factory=list)
    error_code: str | None = None


class GovernedTenLayerStages:
    """Execute the ten reasoning stages without owning transport or storage."""

    def __init__(self, truthcore: Any):
        self.truthcore = truthcore

    async def l1(
        self,
        context: GovernedContext,
        *,
        tier: str,
        axis17_context: dict[str, Any],
    ) -> LayerExecution:
        coordinate_axes = (
            context.routing.get("axis_vector", {}).get("axes", {})
            if isinstance(context.routing.get("axis_vector"), dict)
            else {}
        )
        axis15 = (
            coordinate_axes.get("15")
            if isinstance(coordinate_axes, dict)
            else {}
        )
        risk_domain = (
            axis15.get("value")
            if isinstance(axis15, dict)
            else axis15
        ) or "standard"
        truthcore = await self.truthcore.execute(
            context.query,
            tier=tier,
            axis17_context=axis17_context,
            context={
                **context.request.metadata,
                "request_id": context.request.request_id,
                "trace_id": context.trace_id,
                "session_id": context.request.session_id,
                "principal_id": context.request.principal_id,
                "risk_domain": str(risk_domain),
                "evidence": [],
                "dsqp": {},
            },
            mode=context.request.mode.value,
        )
        context.truthcore = truthcore
        steps = [
            item
            for item in truthcore.get("steps_executed") or []
            if isinstance(item, dict)
        ]
        completed = [item for item in steps if item.get("status") == "completed"]
        selected_ids = [
            str(item.get("ka_id"))
            for item in completed
            if item.get("ka_id")
        ]
        ka_results = {
            str(item.get("ka_id")): dict(item)
            for item in completed
            if item.get("ka_id")
        }
        plan = (
            dict(truthcore.get("selection_plan"))
            if isinstance(truthcore.get("selection_plan"), dict)
            else self._stage_plan(
                "L1",
                selected_ids,
                "truthcore_compatibility_adapter",
            )
        )
        if not truthcore.get("ok"):
            return LayerExecution(
                ok=False,
                outputs={
                    "layer_id": "L1",
                    "decision": "block",
                    "truthcore": truthcore,
                },
                selected_ka_ids=selected_ids,
                ka_plan=plan,
                ka_results=ka_results,
                error_code="L1_KA_PLAN_FAILURE",
            )

        normalized_query = context.query
        adversarial_block = False
        for item in completed:
            output = item.get("output")
            if not isinstance(output, dict):
                continue
            if item.get("ka_id") == "KA-004":
                if output.get("is_valid") is False:
                    adversarial_block = True
                normalized_query = str(
                    output.get("normalized_query") or normalized_query
                ).strip()
            if item.get("ka_id") == "KA-061":
                adversarial_block = adversarial_block or bool(
                    output.get("blocked") or output.get("veto")
                )
                normalized_query = str(
                    output.get("sanitized_query") or normalized_query
                ).strip()
        if not normalized_query:
            adversarial_block = True

        context.query = normalized_query
        context.reasoning.query = normalized_query
        context.reasoning.coordinate_17 = dict(
            context.routing.get("axis_vector") or {}
        )
        context.reasoning.tier = tier
        decision = {
            "decision": "block" if adversarial_block else "allow",
            "reason": (
                "input_validation_or_adversarial_shield_block"
                if adversarial_block
                else "normalized_and_routed"
            ),
        }
        return LayerExecution(
            ok=not adversarial_block,
            outputs={
                "layer_id": "L1",
                "query": normalized_query,
                "tier": tier,
                "axis_vector": context.reasoning.coordinate_17,
                "selected_ka_ids": selected_ids,
                "decision": decision,
            },
            selected_ka_ids=selected_ids,
            ka_plan=plan,
            ka_results=ka_results,
            decisions=[decision],
            error_code="L1_INPUT_BLOCKED" if adversarial_block else None,
        )

    def l2(self, context: GovernedContext) -> LayerExecution:
        evidence_ids = [item.evidence_id for item in context.evidence]
        context.reasoning.evidence_ids = evidence_ids
        return LayerExecution(
            ok=True,
            outputs={
                "layer_id": "L2",
                "evidence_ids": evidence_ids,
                "source_ids": [item.source_id for item in context.evidence],
                "citation_labels": [
                    item.citation_label for item in context.evidence
                ],
                "retrieval_count": len(context.evidence),
                "similarity_is_source_quality": False,
            },
            ka_plan=self._stage_plan(
                "L2",
                [],
                "canonical_retrieval_and_graph_services",
            ),
        )

    def l3(self, context: GovernedContext) -> LayerExecution:
        retrieval_decisions = list(
            context.request.metadata.get("_retrieval_decisions") or []
        )
        evidence_disclosures = [
            {
                "evidence_id": item.evidence_id,
                "source_id": item.source_id,
                "source_type": item.source_type,
                "origin": item.source.origin if item.source else None,
            }
            for item in context.evidence
        ]
        return LayerExecution(
            ok=True,
            outputs={
                "layer_id": "L3",
                "acquisition_mode": "bounded_local_retrieval",
                "external_research_authorized": False,
                "provider_or_connector_disclosure": evidence_disclosures,
                "retrieval_decisions": retrieval_decisions,
                "evidence_budget_used": len(context.evidence),
            },
            ka_plan=self._stage_plan(
                "L3",
                [],
                "governed_retrieval_decisions",
            ),
            decisions=retrieval_decisions,
        )

    def l4(self, context: GovernedContext) -> LayerExecution:
        profiles = (
            context.dsqp.get("profiles")
            if isinstance(context.dsqp.get("profiles"), dict)
            else {}
        )
        context.reasoning.dsqp_profiles = dict(profiles)
        expected = {"8", "9", "10", "11"}
        present = set(profiles)
        ok = expected.issubset(present) and not context.dsqp.get("partial")
        return LayerExecution(
            ok=ok,
            outputs={
                "layer_id": "L4",
                "expected_axes": sorted(expected),
                "constructed_axes": sorted(present),
                "profile_ids": [
                    profile.get("persona_id")
                    for profile in profiles.values()
                    if isinstance(profile, dict)
                ],
                "construction_mode": "deterministic",
            },
            ka_plan=self._stage_plan(
                "L4",
                [],
                "canonical_dsqp_profile_constructor",
            ),
            error_code="L4_PERSONA_CONTEXT_FAILURE" if not ok else None,
        )

    def l5(self, context: GovernedContext) -> LayerExecution:
        context.provider_messages = build_provider_messages(context)
        system_text = str(
            context.provider_messages[0].get("content") or ""
        )
        completed_kas = [
            str(item.get("ka_id"))
            for item in context.truthcore.get("steps_executed") or []
            if isinstance(item, dict)
            and item.get("status") == "completed"
            and item.get("ka_id")
        ]
        ok = bool(context.provider_messages) and bool(context.query)
        return LayerExecution(
            ok=ok,
            outputs={
                "layer_id": "L5",
                "message_count": len(context.provider_messages),
                "contains_source_ids": all(
                    item.source_id in system_text for item in context.evidence
                ),
                "contains_dsqp": (
                    "Deterministic persona context" in system_text
                ),
                "contains_ka_results": (
                    "Executed TruthCore/KA context" in system_text
                ),
                "selected_ka_ids": completed_kas,
                "dissent_resolution": "deferred_to_cp19_f_persona_qualification",
            },
            selected_ka_ids=completed_kas,
            ka_plan=self._stage_plan(
                "L5",
                completed_kas,
                "canonical_prompt_plan",
            ),
            error_code="L5_CANDIDATE_PLAN_FAILURE" if not ok else None,
        )

    def l6(
        self,
        context: GovernedContext,
        *,
        answer: str,
        governance_engine: Any,
    ) -> tuple[LayerExecution, dict[str, Any]]:
        validation = validate_output(
            answer,
            context.evidence,
            mode=context.request.mode,
            governance_engine=governance_engine,
        )
        context.claims = validation.pop("claims")
        context.citations = validation.pop("citations")
        context.validators = validation.pop("validators")
        context.confidence_measurement = calculate_confidence(
            context.claims,
            context.evidence,
            context.validators,
        )
        context.reasoning.candidate = str(validation.get("answer") or answer)
        context.reasoning.claims = [
            claim.to_dict() for claim in context.claims
        ]
        context.reasoning.validators = [
            validator.to_dict() for validator in context.validators
        ]
        context.reasoning.confidence_measurement = (
            context.confidence_measurement.to_dict()
        )
        context.warnings.extend(validation.get("warnings") or [])
        return (
            LayerExecution(
                ok=bool(validation["ok"]),
                outputs={
                    "layer_id": "L6",
                    **validation,
                    "confidence_measurement": (
                        context.confidence_measurement.to_dict()
                    ),
                },
                ka_plan=self._stage_plan(
                    "L6",
                    [],
                    "canonical_evidence_and_confidence_policy",
                ),
                decisions=[
                    {
                        "decision": (
                            "allow" if validation["ok"] else "block"
                        ),
                        "validation_score": validation["validation_score"],
                    }
                ],
                error_code=(
                    "L6_OUTPUT_VALIDATION_FAILURE"
                    if not validation["ok"]
                    else None
                ),
            ),
            validation,
        )

    def l7(self, context: GovernedContext) -> LayerExecution:
        dependency_map = {
            claim.claim_id: list(claim.evidence_ids)
            for claim in context.claims
        }
        missing_boundaries = [
            claim.claim_id
            for claim in context.claims
            if claim.status in {"insufficient", "contradicted"}
        ]
        return LayerExecution(
            ok=True,
            outputs={
                "layer_id": "L7",
                "claim_dependency_map": dependency_map,
                "causal_inference_status": "not_measured",
                "counterfactual_status": "not_applicable",
                "planning_status": "bounded",
                "reasoning_boundary": "available_evidence_and_declared_context",
                "boundary_findings": missing_boundaries,
                "external_truth_claimed": False,
            },
            ka_plan=self._stage_plan(
                "L7",
                [],
                "canonical_reasoning_boundary_checks",
            ),
        )

    def l8(self, context: GovernedContext) -> LayerExecution:
        blocking = [
            validator.validator_id
            for validator in context.validators
            if validator.status in {"failed", "blocked"}
        ]
        policy_blocks = [
            decision
            for decision in context.policy_decisions
            if decision.get("decision") == "block"
        ]
        ok = not blocking and not policy_blocks
        decision = {
            "decision": "allow" if ok else "block",
            "blocking_validator_ids": blocking,
            "blocking_policy_count": len(policy_blocks),
        }
        return LayerExecution(
            ok=ok,
            outputs={
                "layer_id": "L8",
                "trust_policy_decision": decision,
                "risk_class": (
                    ((context.reasoning.coordinate_17.get("axes") or {}).get("15") or {}).get("value")
                    if isinstance(context.reasoning.coordinate_17, dict)
                    else None
                ),
                "privacy_security_compliance": "governance_and_output_controls_applied",
            },
            ka_plan=self._stage_plan(
                "L8",
                [],
                "canonical_governance_and_output_controls",
            ),
            decisions=[decision],
            error_code="L8_TRUST_POLICY_BLOCK" if not ok else None,
        )

    def l9(
        self,
        context: GovernedContext,
        *,
        tier: str,
        iteration: int,
        max_iterations: int,
        requires_evidence: bool,
    ) -> tuple[LayerExecution, ConvergenceDecision]:
        convergence = decide_convergence(
            context.claims,
            context.validators,
            context.confidence_measurement,
            mode=context.request.mode,
            tier=tier,
            iteration=iteration,
            max_iterations=max_iterations,
            requires_evidence=requires_evidence,
        )
        context.convergence_decisions.append(convergence)
        context.reasoning.convergence = convergence.to_dict()
        ok = convergence.action != "block"
        return (
            LayerExecution(
                ok=ok,
                outputs={
                    "layer_id": "L9",
                    "trace_consistency": "consistent",
                    "persona_agreement": "not_measured",
                    "drift_status": "not_measured",
                    "convergence": convergence.to_dict(),
                },
                ka_plan=self._stage_plan(
                    "L9",
                    [],
                    "canonical_bounded_convergence_policy",
                ),
                decisions=[convergence.to_dict()],
                error_code="L9_CONVERGENCE_BLOCK" if not ok else None,
            ),
            convergence,
        )

    def l10(
        self,
        context: GovernedContext,
        *,
        final_action: str,
    ) -> LayerExecution:
        release = final_action in {"finalize", "abstain", "local_review"}
        decision = {
            "decision": "release" if release else "halt",
            "final_action": final_action,
            "candidate_present": context.reasoning.candidate is not None,
            "control_set": "cp19_d_transitional_release",
            "full_l9_l10_ka_qualification_checkpoint": "CP19-E",
        }
        context.reasoning.release = decision
        return LayerExecution(
            ok=release,
            outputs={
                "layer_id": "L10",
                "release": decision,
                "effects_applied": False,
                "validated_memory_commit": "not_requested",
            },
            ka_plan=self._stage_plan(
                "L10",
                [],
                "canonical_release_boundary",
            ),
            decisions=[decision],
            error_code="L10_RELEASE_BLOCK" if not release else None,
        )

    @staticmethod
    def _stage_plan(
        layer_id: str,
        selected_ids: list[str],
        owner: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": "dle.ka-stage-plan.v1",
            "layer_id": layer_id,
            "selected_ids": list(selected_ids),
            "executor_owner": owner,
            "selection_state": (
                "selected_and_executed"
                if selected_ids
                else "no_production_qualified_ka_required"
            ),
            "effects_authorized": False,
        }
