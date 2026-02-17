"""
Layer 10: EmergenceDetectionController

The EmergenceDetectionController is the final safety gate and release authority
of the UKG 10-layer stack. It performs emergence detection, safety audit,
and makes the final binary RELEASE vs CONTAIN decision.
"""

import logging
import time
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
    Layer 10: EmergenceDetectionController (The Sentinel)
    
    The Final Guardian. Orchestrates two operational lanes:
    - Lane A (Response Gate): Real-time safety, emergence, and release authority.
    - Lane B (Knowledge Commit): Authorized persistence of reasoning and learning.
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
    
    # Canonical KAs for Lane A (Response Gate)
    LANE_A_KAS = [
        "KA-021", "KA-108", "KA-116",  # Emergence/Drift
        "KA-058", "KA-059", "KA-061", "KA-063", "KA-027",  # Safety/Ethics
        "KA-014", "KA-023", "KA-095", "KA-062"  # Trust/Governance
    ]

    # Canonical KAs for Lane B (Knowledge Commit)
    LANE_B_KAS = [
        "KA-109", "KA-079", "KA-050", "KA-094",  # Commit/Classification
        "KA-065", "KA-083", "KA-088", "KA-096"  # Lifecycle/Regression
    ]

    def __init__(self, ka_controller=None, config: Optional[Dict] = None):
        self.ka_controller = ka_controller
        self.config = config or {}
        logger.info("EmergenceDetectionController (Layer 10 Sentinel) initialized")

    def authorize(self, input_data: Optional[L10Input]) -> L10Result:
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
                input_data, emergence_report, safety_report, trust_report
            )
            
            # --- LANE B: Knowledge Commit (Async/Deferred Logic) ---
            if decision in [L10Decision.RELEASE, L10Decision.MODIFY]:
                self._process_knowledge_commit_lane_b(input_data, kas_invoked)
            
            # 5. DSQP Trace Finalization (Axis 15)
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
                requires_human_signoff=(trust_report.action_required == "human_review") or (decision == L10Decision.ESCALATE)
            )

        except Exception as e:
            logger.error(f"Layer 10 Sentinel Critical Failure: {e}", exc_info=True)
            return self._create_failure_result(input_data, str(e), (time.time() - start_time) * 1000)

    def _detect_emergence_lane_a(self, input_data: L10Input, kas_invoked: List[str]) -> EmergenceAssessment:
        """Detect emergent behaviors and capability drift using canonical and L10 KAs."""
        assessment = EmergenceAssessment()
        content = input_data.l9_result.get("epistemic_report", {}).get("current_output", "")
        
        if not self.ka_controller:
            return assessment

        # KA-021: Emergence Detection (General)
        try:
            ka_res = self.ka_controller.execute_algorithm("KA-021", {"content": content, "trace": input_data.reasoning_trace})
            kas_invoked.append("KA-021")
            if ka_res.get("emergence_detected"):
                assessment.emergence_detected = True
                assessment.overall_level = EmergenceLevel.MODERATE
        except Exception as e:
            logger.debug(f"KA-021 failed: {e}")

        # KA-108: Capability Escalation (Unsafe drift)
        try:
            ka_res = self.ka_controller.execute_algorithm("KA-108", {"content": content, "problem_spec": input_data.problem_spec})
            kas_invoked.append("KA-108")
            if ka_res.get("escalation_detected"):
                assessment.patterns.append(EmergencePattern(
                    pattern_type="capability_escalation",
                    location="reasoning_path",
                    description="AI attempted to bypass safety bounds",
                    risk_level=EmergenceLevel.HIGH,
                    score=0.9
                ))
        except Exception as e:
            logger.debug(f"KA-108 failed: {e}")

        # L10-KA-001/002: Entropy and Self-Awareness
        try:
            ka_res = self.ka_controller.execute_algorithm("L10-KA-001", {"content": content})
            kas_invoked.append("L10-KA-001")
            assessment.entropy_delta = ka_res.get("entropy_score", 0.0)
            
            ka_res = self.ka_controller.execute_algorithm("L10-KA-002", {"content": content})
            kas_invoked.append("L10-KA-002")
            if ka_res.get("awareness_detected"):
                assessment.patterns.append(EmergencePattern(
                    pattern_type="self_referential",
                    location="output",
                    description="Self-awareness indicators found",
                    risk_level=EmergenceLevel.LOW,
                    score=0.3
                ))
        except Exception as e:
            logger.debug(f"L10-KA-001/2 failed: {e}")

        return assessment

    def _run_safety_audit_lane_a(self, input_data: L10Input, kas_invoked: List[str]) -> SafetyCheckResult:
        """Sequential safety and policy audit."""
        result = SafetyCheckResult()
        content = input_data.l9_result.get("epistemic_report", {}).get("current_output", "")
        
        if not self.ka_controller:
            return result

        # Safety & Privacy Baseline (KA-058, KA-059)
        for ka_id in ["KA-058", "KA-059"]:
            try:
                ka_res = self.ka_controller.execute_algorithm(ka_id, {"content": content})
                kas_invoked.append(ka_id)
                if not ka_res.get("passed", True):
                    result.passed = False
                    v_type = "PII_leak" if ka_id == "KA-059" else "safety_violation"
                    result.violations.append(SafetyViolation(
                        module="standard_safety",
                        violation_type=v_type,
                        severity="major",
                        description=f"{ka_id} flag: {ka_res.get('flag', 'Unknown')}",
                        recommended_action="redact" if ka_id == "KA-059" else "withhold"
                    ))
            except Exception as e:
                logger.debug(f"{ka_id} failed: {e}")

        # Ethics Validator (L10-KA-004 + KA-027)
        try:
            ka_res = self.ka_controller.execute_algorithm("L10-KA-004", {"content": content})
            kas_invoked.append("L10-KA-004")
            if ka_res.get("violations"):
                result.passed = False
                for v in ka_res["violations"]:
                    result.violations.append(SafetyViolation(
                        module="ethics",
                        violation_type=v["type"],
                        severity=v["severity"],
                        description=v["message"],
                        recommended_action="modify"
                    ))
        except Exception as e:
            logger.debug(f"L10-KA-004 failed: {e}")

        result.release_approved = len([v for v in result.violations if v.severity == "critical"]) == 0
        return result

    def _evaluate_trust_gate_lane_a(self, input_data: L10Input, kas_invoked: List[str]) -> TrustGateResult:
        """Enforce domain thresholds with belief decay and Axis 17 governance."""
        orig_conf = input_data.l9_result.get("readiness_score", 1.0)
        decayed_conf = orig_conf * BELIEF_DECAY_FACTOR
        
        domain = input_data.risk_domain
        threshold = TRUST_THRESHOLDS.get(domain, 0.95)
        
        status = "pass" if decayed_conf >= threshold else "fail"
        action = "none"
        
        if status == "fail":
            action = "human_review" if domain == "high_risk" else "refinement"
            # KA-095: Human-in-the-Loop Escalation
            if action == "human_review" and self.ka_controller:
                try:
                    self.ka_controller.execute_algorithm("KA-095", {"problem": input_data.problem_spec, "reason": "high_risk_low_confidence"})
                    kas_invoked.append("KA-095")
                except Exception:
                    pass
            
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

    def _process_knowledge_commit_lane_b(self, input_data: L10Input, kas_invoked: List[str]) -> Dict[str, Any]:
        """Authorized persistence logic (Lane B). Decides if knowledge is saved."""
        commit_report = {"status": "authorized"}
        
        if not self.ka_controller:
            return commit_report

        # KA-109: Containment Classifier (Tagging)
        try:
            ka_res = self.ka_controller.execute_algorithm("KA-109", {"content": input_data.reasoning_trace})
            kas_invoked.append("KA-109")
            commit_report["containment_class"] = ka_res.get("class", "RESTRICTED")
        except Exception:
            pass

        # KA-079: Knowledge Promotion Gate
        try:
            ka_res = self.ka_controller.execute_algorithm("KA-079", {"trace": input_data.reasoning_trace})
            kas_invoked.append("KA-079")
            commit_report["promotion_authorized"] = ka_res.get("authorized", False)
        except Exception:
            pass

        return commit_report

    def _make_containment_decision(self, 
                                  input_data: L10Input, 
                                  emergence: EmergenceAssessment,
                                  safety: SafetyCheckResult,
                                  trust: TrustGateResult) -> Tuple[L10Decision, Optional[str], List[ContainmentAction]]:
        """Decision tree mapping signals to containment actions."""
        actions = []
        final_answer = input_data.l9_result.get("epistemic_report", {}).get("current_output", "")
        
        # 1. Critical Fail -> HALT
        if not safety.release_approved or emergence.overall_level == EmergenceLevel.CRITICAL:
            return L10Decision.HALT, "Output halted due to critical safety/emergence violation.", actions
            
        # 2. Safety Violations -> MODIFY
        if safety.violations:
            for v in safety.violations:
                actions.append(ContainmentAction(
                    action_type=v.recommended_action,
                    reason=v.violation_type,
                    description=v.description
                ))
            # Simulated redaction logic for PII violation
            if any(v.violation_type == "PII_leak" for v in safety.violations):
                import re
                final_answer = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED EMAIL]', final_answer)
                
            return L10Decision.MODIFY, final_answer, actions
            
        # 3. Trust Fail -> ESCALATE or WITHHOLD
        if trust.status == "fail":
            if trust.action_required == "human_review":
                return L10Decision.ESCALATE, final_answer, actions
            return L10Decision.WITHHOLD, "Answer withheld due to internal confidence thresholds.", actions
            
        # 4. Standard Pass -> RELEASE
        return L10Decision.RELEASE, final_answer, actions

    def _generate_dsqp_seal(self, 
                           input_data: L10Input, 
                           emergence: EmergenceAssessment, 
                           safety: SafetyCheckResult) -> DSQPTraceSeal:
        """Axis 15: Create immutable audit seal."""
        trace_id = input_data.simulation_id
        # In production, this would involve sha256 of the concatenated L1-L9 trace objects
        return DSQPTraceSeal(
            trace_id=trace_id,
            hash_chain_root="sha256:d826... sentinel_sealed",
            compliance_status="compliant" if safety.passed and emergence.overall_level != EmergenceLevel.HIGH else "flagged"
        )

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
