"""
Layer 10: EmergenceDetectionController

The EmergenceDetectionController is the final safety gate and release authority
of the UKG 10-layer stack. It performs emergence detection, safety audit,
and makes the final binary RELEASE vs CONTAIN decision.
"""

import logging
import time
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Tuple

from .l10_schemas import (
    L10Decision,
    EmergenceLevel,
    EmergencePattern,
    EmergenceAssessment,
    SafetyViolation,
    SafetyCheckResult,
    TrustGateResult,
    ContainmentAction,
    DSQPTraceSeal,
    L10Input,
    L10Result
)

logger = logging.getLogger(__name__)

# Trust thresholds with belief decay factored in
TRUST_THRESHOLDS = {
    "standard": 0.95,
    "high_risk": 0.985
}

# Belief decay factor (98% nudge)
BELIEF_DECAY_FACTOR = 0.98

# Max processing time for safety checks
MAX_SAFETY_TIME_MS = 20000


class EmergenceDetectionController:
    """
    Layer 10: EmergenceDetectionController
    
    The Final Guardian. Ensures no harmful content, privacy violations,
    unethical advice, or AGI-like runaway behaviors escape to the user.
    """
    
    # L10 specific KA suite
    L10_KAS = [
        "L10-KA-001",  # Entropy-Based Emergence Scorer
        "L10-KA-002",  # Self-Awareness Monitor
        "L10-KA-003",  # Privacy & PII Redactor
        "L10-KA-004",  # Ethical Alignment Validator
        "L10-KA-005",  # Containment Decision Engine
        "L10-KA-006",  # Terminal Trust Gate (Belief Decay)
        "L10-KA-007",  # Human Escalation Router (Axis 17)
    ]
    
    # Canonical KAs from registry
    CANONICAL_KAS = [
        "KA-021",  # Emergence Detection (General)
        "KA-108",  # Capability Escalation Detector (unsafe drift)
        "KA-109",  # Knowledge Containment Classifier
        "KA-095",  # Human-in-the-Loop Escalation
    ]

    def __init__(self, ka_controller=None, config: Optional[Dict] = None):
        self.ka_controller = ka_controller
        self.config = config or {}
        logger.info("EmergenceDetectionController (Layer 10) initialized")

    def authorize(self, input_data: Optional[L10Input]) -> L10Result:
        """
        Final release authority gate.
        """
        start_time = time.time()
        kas_invoked = []
        
        if input_data is None:
            return self._create_failure_result(None, "Input data is None", 0.0)

        try:
            # Component 1: Emergence Detection
            emergence_report = self._detect_emergence(input_data, kas_invoked)
            
            # Component 2: Safety & Policy Enforcement
            safety_report = self._run_safety_audit(input_data, kas_invoked)
            
            # Component 3: Trust Gate (Belief Decay)
            trust_report = self._evaluate_trust_gate(input_data, kas_invoked)
            
            # Additional canonical checks
            canonical_results = self._run_canonical_safety_checks(input_data, kas_invoked)
            self._integrate_canonical_findings(safety_report, emergence_report, canonical_results)
            
            # Component 4: Containment Decision Tree
            decision, final_answer, actions = self._make_containment_decision(
                input_data, emergence_report, safety_report, trust_report
            )
            
            # Component 5: DSQP Trace Finalization (Axis 15)
            dsqp_seal = self._generate_dsqp_seal(input_data, emergence_report, safety_report)
            
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
                requires_human_signoff=trust_report.action_required == "human_review"
            )

        except Exception as e:
            logger.error(f"Layer 10 Critical Failure: {e}")
            # Final Safety: FAIL OPEN is NOT ALLOWED. Default to HALT/CONTAIN on error.
            return self._create_failure_result(input_data, str(e), (time.time() - start_time) * 1000)

    def _detect_emergence(self, input_data: L10Input, kas_invoked: List[str]) -> EmergenceAssessment:
        """Component 1: Detect emergent behaviors and unintended patterns."""
        # Simulated logic for now, calling L10-KA-001/002
        assessment = EmergenceAssessment()
        
        # KA-021: Canonical Emergence Detection
        # L10-KA-001: Entropy Scorer
        # L10-KA-002: Self-Awareness Monitor
        
        # Placeholder score calculation
        l9_sol = str(input_data.l9_result.get("epistemic_report", {}))
        if "I am" in l9_sol or "I think" in l9_sol:
            assessment.emergence_detected = True
            assessment.overall_level = EmergenceLevel.LOW
            assessment.patterns.append(EmergencePattern(
                pattern_type="self_referential",
                location="solution_text",
                description="AI making statements about itself",
                risk_level=EmergenceLevel.LOW,
                score=0.4
            ))
            kas_invoked.append("L10-KA-002")
            
        return assessment

    def _run_safety_audit(self, input_data: L10Input, kas_invoked: List[str]) -> SafetyCheckResult:
        """Component 2: Enforce safety rules and policy compliance."""
        result = SafetyCheckResult()
        
        # Calling L10-KA-003, L10-KA-004
        l9_sol = input_data.l9_result.get("epistemic_report", {}).get("current_output", "") or ""
        
        # PII Check (Simulated)
        if "@" in l9_sol and ".com" in l9_sol:
            result.passed = False
            result.violations.append(SafetyViolation(
                module="privacy",
                violation_type="PII_leak",
                severity="major",
                description="Potential email address detected in output",
                recommended_action="redact"
            ))
            kas_invoked.append("L10-KA-003")
            
        result.release_approved = len([v for v in result.violations if v.severity == "critical"]) == 0
        return result

    def _evaluate_trust_gate(self, input_data: L10Input, kas_invoked: List[str]) -> TrustGateResult:
        """Component 3: Enforce domain thresholds with belief decay."""
        orig_conf = input_data.l9_result.get("readiness_score", 1.0)
        decayed_conf = orig_conf * BELIEF_DECAY_FACTOR
        
        domain = input_data.risk_domain
        threshold = TRUST_THRESHOLDS.get(domain, 0.95)
        
        status = "pass" if decayed_conf >= threshold else "fail"
        action = "none"
        if status == "fail":
            action = "human_review" if domain == "high_risk" else "refinement"
            
        kas_invoked.append("L10-KA-006")
        
        return TrustGateResult(
            status=status,
            domain_category=domain,
            required_threshold=threshold,
            original_confidence=orig_conf,
            decayed_confidence=decayed_conf,
            gap=decayed_conf - threshold,
            action_required=action
        )

    def _make_containment_decision(self, 
                                  input_data: L10Input, 
                                  emergence: EmergenceAssessment,
                                  safety: SafetyCheckResult,
                                  trust: TrustGateResult) -> Tuple[L10Decision, Optional[str], List[ContainmentAction]]:
        """Component 4: Final decision based on all signals."""
        actions = []
        final_answer = input_data.l9_result.get("epistemic_report", {}).get("current_output", "")
        
        # 1. Critical Fail -> HALT
        if not safety.release_approved or emergence.overall_level == EmergenceLevel.CRITICAL:
            return L10Decision.HALT, "Output halted due to safety/emergence policy violation.", actions
            
        # 2. Safety Violations -> MODIFY
        if safety.violations:
            for v in safety.violations:
                if v.recommended_action == "redact":
                    actions.append(ContainmentAction(
                        action_type="redaction",
                        reason=v.violation_type,
                        description=v.description
                    ))
            return L10Decision.MODIFY, final_answer, actions # Implementation of modification logic would go here
            
        # 3. Trust Fail -> ESCALATE or WITHHOLD
        if trust.status == "fail":
            if trust.action_required == "human_review":
                return L10Decision.ESCALATE, final_answer, actions
            return L10Decision.WITHHOLD, "Answer withheld due to low confidence.", actions
            
        # 4. Standard Pass -> RELEASE
        return L10Decision.RELEASE, final_answer, actions

    def _generate_dsqp_seal(self, 
                           input_data: L10Input, 
                           emergence: EmergenceAssessment, 
                           safety: SafetyCheckResult) -> DSQPTraceSeal:
        """Component 5: Immutable audit seal for Axis 15."""
        # In a real system, this would involve hashing the L1-L9 trace.
        # Here we simulate with a placeholder hash.
        trace_id = input_data.simulation_id
        return DSQPTraceSeal(
            trace_id=trace_id,
            hash_chain_root="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            compliance_status="compliant" if safety.passed else "non_compliant"
        )

    def _run_canonical_safety_checks(self, input_data: L10Input, kas_invoked: List[str]) -> Dict[str, Any]:
        """Run canonical KAs like KA-021, KA-108, KA-109."""
        results = {}
        if not self.ka_controller:
            return results
            
        # Simulated calls
        for ka_id in self.CANONICAL_KAS:
            try:
                # result = self.ka_controller.execute_algorithm(ka_id, {...})
                # kas_invoked.append(ka_id)
                pass
            except Exception:
                pass
        return results

    def _integrate_canonical_findings(self, safety: SafetyCheckResult, emergence: EmergenceAssessment, canonical: Dict[str, Any]):
        """Merge canonical KA findings into L10 reports."""
        pass

    def _create_failure_result(self, input_data: Optional[L10Input], error_msg: str, processing_time: float) -> L10Result:
        """Fail-Closed result for Layer 10 errors."""
        sim_id = input_data.simulation_id if input_data else "unknown"
        return L10Result(
            simulation_id=sim_id,
            decision=L10Decision.HALT,
            final_answer=f"System error: Final safety gate failed to authorize release. Details: {error_msg}",
            dsqp_seal=DSQPTraceSeal(trace_id=sim_id, hash_chain_root="error", compliance_status="error"),
            processing_time_ms=processing_time
        )
