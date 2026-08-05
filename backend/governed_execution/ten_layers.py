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
    GovernedPolicyDecision,
)
from backend.governed_execution.prompt import build_provider_messages
from backend.governed_execution.quality import (
    calculate_confidence,
    decide_convergence,
)
from backend.governed_execution.validation import validate_output
from backend.knowledge_algorithms.contracts import (
    KABudget,
    KAExecutionContext,
    KAExecutionMode,
)
from backend.knowledge_algorithms.controller import (
    CanonicalKAController,
    get_ka_controller,
)
from backend.knowledge_algorithms.l10.l10_ka_003_pii_redactor import (
    PII_PATTERNS,
)
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionStatus,
    KAPlanExecutor,
    KASelectionPlan,
    KASelectionRequest,
    KATraceState,
    ManifestKASelector,
)

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

    def __init__(
        self,
        truthcore: Any,
        *,
        ka_controller: CanonicalKAController | None = None,
    ):
        self.truthcore = truthcore
        self.ka_controller = ka_controller or get_ka_controller()
        self.ka_selector = ManifestKASelector(self.ka_controller.manifest)
        self.ka_executor = KAPlanExecutor(self.ka_controller)

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
        axis15 = coordinate_axes.get("15") if isinstance(coordinate_axes, dict) else {}
        risk_domain = (
            axis15.get("value") if isinstance(axis15, dict) else axis15
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
            str(item.get("ka_id")) for item in completed if item.get("ka_id")
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
        context.reasoning.coordinate_17 = dict(context.routing.get("axis_vector") or {})
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
                "citation_labels": [item.citation_label for item in context.evidence],
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

    async def l4(self, context: GovernedContext) -> LayerExecution:
        profiles = (
            context.dsqp.get("profiles")
            if isinstance(context.dsqp.get("profiles"), dict)
            else {}
        )
        context.reasoning.dsqp_profiles = dict(profiles)
        expected = {"8", "9", "10", "11"}
        present = set(profiles)
        profiles_by_type = self._persona_profiles_by_type(profiles)
        expected_personas = {"knowledge", "sector", "regulatory", "compliance"}
        profiles_complete = (
            expected.issubset(present)
            and expected_personas == set(profiles_by_type)
            and not context.dsqp.get("partial")
            and all(
                isinstance(profile.get("validation"), dict)
                and profile["validation"].get("valid") is True
                for profile in profiles_by_type.values()
            )
        )
        if not profiles_complete:
            return LayerExecution(
                ok=False,
                outputs={
                    "layer_id": "L4",
                    "expected_axes": sorted(expected),
                    "constructed_axes": sorted(present),
                    "expected_personas": sorted(expected_personas),
                    "constructed_personas": sorted(profiles_by_type),
                },
                ka_plan=self._stage_plan(
                    "L4",
                    [],
                    "canonical_dsqp_profile_constructor",
                ),
                error_code="L4_PERSONA_CONTEXT_FAILURE",
            )

        request = self._selection_request(
            context,
            layer_id="L4",
            tier=context.reasoning.tier or "standard",
            requested_ids=["KA-012", "KA-028"],
            ka_inputs={
                "KA-012": {
                    "query": context.query,
                    "active_personas": sorted(expected_personas),
                    "context": {
                        "trace_id": context.trace_id,
                        "evidence_ids": list(context.reasoning.evidence_ids),
                        "coordinate_17": dict(context.reasoning.coordinate_17),
                        "provider_subcall_budget": 0,
                    },
                    "dsqp_profiles": profiles_by_type,
                },
                "KA-028": {
                    "query": context.query,
                    "context": {
                        "trace_id": context.trace_id,
                        "evidence_ids": list(context.reasoning.evidence_ids),
                    },
                    "existing_personas": sorted(expected_personas),
                    "limit": 2,
                },
            },
            service_capabilities={"persona_context_service"},
        )
        plan = self.ka_selector.plan(request)
        report = await self.ka_executor.execute(plan, request)
        executed_ids = self._executed_ids(report)
        ka_results = self._committed_results(report, executed_ids)
        analysis_result = ka_results.get("KA-012", {}).get("output", {})
        expansion_result = ka_results.get("KA-028", {}).get("output", {})
        findings = analysis_result.get("persona_findings") or []
        observed_personas = {
            str(item.get("persona_type"))
            for item in findings
            if isinstance(item, dict) and item.get("persona_type")
        }
        complete = (
            report.status is KAPlanExecutionStatus.SUCCEEDED
            and set(executed_ids) == {"KA-012", "KA-028"}
            and expected_personas == observed_personas
            and analysis_result.get("provider_subcalls_used") == 0
            and analysis_result.get("provider_subcall_budget") == 0
        )
        if complete:
            for canonical_id in ("KA-012", "KA-028"):
                context.ka_result_cache[canonical_id] = report.results[canonical_id]
            context.dsqp["persona_analysis"] = analysis_result
            context.dsqp["persona_expansion"] = expansion_result
        effects = (
            [
                {
                    "ka_id": canonical_id,
                    "state": "proposal_only",
                    "effect_port": "persona_context_service",
                    "applied": False,
                    "receipt": None,
                }
                for canonical_id in ("KA-012", "KA-028")
            ]
            if complete
            else []
        )
        return LayerExecution(
            ok=complete,
            outputs={
                "layer_id": "L4",
                "expected_axes": sorted(expected),
                "constructed_axes": sorted(present),
                "expected_personas": sorted(expected_personas),
                "constructed_personas": sorted(observed_personas),
                "profile_ids": [
                    profile.get("persona_id")
                    for profile in profiles.values()
                    if isinstance(profile, dict)
                ],
                "construction_mode": "deterministic",
                "persona_finding_count": len(findings),
                "constraint_count": len(analysis_result.get("constraints") or []),
                "objection_count": len(analysis_result.get("objections") or []),
                "additional_perspective_count": expansion_result.get("count"),
                "additional_perspective_ids": expansion_result.get("selection_order"),
                "provider_subcalls_used": (
                    analysis_result.get("provider_subcalls_used")
                ),
                "child_trace_ids": self._child_trace_ids(
                    report,
                    executed_ids,
                ),
            },
            selected_ka_ids=executed_ids,
            ka_plan=self._plan_summary(plan, report),
            ka_results=ka_results,
            decisions=[
                {
                    "decision": (
                        "persona_analysis_committed"
                        if complete
                        else "persona_analysis_blocked"
                    ),
                    "provider_subcall_budget": 0,
                }
            ],
            effects=effects,
            error_code=("L4_PERSONA_KA_FAILURE" if not complete else None),
        )

    async def l5(self, context: GovernedContext) -> LayerExecution:
        prior = context.ka_result_cache.get("KA-012")
        expansion_prior = context.ka_result_cache.get("KA-028")
        analysis = context.dsqp.get("persona_analysis")
        if prior is None or expansion_prior is None or not isinstance(analysis, dict):
            return LayerExecution(
                ok=False,
                outputs={
                    "layer_id": "L5",
                    "reason": "committed_persona_analysis_missing",
                },
                ka_plan=self._stage_plan(
                    "L5",
                    [],
                    "canonical_persona_synthesis",
                ),
                error_code="L5_PERSONA_ANALYSIS_MISSING",
            )
        expected_personas = ["knowledge", "sector", "regulatory", "compliance"]
        domain = self._persona_domain(context)
        request = self._selection_request(
            context,
            layer_id="L5",
            tier=context.reasoning.tier or "standard",
            requested_ids=["KA-013", "KA-030", "KA-038"],
            ka_inputs={
                "KA-013": {
                    "persona_results": analysis.get("persona_results") or [],
                    "domain": domain,
                    "required_personas": expected_personas,
                    "minimum_profile_coverage": 0.70,
                },
                "KA-030": {
                    "query": context.query,
                    "conflicts": [],
                    "context": {
                        "trace_id": context.trace_id,
                        "domain": domain,
                    },
                },
                "KA-038": {"claims": []},
            },
            prior_results={"KA-012": prior, "KA-028": expansion_prior},
            service_capabilities={"persona_context_service"},
        )
        plan = self.ka_selector.plan(request)
        report = await self.ka_executor.execute(plan, request)
        executed_ids = self._executed_ids(report)
        ka_results = self._committed_results(report, executed_ids)
        weighting = ka_results.get("KA-013", {}).get("output", {})
        conflict_resolution = ka_results.get("KA-030", {}).get("output", {})
        consensus = ka_results.get("KA-038", {}).get("output", {})
        sufficiency = weighting.get("sufficiency") or {}
        dissent_count = int(weighting.get("dissent_count") or 0)
        complete = (
            report.status is KAPlanExecutionStatus.SUCCEEDED
            and set(executed_ids) == {"KA-013", "KA-030", "KA-038"}
            and sufficiency.get("sufficient") is True
            and weighting.get("silent_dissent_count") == 0
            and conflict_resolution.get("silent_dissent_count") == 0
            and conflict_resolution.get("all_dissent_preserved") is True
            and len(conflict_resolution.get("prompt_constraints") or [])
            == dissent_count
            and consensus.get("dependencies_consumed") == ["KA-013", "KA-030"]
            and consensus.get("substantive_consensus_claimed") is False
        )
        if complete:
            for canonical_id in ("KA-013", "KA-030", "KA-038"):
                context.ka_result_cache[canonical_id] = report.results[canonical_id]
            receipt = {
                "schema_version": "dle.persona-context-receipt.v1",
                "service": "PersonaContextService",
                "status": "applied",
                "plan_id": plan.plan_id,
                "ka_proposal_ids": [
                    "KA-012",
                    "KA-013",
                    "KA-028",
                    "KA-030",
                    "KA-038",
                ],
                "context_target": "provider_system_message",
                "provider_subcalls_used": 0,
            }
            context.dsqp["persona_synthesis"] = {
                "weighting": weighting,
                "conflict_resolution": conflict_resolution,
                "consensus": consensus,
            }
            context.dsqp["persona_context_receipt"] = receipt
        context.provider_messages = build_provider_messages(context)
        system_text = str(context.provider_messages[0].get("content") or "")
        completed_kas = [
            str(item.get("ka_id"))
            for item in context.truthcore.get("steps_executed") or []
            if isinstance(item, dict)
            and item.get("status") == "completed"
            and item.get("ka_id")
        ]
        ok = (
            complete
            and bool(context.provider_messages)
            and bool(context.query)
            and "Governed persona analysis and synthesis" in system_text
        )
        return LayerExecution(
            ok=ok,
            outputs={
                "layer_id": "L5",
                "message_count": len(context.provider_messages),
                "contains_source_ids": all(
                    item.source_id in system_text for item in context.evidence
                ),
                "contains_dsqp": ("Deterministic persona context" in system_text),
                "contains_persona_ka_results": (
                    "Governed persona analysis and synthesis" in system_text
                ),
                "contains_ka_results": ("Executed TruthCore/KA context" in system_text),
                "selected_ka_ids": completed_kas,
                "persona_domain": domain,
                "authority_weight_total": round(
                    sum(
                        float(item.get("authority_weight") or 0.0)
                        for item in weighting.get("weighted_results") or []
                        if isinstance(item, dict)
                    ),
                    8,
                ),
                "dissent_count": dissent_count,
                "silent_dissent_count": (
                    conflict_resolution.get("silent_dissent_count")
                ),
                "dissent_resolution": (weighting.get("dissent_resolution")),
                "persona_sufficient": sufficiency.get("sufficient"),
                "consensus_ready": consensus.get("consensus_ready"),
                "substantive_consensus_claimed": consensus.get(
                    "substantive_consensus_claimed"
                ),
                "persona_context_receipt": context.dsqp.get("persona_context_receipt"),
                "provider_subcalls_used": 0,
                "child_trace_ids": self._child_trace_ids(
                    report,
                    executed_ids,
                ),
            },
            selected_ka_ids=executed_ids,
            ka_plan=self._plan_summary(plan, report),
            ka_results=ka_results,
            decisions=[
                {
                    "decision": (
                        "persona_synthesis_committed"
                        if complete
                        else "persona_synthesis_blocked"
                    ),
                    "sufficiency": sufficiency,
                    "dissent_count": dissent_count,
                    "silent_dissent_count": (
                        conflict_resolution.get("silent_dissent_count")
                    ),
                }
            ],
            effects=(
                [
                    {
                        "ka_id": canonical_id,
                        "state": "applied_by_owner",
                        "effect_port": "persona_context_service",
                        "applied": True,
                        "receipt": context.dsqp.get("persona_context_receipt"),
                    }
                    for canonical_id in ("KA-012", "KA-028")
                ]
                if complete
                else []
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
        context.reasoning.claims = [claim.to_dict() for claim in context.claims]
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
                        "decision": ("allow" if validation["ok"] else "block"),
                        "validation_score": validation["validation_score"],
                    }
                ],
                error_code=(
                    "L6_OUTPUT_VALIDATION_FAILURE" if not validation["ok"] else None
                ),
            ),
            validation,
        )

    def l7(self, context: GovernedContext) -> LayerExecution:
        dependency_map = {
            claim.claim_id: list(claim.evidence_ids) for claim in context.claims
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

    async def l8(self, context: GovernedContext) -> LayerExecution:
        blocking = [
            validator.validator_id
            for validator in context.validators
            if validator.status in {"failed", "blocked"}
        ]
        policy_blocks = [
            decision for decision in context.policy_decisions if decision.blocked
        ]
        candidate = str(context.reasoning.candidate or "")
        # KA-024 receives the measured binary policy-gate signal here. Answer
        # quality/confidence remains independently measured by L6/L9 and may
        # trigger refinement or abstention without being mislabeled as trust.
        confidence = 0.0 if blocking else 1.0
        try:
            risk_score = float(context.request.metadata.get("risk_score", 0.0))
        except (TypeError, ValueError):
            risk_score = 1.0
        risk_score = max(0.0, min(1.0, risk_score))
        evidence_input = [
            {
                "source": item.source_type,
                "source_id": item.source_id,
                "content_hash": item.content_hash,
                "quality_score": item.quality_score,
                "provenance_checks": (
                    item.metadata.get("provenance_checks", [])
                    if isinstance(item.metadata, dict)
                    else []
                ),
                "signature_verified": bool(
                    item.metadata.get("signature_verified")
                    if isinstance(item.metadata, dict)
                    else False
                ),
                "authority_verified": bool(
                    item.metadata.get("authority_verified")
                    if isinstance(item.metadata, dict)
                    else False
                ),
            }
            for item in context.evidence
        ]
        trust_source = evidence_input[0] if evidence_input else {}
        request = self._selection_request(
            context,
            layer_id="L8",
            tier=context.reasoning.tier or "standard",
            requested_ids=["KA-010", "KA-024", "KA-027", "KA-1074"],
            ka_inputs={
                "KA-004": {"query": context.query},
                "KA-005": {"query": context.query},
                "KA-010": {"content": candidate},
                "KA-018": {
                    "source_id": trust_source.get("source_id", "unspecified"),
                    "source_type": trust_source.get("source", "unverified"),
                    "content_sha256": trust_source.get("content_hash", "0" * 64),
                    "provenance_checks": trust_source.get("provenance_checks", []),
                },
                "KA-022": {
                    "recommendation": candidate,
                    "impact_scores": {"governed_risk": risk_score},
                },
                "KA-024": {
                    "confidence": confidence,
                    "risk_score": risk_score,
                },
                "KA-027": {
                    "recommendation": candidate,
                    "has_linguistic_bias": False,
                },
                "KA-062": {
                    "source_id": trust_source.get("source_id", "unspecified"),
                    "signature_verified": bool(trust_source.get("signature_verified")),
                    "authority_verified": bool(trust_source.get("authority_verified")),
                    "independently_corrobated": len(evidence_input) > 1,
                },
                "KA-1074": {
                    "fields": [
                        {
                            "field_id": "candidate",
                            "value": candidate,
                            "classification": "public",
                            "strategy": "retain",
                        }
                    ]
                },
                "KA-1107": {
                    "planned_steps": [
                        {
                            "step_id": "l8-trust-gate",
                            "capability_id": "KA-024",
                            "layer": "L8",
                            "query_class": "governed_validation",
                        }
                    ],
                    "allowed_capability_ids": ["KA-024"],
                    "allowed_layers": ["L8"],
                    "allowed_query_classes": ["governed_validation"],
                },
            },
            service_capabilities={
                "truthgate_policy_service",
                "privacy_transformation_service",
            },
        )
        plan = self.ka_selector.plan(request)
        report = await self.ka_executor.execute(plan, request)
        executed_ids = self._executed_ids(report)
        ka_results = self._committed_results(report, executed_ids)
        trust_output = ka_results.get("KA-024", {}).get("output", {})
        bias_output = ka_results.get("KA-010", {}).get("output", {})
        boundary_output = ka_results.get("KA-1107", {}).get("output", {})
        ethics_output = ka_results.get("KA-027", {}).get("output", {})
        privacy_output = ka_results.get("KA-1074", {}).get("output", {})
        ka_ok = (
            report.status is KAPlanExecutionStatus.SUCCEEDED
            and bias_output.get("is_biased") is not True
            and trust_output.get("is_approved") is True
            and boundary_output.get("plan_allowed") is True
            and ethics_output.get("status") != "CRITICAL_FAILURE"
            and privacy_output.get("non_public_value_exposed") is False
        )
        ok = not blocking and not policy_blocks and ka_ok
        decision = GovernedPolicyDecision(
            policy_id="truthgate_layer_8",
            decision="allow" if ok else "block",
            rationale=(
                "canonical_truthgate_ka_plan_committed"
                if ok
                else "validator_policy_or_truthgate_ka_block"
            ),
            stage="L8",
            flags=sorted(
                {
                    *blocking,
                    *(["prior_policy_block"] if policy_blocks else []),
                    *(["truthgate_ka_block"] if not ka_ok else []),
                }
            ),
            ka_results=ka_results,
        )
        context.policy_decisions.append(decision)
        decision_payload = {
            **decision.to_dict(),
            "blocking_validator_ids": blocking,
            "blocking_policy_count": len(policy_blocks),
        }
        return LayerExecution(
            ok=ok,
            outputs={
                "layer_id": "L8",
                "trust_policy_decision": decision_payload,
                "risk_class": (
                    (
                        (context.reasoning.coordinate_17.get("axes") or {}).get("15")
                        or {}
                    ).get("value")
                    if isinstance(context.reasoning.coordinate_17, dict)
                    else None
                ),
                "privacy_security_compliance": "governance_and_output_controls_applied",
            },
            selected_ka_ids=executed_ids,
            ka_plan=self._plan_summary(plan, report),
            ka_results=ka_results,
            decisions=[decision_payload],
            error_code="L8_TRUST_POLICY_BLOCK" if not ok else None,
        )

    async def l9(
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
        trace = self._committed_layer_trace(context, through_layer=8)
        confidence_value = (
            context.confidence_measurement.value
            if context.confidence_measurement
            else None
        )
        persona_measurements = self._persona_measurements(context)
        issues = [
            {
                "type": (
                    "contradicted_claim"
                    if claim.status == "contradicted"
                    else "unsupported_claim"
                ),
                "claim_id": claim.claim_id,
            }
            for claim in context.claims
            if claim.status == "contradicted"
            or (requires_evidence and claim.status in {"unsupported", "insufficient"})
        ]
        requested_ids = [f"L9-KA-{number:03d}" for number in range(1, 8)]
        request = self._selection_request(
            context,
            layer_id="L9",
            tier=tier,
            requested_ids=requested_ids,
            ka_inputs={
                "L9-KA-001": {
                    "trace": trace,
                    "layers": list(range(1, 9)),
                },
                "L9-KA-002": {
                    "original_query": context.query,
                    "final_solution": context.reasoning.candidate or "",
                },
                "L9-KA-003": {
                    "domain_confidences": persona_measurements,
                    "threshold": 0.95 if tier != "high" else 0.99,
                },
                "L9-KA-004": {
                    "solution": {
                        "overall_confidence": confidence_value,
                        "domain_confidences": persona_measurements,
                    },
                    "trace": trace,
                },
                "L9-KA-005": {
                    "readiness": confidence_value,
                    "readiness_threshold": (0.85 if tier == "high" else 0.70),
                    "issues": issues,
                    "convergence_action": convergence.action,
                },
                "L9-KA-006": {
                    "l8_confidence": confidence_value,
                },
                "L9-KA-007": {
                    "iteration": iteration,
                    "max_iterations": max_iterations,
                    "previous_scores": [
                        layer.outputs.get("readiness_score")
                        for layer in context.reasoning.layers
                        if layer.layer_id == "L9"
                        and layer.outputs.get("readiness_score") is not None
                    ],
                    "prior_fixes": [
                        decision.to_dict()
                        for decision in context.convergence_decisions
                        if decision.action == "refine"
                    ],
                },
            },
        )
        try:
            plan = self.ka_selector.plan(request)
            report = await self.ka_executor.execute(plan, request)
        except Exception as exc:  # noqa: BLE001 - required L9 boundary
            return (
                LayerExecution(
                    ok=False,
                    outputs={
                        "layer_id": "L9",
                        "decision": "block",
                        "reason": "required_l9_plan_failed",
                        "error_type": type(exc).__name__,
                    },
                    ka_plan=self._plan_summary(plan if "plan" in locals() else None),
                    error_code="L9_REQUIRED_KA_FAILURE",
                ),
                self._override_convergence(
                    convergence,
                    action="block",
                    reason="required_l9_plan_failed",
                ),
            )

        executed_ids = self._executed_ids(report)
        ka_results = self._committed_results(report, executed_ids)
        if report.status is not KAPlanExecutionStatus.SUCCEEDED or set(
            executed_ids
        ) != set(requested_ids):
            convergence = self._override_convergence(
                convergence,
                action="block",
                reason=(
                    "required_l9_result_missing_or_failed:"
                    + str(report.required_failure or "trace_mismatch")
                ),
            )
        else:
            trace_result = report.results["L9-KA-001"].output
            drift_result = report.results["L9-KA-002"].output
            recursion_result = report.results["L9-KA-005"].output
            readiness_result = report.results["L9-KA-006"].output
            loop_result = report.results["L9-KA-007"].output
            forged = any(
                issue.get("type") == "uncommitted_ka_invocation"
                for issue in trace_result.get("issues") or []
            )
            if forged:
                convergence = self._override_convergence(
                    convergence,
                    action="block",
                    reason="l9_trace_forgery_detected",
                )
            elif recursion_result.get("trigger_refinement") and loop_result.get(
                "exhausted"
            ):
                convergence = self._override_convergence(
                    convergence,
                    action="block",
                    reason="l9_recursion_budget_exhausted",
                )
            elif (
                drift_result.get("numeric_facts_preserved") is False
                and convergence.action == "finalize"
            ):
                convergence = self._override_convergence(
                    convergence,
                    action=("refine" if iteration < max_iterations else "abstain"),
                    reason="l9_numeric_belief_drift",
                )
            elif (
                recursion_result.get("trigger_refinement")
                and loop_result.get("continue")
                and convergence.action == "finalize"
            ):
                convergence = self._override_convergence(
                    convergence,
                    action=("refine" if iteration < max_iterations else "abstain"),
                    reason="l9_readiness_requires_refinement",
                )

        context.convergence_decisions.append(convergence)
        context.reasoning.convergence = convergence.to_dict()
        readiness_result = (
            report.results.get("L9-KA-006").output
            if report.results.get("L9-KA-006")
            else {}
        )
        persona_result = (
            report.results.get("L9-KA-003").output
            if report.results.get("L9-KA-003")
            else {}
        )
        drift_result = (
            report.results.get("L9-KA-002").output
            if report.results.get("L9-KA-002")
            else {}
        )
        trace_result = (
            report.results.get("L9-KA-001").output
            if report.results.get("L9-KA-001")
            else {}
        )
        ok = convergence.action != "block"
        return (
            LayerExecution(
                ok=ok,
                outputs={
                    "layer_id": "L9",
                    "trace_consistency": (
                        "consistent"
                        if trace_result.get("trace_complete")
                        else "findings"
                    ),
                    "persona_agreement": persona_result,
                    "drift_status": drift_result,
                    "readiness_score": readiness_result.get("readiness_score"),
                    "readiness_measurement": readiness_result,
                    "kas_invoked": executed_ids,
                    "convergence": convergence.to_dict(),
                },
                selected_ka_ids=list(plan.selected_ids),
                ka_plan=self._plan_summary(plan, report),
                ka_results=ka_results,
                decisions=[convergence.to_dict()],
                error_code="L9_CONVERGENCE_BLOCK" if not ok else None,
            ),
            convergence,
        )

    async def l10(
        self,
        context: GovernedContext,
        *,
        final_action: str,
    ) -> LayerExecution:
        content = context.reasoning.candidate or ""
        confidence_value = (
            context.confidence_measurement.value
            if context.confidence_measurement
            else None
        )
        risk_domain = self._risk_domain(context)
        convergence_reason = (
            context.reasoning.convergence.get("reason")
            if isinstance(context.reasoning.convergence, dict)
            else None
        )
        allow_not_measured = final_action in {
            "abstain",
            "local_review",
        } or convergence_reason in {
            "finalize_with_not_measured_confidence",
            "low_risk_finalize_with_explicit_unsupported_claims",
        }
        requested_ids = [f"L10-KA-{number:03d}" for number in range(1, 8)]
        common = {
            "content": content,
            "final_action": final_action,
            "confidence": confidence_value,
            "risk_domain": risk_domain,
            "request_id": context.request.request_id,
            "allow_not_measured": allow_not_measured,
            "consequential_decision": bool(
                context.request.metadata.get("consequential_decision")
            ),
        }
        request = self._selection_request(
            context,
            layer_id="L10",
            tier=context.reasoning.tier or "unknown",
            requested_ids=requested_ids,
            ka_inputs={
                "L10-KA-001": {
                    "content": content,
                    "threshold": 0.82,
                },
                "L10-KA-002": {"content": content},
                "L10-KA-003": {"content": content},
                "L10-KA-004": {"content": content},
                "L10-KA-005": common,
                "L10-KA-006": {
                    "confidence": confidence_value,
                    "threshold": (0.985 if risk_domain == "high_risk" else 0.95),
                    "allow_not_measured": allow_not_measured,
                },
                "L10-KA-007": common,
            },
        )
        try:
            plan = self.ka_selector.plan(request)
            report = await self.ka_executor.execute(plan, request)
        except Exception as exc:  # noqa: BLE001 - required L10 boundary
            decision = {
                "decision": "halt",
                "final_action": final_action,
                "reason": "required_l10_plan_failed",
                "error_type": type(exc).__name__,
            }
            context.reasoning.release = decision
            return LayerExecution(
                ok=False,
                outputs={"layer_id": "L10", "release": decision},
                ka_plan=self._plan_summary(plan if "plan" in locals() else None),
                decisions=[decision],
                error_code="L10_REQUIRED_KA_FAILURE",
            )

        executed_ids = self._executed_ids(report)
        ka_results = self._committed_results(report, executed_ids)
        containment = (
            report.results.get("L10-KA-005").output
            if report.results.get("L10-KA-005")
            else {}
        )
        redaction = (
            report.results.get("L10-KA-003").output
            if report.results.get("L10-KA-003")
            else {}
        )
        complete = report.status is KAPlanExecutionStatus.SUCCEEDED and set(
            executed_ids
        ) == set(requested_ids)
        containment_decision = str(containment.get("decision") or "HALT").upper()
        release = complete and containment_decision in {
            "RELEASE",
            "MODIFY",
        }
        released_content = (
            str(redaction.get("redacted_content") or content) if release else None
        )
        if release:
            if released_content != content:
                self.redact_sensitive_context(context)
            context.reasoning.candidate = released_content
        decision = {
            "decision": "release" if release else "halt",
            "final_action": final_action,
            "candidate_present": bool(content),
            "containment_decision": containment_decision,
            "required_suite_complete": complete,
            "control_set": "cp19_e_full_l9_l10_ka_suite",
            "released_content_modified": released_content != content,
        }
        context.reasoning.release = decision
        return LayerExecution(
            ok=release,
            outputs={
                "layer_id": "L10",
                "release": decision,
                "released_content": released_content,
                "kas_invoked": executed_ids,
                "privacy": {
                    "redactions_found": redaction.get("redactions_found", 0),
                    "sensitive_values_returned": redaction.get(
                        "sensitive_values_returned", False
                    ),
                },
                "effects_applied": False,
                "validated_memory_commit": "not_requested",
            },
            selected_ka_ids=list(plan.selected_ids),
            ka_plan=self._plan_summary(plan, report),
            ka_results=ka_results,
            decisions=[decision],
            error_code=(
                "L10_REQUIRED_KA_FAILURE"
                if not complete
                else "L10_RELEASE_BLOCK"
                if not release
                else None
            ),
        )

    def _selection_request(
        self,
        context: GovernedContext,
        *,
        layer_id: str,
        tier: str,
        requested_ids: list[str],
        ka_inputs: dict[str, dict[str, Any]],
        prior_results: dict[str, Any] | None = None,
        service_capabilities: set[str] | None = None,
    ) -> KASelectionRequest:
        remaining_ms = 20_000
        if context.deadline_at_monotonic is not None:
            import time

            remaining_ms = max(
                1,
                int((context.deadline_at_monotonic - time.monotonic()) * 1000),
            )
        return KASelectionRequest(
            requested_ids=requested_ids,
            ka_inputs=ka_inputs,
            prior_results=dict(prior_results or {}),
            service_capabilities=set(service_capabilities or set()),
            mode=KAExecutionMode.PRODUCTION,
            context=KAExecutionContext(
                request_id=context.request.request_id,
                run_id=context.trace_id,
                session_id=context.request.session_id,
                principal_id=context.request.principal_id,
                workflow="governed.v1",
                tier=tier,
                layer=layer_id,
                budget=KABudget(
                    deadline_ms=min(remaining_ms, 20_000),
                    max_dependency_executions=16,
                    max_recursion_depth=8,
                    max_selected_algorithms=16,
                    max_fan_out=8,
                    max_parallelism=4,
                    max_input_bytes=1_000_000,
                    max_output_bytes=5_000_000,
                    max_effects=16,
                ),
            ),
        )

    @classmethod
    def redact_sensitive_context(cls, context: GovernedContext) -> None:
        """Remove detected PII from trace-bearing governed state."""
        for stage in context.stages:
            stage.inputs = cls.redact_sensitive_value(stage.inputs)
            stage.outputs = cls.redact_sensitive_value(stage.outputs)
            stage.metrics = cls.redact_sensitive_value(stage.metrics)
        for layer in context.reasoning.layers:
            layer.inputs = cls.redact_sensitive_value(layer.inputs)
            layer.outputs = cls.redact_sensitive_value(layer.outputs)
            layer.ka_results = cls.redact_sensitive_value(layer.ka_results)
            layer.decisions = cls.redact_sensitive_value(layer.decisions)
            layer.effects = cls.redact_sensitive_value(layer.effects)
        for claim in context.claims:
            claim.text = cls.redact_sensitive_value(claim.text)
        for validator in context.validators:
            validator.inputs = cls.redact_sensitive_value(validator.inputs)
            validator.outputs = cls.redact_sensitive_value(validator.outputs)
        for evidence in context.evidence:
            redacted_text = cls.redact_sensitive_value(evidence.text)
            if redacted_text != evidence.text:
                from hashlib import sha256

                evidence.text = redacted_text
                evidence.content_hash = sha256(
                    redacted_text.encode("utf-8")
                ).hexdigest()
                if evidence.source is not None:
                    evidence.source.content_hash = evidence.content_hash
            evidence.title = cls.redact_sensitive_value(evidence.title)
            evidence.locator = cls.redact_sensitive_value(evidence.locator)
            evidence.metadata = cls.redact_sensitive_value(evidence.metadata)
        context.provider_messages = cls.redact_sensitive_value(
            context.provider_messages
        )
        context.reasoning.candidate = cls.redact_sensitive_value(
            context.reasoning.candidate
        )
        context.reasoning.claims = cls.redact_sensitive_value(context.reasoning.claims)
        context.reasoning.validators = cls.redact_sensitive_value(
            context.reasoning.validators
        )
        context.truthcore = cls.redact_sensitive_value(context.truthcore)
        context.dsqp = cls.redact_sensitive_value(context.dsqp)
        for decision in context.policy_decisions:
            decision.rationale = cls.redact_sensitive_value(decision.rationale)
            decision.flags = cls.redact_sensitive_value(decision.flags)
            decision.ka_results = cls.redact_sensitive_value(decision.ka_results)
        if "_knowledge_lifecycle" in context.request.metadata:
            context.request.metadata["_knowledge_lifecycle"] = (
                cls.redact_sensitive_value(
                    context.request.metadata["_knowledge_lifecycle"]
                )
            )
        if context.memory_proposal is not None:
            context.memory_proposal.content = cls.redact_sensitive_value(
                context.memory_proposal.content
            )

    @classmethod
    def redact_sensitive_value(cls, value: Any) -> Any:
        """Recursively redact supported PII patterns without returning matches."""
        if isinstance(value, str):
            redacted = value
            for pii_type, pattern in PII_PATTERNS.items():
                redacted = pattern.sub(
                    f"[REDACTED_{pii_type}]",
                    redacted,
                )
            return redacted
        if isinstance(value, dict):
            return {
                key: cls.redact_sensitive_value(item) for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls.redact_sensitive_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls.redact_sensitive_value(item) for item in value)
        return value

    @staticmethod
    def _plan_summary(
        plan: KASelectionPlan | None,
        report: Any | None = None,
    ) -> dict[str, Any]:
        if plan is None:
            return {
                "schema_version": "dle.ka-stage-plan.v1",
                "selection_state": "plan_unavailable",
            }
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

    @staticmethod
    def _executed_ids(report: Any) -> list[str]:
        return sorted(
            canonical_id
            for canonical_id, trace in report.traces.items()
            if any(event.state is KATraceState.EXECUTED for event in trace.events)
        )

    @staticmethod
    def _committed_results(
        report: Any,
        executed_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        return {
            canonical_id: report.results[canonical_id].model_dump(
                mode="json",
                exclude_none=True,
            )
            for canonical_id in executed_ids
            if canonical_id in report.results
        }

    @staticmethod
    def _committed_layer_trace(
        context: GovernedContext,
        *,
        through_layer: int,
    ) -> dict[str, Any]:
        trace: dict[str, Any] = {}
        for layer in context.reasoning.layers:
            layer_number = int(layer.layer_id.removeprefix("L"))
            if layer_number > through_layer:
                continue
            trace[f"layer{layer_number}"] = {
                "output": dict(layer.outputs),
                "selected_ka_ids": list(layer.selected_ka_ids),
                "ka_results": dict(layer.ka_results),
                "stage_id": layer.stage_id,
                "status": layer.status.value,
            }
        return trace

    @staticmethod
    def _persona_measurements(
        context: GovernedContext,
    ) -> list[dict[str, Any]]:
        measurements = []
        synthesis = context.dsqp.get("persona_synthesis")
        weighting = (
            synthesis.get("weighting")
            if isinstance(synthesis, dict)
            and isinstance(synthesis.get("weighting"), dict)
            else {}
        )
        weighted_results = weighting.get("weighted_results") or []
        for result in weighted_results:
            if not isinstance(result, dict):
                continue
            score = result.get("profile_coverage")
            if score is None:
                continue
            measurements.append(
                {
                    "domain": str(result.get("persona_type") or "unknown"),
                    "confidence": float(score),
                    "measurement_type": "dsqp_profile_coverage",
                }
            )
        if measurements:
            return measurements
        for axis, profile in context.reasoning.dsqp_profiles.items():
            if not isinstance(profile, dict):
                continue
            validation = (
                profile.get("validation")
                if isinstance(profile.get("validation"), dict)
                else {}
            )
            score = validation.get("coverage_score")
            if score is None:
                continue
            measurements.append(
                {
                    "domain": str(
                        profile.get("persona_type")
                        or profile.get("persona_id")
                        or f"axis_{axis}"
                    ),
                    "confidence": float(score),
                    "measurement_type": "dsqp_profile_coverage",
                }
            )
        return measurements

    @staticmethod
    def _persona_profiles_by_type(
        profiles: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        output: dict[str, dict[str, Any]] = {}
        for profile in profiles.values():
            if not isinstance(profile, dict):
                continue
            persona_type = str(profile.get("persona_type") or "").strip().lower()
            if persona_type and persona_type not in output:
                output[persona_type] = profile
        return output

    @classmethod
    def _persona_domain(cls, context: GovernedContext) -> str:
        explicit = (
            str(
                context.request.metadata.get("persona_domain")
                or context.request.metadata.get("domain")
                or ""
            )
            .strip()
            .upper()
        )
        if explicit in {
            "TECHNICAL",
            "SECTOR",
            "REGULATORY",
            "COMPLIANCE",
            "HIGH_RISK",
        }:
            return explicit
        if cls._risk_domain(context) == "high_risk":
            return "HIGH_RISK"
        query = context.query.casefold()
        domains = (
            ("REGULATORY", ("regulation", "regulatory", "law", "legal")),
            ("COMPLIANCE", ("compliance", "audit", "control")),
            ("TECHNICAL", ("technical", "software", "system", "code")),
            ("SECTOR", ("industry", "market", "sector", "operations")),
        )
        for domain, terms in domains:
            if any(term in query for term in terms):
                return domain
        return "GENERAL"

    @staticmethod
    def _child_trace_ids(
        report: Any,
        executed_ids: list[str],
    ) -> list[str]:
        return sorted(
            {
                report.results[canonical_id].trace_id
                for canonical_id in executed_ids
                if canonical_id in report.results
                and report.results[canonical_id].trace_id
            }
        )

    @staticmethod
    def _risk_domain(context: GovernedContext) -> str:
        coordinate = context.reasoning.coordinate_17
        axes = coordinate.get("axes") if isinstance(coordinate, dict) else {}
        axis15 = axes.get("15") if isinstance(axes, dict) else {}
        value = axis15.get("value") if isinstance(axis15, dict) else axis15
        normalized = str(value or "standard").strip().lower()
        return (
            "high_risk"
            if normalized
            in {"high", "critical", "healthcare", "finance", "legal", "safety"}
            else "standard"
        )

    @staticmethod
    def _override_convergence(
        current: ConvergenceDecision,
        *,
        action: str,
        reason: str,
    ) -> ConvergenceDecision:
        return ConvergenceDecision(
            action=action,
            reason=reason,
            iteration=current.iteration,
            max_iterations=current.max_iterations,
            terminal=action != "refine",
            unsupported_claim_ids=list(current.unsupported_claim_ids),
            contradicted_claim_ids=list(current.contradicted_claim_ids),
            failed_validator_ids=list(current.failed_validator_ids),
            decision_version="dle-convergence.cp19-e.v1",
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
