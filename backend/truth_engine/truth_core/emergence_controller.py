"""
Layer 10: EmergenceDetectionController

The EmergenceDetectionController is the final safety gate and release authority
of the UKG 10-layer stack. It performs emergence detection, safety audit,
and makes the final binary RELEASE vs CONTAIN decision.
"""

import hashlib
import json
import logging
import time
from typing import Any, ClassVar

from backend.knowledge_algorithms.contracts import KAExecutionResult

from .l10_schemas import (
    ContainmentAction,
    DSQPTraceSeal,
    EmergenceAssessment,
    EmergenceLevel,
    EmergencePattern,
    L10Decision,
    L10Input,
    L10Result,
    SafetyCheckResult,
    SafetyViolation,
    TrustGateResult,
)

logger = logging.getLogger(__name__)

# Trust thresholds with belief decay factored in
TRUST_THRESHOLDS = {"standard": 0.95, "high_risk": 0.985}

# Belief decay factor (98% nudge)
BELIEF_DECAY_FACTOR = 0.98

# Max processing time for safety checks
MAX_SAFETY_TIME_MS = 20000


class EmergenceDetectionController:
    """
    Layer 10: EmergenceDetectionController (The Sentinel)

    The Final Guardian. Orchestrates two operational lanes:
    - Lane A (Response Gate): Real-time safety, emergence, and release authority.
    - Lane B (Knowledge Commit): Authorized persistence of reasoning and learning.
    """

    # L10 specific KA suite
    L10_KAS: ClassVar[list[str]] = [
        "L10-KA-001",  # Entropy-Based Emergence Scorer
        "L10-KA-002",  # Self-Awareness Monitor
        "L10-KA-003",  # Privacy & PII Redactor
        "L10-KA-004",  # Ethical Alignment Validator
        "L10-KA-005",  # Containment Decision Engine
        "L10-KA-006",  # Terminal Trust Gate (Belief Decay)
        "L10-KA-007",  # Human Escalation Router (Axis 17)
    ]

    # Canonical KAs for Lane A (Response Gate)
    LANE_A_KAS: ClassVar[list[str]] = [
        "KA-021",
        "KA-1108",
        "KA-116",  # Emergence/Drift
        "KA-061",
        "KA-063",
        "KA-027",  # Safety/Ethics
        "KA-014",
        "KA-023",
        "KA-1095",
        "KA-062",  # Trust/Governance
    ]

    # Canonical KAs for Lane B (Knowledge Commit)
    LANE_B_KAS: ClassVar[list[str]] = [
        "KA-1109",
        "KA-1079",
        "KA-050",
        "KA-1094",  # Commit/Classification
        "KA-065",
        "KA-083",
        "KA-088",
        "KA-096",  # Lifecycle/Regression
    ]

    def __init__(self, ka_controller=None, config: dict | None = None):
        self.ka_controller = ka_controller
        self.config = config or {}
        logger.info("EmergenceDetectionController (Layer 10 Sentinel) initialized")

    def _execute_ka(
        self,
        ka_id: str,
        payload: dict[str, Any],
        kas_invoked: list[str],
    ) -> dict[str, Any]:
        """Execute through the typed contract and record only successful calls."""
        if self.ka_controller is None:
            raise RuntimeError(f"{ka_id} controller is unavailable")
        execute_typed = getattr(self.ka_controller, "execute_typed", None)
        if not callable(execute_typed):
            raise TypeError(
                f"{type(self.ka_controller).__name__} does not implement execute_typed"
            )
        result = execute_typed(ka_id, payload)
        if not isinstance(result, KAExecutionResult):
            raise TypeError(f"{ka_id} returned a non-canonical execution result")
        output = result.require_output()
        kas_invoked.append(result.canonical_id)
        return output

    @staticmethod
    def _required_output_value(
        ka_id: str,
        output: dict[str, Any],
        field: str,
    ) -> Any:
        if field not in output:
            raise RuntimeError(f"{ka_id} output is missing required field {field!r}")
        return output[field]

    def authorize(self, input_data: L10Input | None) -> L10Result:
        """
        Final release authority gate (Lane A + Lane B triggers).
        """
        start_time = time.time()
        kas_invoked = []

        if input_data is None:
            return self._create_failure_result(None, "Input data is None", 0.0)

        try:
            # --- LANE A: Response Gate (Sync) ---

            # 1. Emergence & Capability Drift
            emergence_report = self._detect_emergence_lane_a(input_data, kas_invoked)

            # 2. Safety & Policy Audit
            safety_report = self._run_safety_audit_lane_a(input_data, kas_invoked)

            # 3. Trust Gate (Belief Decay)
            trust_report = self._evaluate_trust_gate_lane_a(input_data, kas_invoked)

            # 4. Final Release Decision
            decision, final_answer, actions = self._make_containment_decision(
                input_data,
                emergence_report,
                safety_report,
                trust_report,
                kas_invoked,
            )

            # --- LANE B: Knowledge Commit (Async/Deferred Logic) ---
            if decision in [L10Decision.RELEASE, L10Decision.MODIFY]:
                self._process_knowledge_commit_lane_b(input_data, kas_invoked)

            # 5. DSQP Trace Finalization (Axis 15)
            dsqp_seal = self._generate_dsqp_seal(
                input_data, emergence_report, safety_report
            )

            processing_time = (time.time() - start_time) * 1000

            return L10Result(
                simulation_id=input_data.simulation_id,
                decision=decision,
                final_answer=final_answer,
                emergence_report=emergence_report,
                safety_report=safety_report,
                trust_report=trust_report,
                containment_actions=actions,
                dsqp_seal=dsqp_seal,
                kas_invoked=kas_invoked,
                processing_time_ms=processing_time,
                requires_human_signoff=(trust_report.action_required == "human_review")
                or (decision == L10Decision.ESCALATE),
            )

        except Exception as e:
            logger.exception("Layer 10 Sentinel Critical Failure")
            return self._create_failure_result(
                input_data, str(e), (time.time() - start_time) * 1000
            )

    def _detect_emergence_lane_a(
        self, input_data: L10Input, kas_invoked: list[str]
    ) -> EmergenceAssessment:
        """Detect emergent behaviors and capability drift using canonical and L10 KAs."""
        assessment = EmergenceAssessment()
        content = input_data.l9_result.get("epistemic_report", {}).get(
            "current_output", ""
        )

        if not self.ka_controller:
            return assessment

        # KA-021: Emergence Detection (General)
        try:
            observations = input_data.l9_result.get("emergence_observations")
            if not isinstance(observations, list) or not observations:
                observations = [
                    {
                        "observation_id": input_data.simulation_id,
                        "metric_name": "reasoning_trace_step_count",
                        "baseline_value": float(len(input_data.reasoning_trace)),
                        "observed_value": float(len(input_data.reasoning_trace)),
                        "tolerance": 0.0,
                        "corroborating_trace_ids": [input_data.simulation_id],
                    }
                ]
            ka_res = self._execute_ka(
                "KA-021",
                {"observations": observations},
                kas_invoked,
            )
            if self._required_output_value("KA-021", ka_res, "is_emergent"):
                assessment.emergence_detected = True
                assessment.overall_level = EmergenceLevel.MODERATE
        except Exception as exc:
            raise RuntimeError("Required KA-021 emergence check failed") from exc

        # KA-1108: Capability Escalation (Unsafe drift)
        try:
            crossed_boundary = "bypass" in content.lower()
            ka_res = self._execute_ka(
                "KA-1108",
                {
                    "interactions": [
                        {
                            "interaction_id": input_data.simulation_id,
                            "source_capability_id": "reasoning_stack",
                            "target_capability_id": "release_boundary",
                            "observed_invocations": 1,
                            "authorized_invocations": (0 if crossed_boundary else 1),
                            "emergence_flag": bool(assessment.emergence_detected),
                            "crossed_privilege_boundary": crossed_boundary,
                        }
                    ]
                },
                kas_invoked,
            )
            if self._required_output_value("KA-1108", ka_res, "escalation_detected"):
                assessment.patterns.append(
                    EmergencePattern(
                        pattern_type="capability_escalation",
                        location="reasoning_path",
                        description="AI attempted to bypass safety bounds",
                        risk_level=EmergenceLevel.HIGH,
                        score=0.9,
                    )
                )
        except Exception as exc:
            raise RuntimeError("Required KA-1108 escalation check failed") from exc

        # L10-KA-001/002: Entropy and Self-Awareness
        try:
            ka_res = self._execute_ka(
                "L10-KA-001",
                {"content": content},
                kas_invoked,
            )
            assessment.entropy_delta = float(
                self._required_output_value(
                    "L10-KA-001",
                    ka_res,
                    "entropy_score",
                )
            )

            ka_res = self._execute_ka(
                "L10-KA-002",
                {"content": content},
                kas_invoked,
            )
            if self._required_output_value(
                "L10-KA-002",
                ka_res,
                "awareness_detected",
            ):
                assessment.patterns.append(
                    EmergencePattern(
                        pattern_type="self_referential",
                        location="output",
                        description="Self-awareness indicators found",
                        risk_level=EmergenceLevel.LOW,
                        score=0.3,
                    )
                )
        except Exception as exc:
            raise RuntimeError(
                "Required Layer-10 entropy/self-awareness checks failed"
            ) from exc

        return assessment

    def _run_safety_audit_lane_a(
        self, input_data: L10Input, kas_invoked: list[str]
    ) -> SafetyCheckResult:
        """Sequential safety and policy audit."""
        result = SafetyCheckResult()
        content = input_data.l9_result.get("epistemic_report", {}).get(
            "current_output", ""
        )

        if not self.ka_controller:
            return result

        # Privacy baseline. KA-058/KA-059 are unrelated learning/routing KAs
        # and must never be relabelled as safety controls.
        try:
            privacy = self._execute_ka(
                "L10-KA-003",
                {"content": content},
                kas_invoked,
            )
            redaction_count = int(
                self._required_output_value(
                    "L10-KA-003",
                    privacy,
                    "redactions_found",
                )
            )
            if redaction_count:
                result.passed = False
                result.violations.append(
                    SafetyViolation(
                        module="privacy",
                        violation_type="PII_leak",
                        severity="major",
                        description=(
                            f"{redaction_count} sensitive value(s) require redaction"
                        ),
                        recommended_action="redact",
                    )
                )
        except Exception as exc:
            raise RuntimeError("Required Layer-10 privacy check failed") from exc

        # Ethics Validator (L10-KA-004 + KA-027)
        try:
            ka_res = self._execute_ka(
                "L10-KA-004",
                {"content": content},
                kas_invoked,
            )
            violations = self._required_output_value(
                "L10-KA-004",
                ka_res,
                "violations",
            )
            if violations:
                result.passed = False
                for v in violations:
                    result.violations.append(
                        SafetyViolation(
                            module="ethics",
                            violation_type=v["type"],
                            severity=v["severity"],
                            description=v["message"],
                            recommended_action="modify",
                        )
                    )
        except Exception as exc:
            raise RuntimeError("Required Layer-10 ethics check failed") from exc

        result.release_approved = (
            len([v for v in result.violations if v.severity == "critical"]) == 0
        )
        return result

    def _evaluate_trust_gate_lane_a(
        self, input_data: L10Input, kas_invoked: list[str]
    ) -> TrustGateResult:
        """Enforce domain thresholds with belief decay and Axis 17 governance."""
        orig_conf = float(input_data.l9_result.get("readiness_score", 0.0))
        domain = input_data.risk_domain
        threshold = TRUST_THRESHOLDS.get(domain, 0.95)
        try:
            trust_output = self._execute_ka(
                "L10-KA-006",
                {
                    "confidence": orig_conf,
                    "threshold": threshold,
                    "decay_factor": BELIEF_DECAY_FACTOR,
                },
                kas_invoked,
            )
            status = str(
                self._required_output_value("L10-KA-006", trust_output, "status")
            )
            decayed_conf = float(
                self._required_output_value(
                    "L10-KA-006",
                    trust_output,
                    "decayed_confidence",
                )
            )
        except Exception as exc:
            raise RuntimeError("Required Layer-10 trust gate failed") from exc

        action = "none"
        if status == "fail":
            action = "human_review" if domain == "high_risk" else "refinement"
            # KA-1095: Human-in-the-Loop Escalation proposal.
            if action == "human_review" and self.ka_controller:
                try:
                    self._execute_ka(
                        "KA-1095",
                        {
                            "cases": [
                                {
                                    "case_id": input_data.simulation_id,
                                    "risk_class": "high",
                                    "confidence": decayed_conf,
                                    "irreversible_effect": bool(
                                        input_data.problem_spec.get(
                                            "irreversible_effect"
                                        )
                                    ),
                                    "policy_exception": bool(
                                        input_data.problem_spec.get("policy_exception")
                                    ),
                                    "affected_subject_count": int(
                                        input_data.problem_spec.get(
                                            "affected_subject_count", 0
                                        )
                                    ),
                                }
                            ],
                            "minimum_confidence": threshold,
                        },
                        kas_invoked,
                    )
                except Exception as exc:
                    raise RuntimeError(
                        "Required high-risk human escalation failed"
                    ) from exc

        try:
            self._execute_ka(
                "L10-KA-007",
                {
                    "request_id": input_data.simulation_id,
                    "risk_domain": domain,
                    "confidence": decayed_conf,
                    "consequential_decision": bool(
                        input_data.problem_spec.get("consequential_decision")
                    ),
                },
                kas_invoked,
            )
        except Exception as exc:
            raise RuntimeError("Required Layer-10 escalation routing failed") from exc

        return TrustGateResult(
            status=status,
            domain_category=domain,
            required_threshold=threshold,
            original_confidence=orig_conf,
            decayed_confidence=decayed_conf,
            gap=decayed_conf - threshold,
            action_required=action,
        )

    def _process_knowledge_commit_lane_b(
        self, input_data: L10Input, kas_invoked: list[str]
    ) -> dict[str, Any]:
        """Return a persistence proposal; the governed orchestrator owns effects."""
        risk_class = (
            input_data.risk_domain
            if input_data.risk_domain in {"low", "medium", "high", "critical"}
            else "high"
            if input_data.risk_domain == "high_risk"
            else "medium"
        )
        declared_sensitivity = str(
            input_data.problem_spec.get("declared_sensitivity", "internal")
        ).lower()
        if declared_sensitivity not in {
            "public",
            "internal",
            "restricted",
            "prohibited",
        }:
            declared_sensitivity = "restricted"
        risk_signals = [
            str(value)
            for value in input_data.problem_spec.get("risk_signals", [])
            if str(value)
            in {
                "credential",
                "secret",
                "regulated",
                "malware",
                "prompt_injection",
                "unknown_origin",
            }
        ]

        try:
            containment = self._execute_ka(
                "KA-1109",
                {
                    "candidates": [
                        {
                            "knowledge_id": input_data.simulation_id,
                            "declared_sensitivity": declared_sensitivity,
                            "contains_personal_data": bool(
                                input_data.problem_spec.get("contains_personal_data")
                            ),
                            "consent_verified": bool(
                                input_data.problem_spec.get("consent_verified")
                            ),
                            "redistribution_allowed": bool(
                                input_data.problem_spec.get(
                                    "redistribution_allowed", False
                                )
                            ),
                            "risk_signals": risk_signals,
                        }
                    ]
                },
                kas_invoked,
            )
            containment_decision = self._required_output_value(
                "KA-1109", containment, "decisions"
            )[0]
        except Exception as exc:
            raise RuntimeError(
                "Required Lane-B containment classification failed"
            ) from exc

        try:
            promotion = self._execute_ka(
                "KA-1079",
                {
                    "knowledge_id": input_data.simulation_id,
                    "validation_status": str(
                        input_data.l9_result.get("validation_status", "unvalidated")
                    ),
                    "confidence": float(
                        input_data.l9_result.get("readiness_score", 0.0)
                    ),
                    "evidence_count": int(
                        input_data.l9_result.get("evidence_count", 0)
                    ),
                    "citation_count": int(
                        input_data.l9_result.get("citation_count", 0)
                    ),
                    "contradiction_count": int(
                        input_data.l9_result.get("contradiction_count", 0)
                    ),
                    "provenance_complete": bool(
                        input_data.l9_result.get("provenance_complete")
                    ),
                    "risk_class": risk_class,
                },
                kas_invoked,
            )
            promotion_decision = str(
                self._required_output_value("KA-1079", promotion, "decision")
            )
        except Exception as exc:
            raise RuntimeError("Required Lane-B promotion gate failed") from exc

        return {
            "status": "proposal_only",
            "containment_class": containment_decision.get("containment_class"),
            "promotion_decision": promotion_decision,
            "promotion_authorized": promotion_decision == "approve",
            "effects_applied": False,
            "persistence_receipt": None,
            "owner": "GovernedExecutionOrchestrator",
        }

    def _make_containment_decision(
        self,
        input_data: L10Input,
        emergence: EmergenceAssessment,
        safety: SafetyCheckResult,
        trust: TrustGateResult,
        kas_invoked: list[str],
    ) -> tuple[L10Decision, str | None, list[ContainmentAction]]:
        """Decision tree mapping signals to containment actions."""
        actions = []
        final_answer = input_data.l9_result.get("epistemic_report", {}).get(
            "current_output", ""
        )
        privacy_findings = sum(
            violation.violation_type == "PII_leak" for violation in safety.violations
        )
        try:
            containment = self._execute_ka(
                "L10-KA-005",
                {
                    "final_action": "finalize",
                    "confidence": trust.decayed_confidence,
                    "emergence_detected": emergence.emergence_detected,
                    "violations": [
                        violation.model_dump()
                        for violation in safety.violations
                        if violation.violation_type != "PII_leak"
                    ],
                    "dependency_results": {
                        "L10-KA-002": {"level": emergence.overall_level.value},
                        "L10-KA-003": {"redactions_found": privacy_findings},
                        "L10-KA-004": {
                            "violations": [
                                violation.model_dump()
                                for violation in safety.violations
                                if violation.module == "ethics"
                            ]
                        },
                        "L10-KA-006": {
                            "passed": trust.status == "pass",
                            "decayed_confidence": (trust.decayed_confidence),
                        },
                        "L10-KA-007": {
                            "escalation_required": (
                                trust.action_required == "human_review"
                            )
                        },
                    },
                },
                kas_invoked,
            )
            containment_decision = str(
                self._required_output_value("L10-KA-005", containment, "decision")
            ).upper()
        except Exception as exc:
            raise RuntimeError("Required Layer-10 containment decision failed") from exc

        # 1. Critical Fail -> HALT
        if (
            containment_decision == "HALT"
            or not safety.release_approved
            or emergence.overall_level == EmergenceLevel.CRITICAL
        ):
            return (
                L10Decision.HALT,
                "Output halted due to critical safety/emergence violation.",
                actions,
            )

        # 2. Safety Violations -> MODIFY
        if safety.violations:
            for v in safety.violations:
                actions.append(
                    ContainmentAction(
                        action_type=v.recommended_action,
                        reason=v.violation_type,
                        description=v.description,
                    )
                )
            # Simulated redaction logic for PII violation
            if any(v.violation_type == "PII_leak" for v in safety.violations):
                import re

                final_answer = re.sub(
                    r"[\w\.-]+@[\w\.-]+", "[REDACTED EMAIL]", final_answer
                )

            if containment_decision == "ESCALATE":
                return L10Decision.ESCALATE, final_answer, actions
            return L10Decision.MODIFY, final_answer, actions

        # 3. Trust Fail -> ESCALATE or WITHHOLD
        if trust.status == "fail" or containment_decision == "ESCALATE":
            if trust.action_required == "human_review":
                return L10Decision.ESCALATE, final_answer, actions
            return (
                L10Decision.WITHHOLD,
                "Answer withheld due to internal confidence thresholds.",
                actions,
            )

        # 4. Standard Pass -> RELEASE
        return L10Decision.RELEASE, final_answer, actions

    def _generate_dsqp_seal(
        self,
        input_data: L10Input,
        emergence: EmergenceAssessment,
        safety: SafetyCheckResult,
    ) -> DSQPTraceSeal:
        """Create a deterministic integrity digest over the supplied trace."""
        trace_id = input_data.simulation_id
        sealed_payload = {
            "simulation_id": input_data.simulation_id,
            "reasoning_trace": input_data.reasoning_trace,
            "l9_result": input_data.l9_result,
            "coordinate_vector": input_data.coordinate_vector,
            "emergence": emergence.model_dump(mode="json"),
            "safety": safety.model_dump(mode="json"),
        }
        digest = hashlib.sha256(
            json.dumps(
                sealed_payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        return DSQPTraceSeal(
            trace_id=trace_id,
            hash_chain_root=f"sha256:{digest}",
            compliance_status=(
                "control_checks_passed"
                if safety.passed
                and emergence.overall_level
                not in {EmergenceLevel.HIGH, EmergenceLevel.CRITICAL}
                else "flagged"
            ),
        )

    def _create_failure_result(
        self, input_data: L10Input | None, error_msg: str, processing_time: float
    ) -> L10Result:
        """Fail-Closed result for Layer 10 errors."""
        sim_id = input_data.simulation_id if input_data else "unknown"
        logger.error(
            "Layer 10 authorization failed for simulation %s: %s",
            sim_id,
            error_msg,
        )
        return L10Result(
            simulation_id=sim_id,
            decision=L10Decision.HALT,
            final_answer=(
                "System error: Final safety gate failed to authorize release."
            ),
            trust_report=TrustGateResult(
                status="fail",
                domain_category=(input_data.risk_domain if input_data else "unknown"),
                required_threshold=1.0,
                original_confidence=0.0,
                decayed_confidence=0.0,
                gap=-1.0,
                action_required="human_review",
            ),
            dsqp_seal=DSQPTraceSeal(
                trace_id=sim_id, hash_chain_root="error", compliance_status="error"
            ),
            processing_time_ms=processing_time,
        )
