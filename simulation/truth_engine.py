"""
Truth Engine

Formal validation authority for UKG. Determines whether an answer
can be released based on multi-axis confidence, hard gates, and
tier-specific thresholds.

Truth = convergence, not opinion.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class TruthStatus(Enum):
    """Possible truth engine outcomes."""
    PASS = "pass"
    FAIL = "fail"
    REVISE = "revise"
    REFUSE = "refuse"


class GateType(Enum):
    """Types of validation gates."""
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    ETHICS = "ethics"
    FACTUAL = "factual"


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ConfidenceVector:
    """
    Axis-aware confidence vector.
    Each dimension corresponds to a confidence aspect.
    """
    # Core confidence dimensions
    factual: float = 0.0         # Claims verified against evidence
    logical: float = 0.0         # Internal consistency
    sector_fit: float = 0.0      # Industry appropriateness
    
    # Governance dimensions
    regulatory: float = 1.0      # External law/standards (binary-ish)
    compliance: float = 0.0      # Internal controls
    ethical: float = 0.0         # Bias, fairness
    security: float = 0.0        # Safety, misuse prevention
    
    # Risk dimensions
    risk_alignment: float = 0.0  # Axis 14 alignment
    
    # Computed
    overall: float = 0.0
    
    def compute_overall(self, weights: Dict[str, float] = None) -> float:
        """Compute weighted overall confidence."""
        default_weights = {
            "factual": 0.20,
            "logical": 0.15,
            "sector_fit": 0.10,
            "regulatory": 0.15,
            "compliance": 0.15,
            "ethical": 0.10,
            "security": 0.10,
            "risk_alignment": 0.05
        }
        weights = weights or default_weights
        
        total = 0.0
        for dim, weight in weights.items():
            total += getattr(self, dim, 0.0) * weight
        
        self.overall = total
        return total
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "factual": self.factual,
            "logical": self.logical,
            "sector_fit": self.sector_fit,
            "regulatory": self.regulatory,
            "compliance": self.compliance,
            "ethical": self.ethical,
            "security": self.security,
            "risk_alignment": self.risk_alignment,
            "overall": self.overall
        }
    
    def min_critical(self) -> float:
        """Minimum of critical dimensions."""
        return min(self.regulatory, self.compliance, self.security)


@dataclass
class GateResult:
    """Result of a single gate check."""
    gate_type: GateType
    passed: bool
    score: float = 0.0
    violations: List[str] = field(default_factory=list)
    veto: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_type": self.gate_type.value,
            "passed": self.passed,
            "score": self.score,
            "violations": self.violations,
            "veto": self.veto
        }


@dataclass
class TruthResult:
    """Complete truth engine evaluation result."""
    query_id: str = ""
    status: TruthStatus = TruthStatus.FAIL
    confidence_vector: ConfidenceVector = field(default_factory=ConfidenceVector)
    
    # Gate results
    gate_results: Dict[str, GateResult] = field(default_factory=dict)
    hard_gates_passed: bool = False
    
    # Tier
    tier: int = 3
    threshold_met: bool = False
    required_threshold: float = 0.95
    
    # Release decision
    release_authorized: bool = False
    
    # Actions
    actions: List[str] = field(default_factory=list)
    
    # Metadata
    evaluated_at: str = ""
    
    def __post_init__(self):
        if not self.evaluated_at:
            self.evaluated_at = datetime.now(UTC).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "status": self.status.value,
            "confidence_vector": self.confidence_vector.to_dict(),
            "gate_results": {k: v.to_dict() for k, v in self.gate_results.items()},
            "hard_gates_passed": self.hard_gates_passed,
            "tier": self.tier,
            "threshold_met": self.threshold_met,
            "required_threshold": self.required_threshold,
            "release_authorized": self.release_authorized,
            "actions": self.actions,
            "evaluated_at": self.evaluated_at
        }


# =============================================================================
# Truth Engine
# =============================================================================

class TruthEngine:
    """
    Truth Engine - Formal Validation Authority
    
    Computes axis-aware confidence, applies hard gates,
    and makes release decisions based on tier thresholds.
    """
    
    # Tier thresholds
    TIER_THRESHOLDS = {
        1: 0.85,
        2: 0.90,
        3: 0.95,
        4: 0.98,
        5: 0.995
    }
    
    # Critical dimension minimums by tier
    CRITICAL_MINIMUMS = {
        1: 0.70,
        2: 0.80,
        3: 0.90,
        4: 0.95,
        5: 0.99
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Truth Engine."""
        self.config = config or {}
        
        # Override thresholds
        if "tier_thresholds" in self.config:
            for tier, threshold in self.config["tier_thresholds"].items():
                self.TIER_THRESHOLDS[int(tier)] = threshold
        
        # Metrics
        self._evaluations = 0
        self._pass_count = 0
        self._fail_count = 0
        self._veto_count = 0
        
        logger.info("TruthEngine initialized")
    
    def evaluate(
        self,
        query_id: str,
        tier: int,
        persona_outputs: List[Dict[str, Any]] = None,
        layer_results: Dict[str, Any] = None,
        refinement_result: Dict[str, Any] = None
    ) -> TruthResult:
        """
        Evaluate and determine release authorization.
        
        Args:
            query_id: Query identifier
            tier: Execution tier (1-5)
            persona_outputs: Outputs from quad personas
            layer_results: Results from simulation layers
            refinement_result: Results from 12-step refinement
            
        Returns:
            TruthResult with status and release decision
        """
        self._evaluations += 1
        persona_outputs = persona_outputs or []
        layer_results = layer_results or {}
        refinement_result = refinement_result or {}
        
        logger.info(f"TruthEngine evaluating query {query_id} at tier {tier}")
        
        # Step 1: Compute confidence vector
        confidence = self._compute_confidence(
            persona_outputs, layer_results, refinement_result
        )
        
        # Step 2: Check hard gates
        gate_results = self._check_gates(persona_outputs, layer_results)
        hard_gates_passed = all(
            g.passed and not g.veto 
            for g in gate_results.values()
        )
        
        # Step 3: Check tier threshold
        threshold = self.TIER_THRESHOLDS.get(tier, 0.95)
        threshold_met = confidence.overall >= threshold
        
        # Step 4: Check critical minimums
        critical_min = self.CRITICAL_MINIMUMS.get(tier, 0.90)
        critical_passed = confidence.min_critical() >= critical_min
        
        # Step 5: Determine status and release
        status, release, actions = self._determine_outcome(
            hard_gates_passed, threshold_met, critical_passed, confidence, tier
        )
        
        # Build result
        result = TruthResult(
            query_id=query_id,
            status=status,
            confidence_vector=confidence,
            gate_results=gate_results,
            hard_gates_passed=hard_gates_passed,
            tier=tier,
            threshold_met=threshold_met,
            required_threshold=threshold,
            release_authorized=release,
            actions=actions
        )
        
        # Update metrics
        if status == TruthStatus.PASS:
            self._pass_count += 1
        elif status == TruthStatus.FAIL:
            self._fail_count += 1
        
        if any(g.veto for g in gate_results.values()):
            self._veto_count += 1
        
        logger.info(f"TruthEngine result: {status.value}, release={release}")
        
        return result
    
    def _compute_confidence(
        self,
        persona_outputs: List[Dict[str, Any]],
        layer_results: Dict[str, Any],
        refinement_result: Dict[str, Any]
    ) -> ConfidenceVector:
        """Compute axis-aware confidence vector."""
        cv = ConfidenceVector()
        
        # Aggregate persona confidences
        if persona_outputs:
            factual_scores = []
            logical_scores = []
            
            for po in persona_outputs:
                pconf = po.get("confidence_vector", {})
                if "factual" in pconf:
                    factual_scores.append(pconf["factual"])
                if "logical" in pconf:
                    logical_scores.append(pconf["logical"])
            
            if factual_scores:
                cv.factual = sum(factual_scores) / len(factual_scores)
            if logical_scores:
                cv.logical = sum(logical_scores) / len(logical_scores)
        else:
            # Default moderate confidence when no persona outputs
            cv.factual = 0.80
            cv.logical = 0.80
        
        # Sector fit from layer results
        cv.sector_fit = layer_results.get("confidence", {}).get("sector_fit", 0.85)
        
        # Regulatory: Check P10 outputs (hard requirement)
        p10_outputs = [p for p in persona_outputs if p.get("persona_id") == "P10"]
        if p10_outputs:
            p10_conf = p10_outputs[0].get("confidence_vector", {})
            cv.regulatory = p10_conf.get("regulatory", 1.0)
            if p10_outputs[0].get("veto_flag"):
                cv.regulatory = 0.0
        else:
            cv.regulatory = 0.95  # Assume compliant if no P10
        
        # Compliance: Check P11 outputs
        p11_outputs = [p for p in persona_outputs if p.get("persona_id") == "P11"]
        if p11_outputs:
            p11_conf = p11_outputs[0].get("confidence_vector", {})
            cv.compliance = p11_conf.get("compliance", 0.90)
            if p11_outputs[0].get("veto_flag"):
                cv.compliance = 0.0
        else:
            cv.compliance = 0.90
        
        # Ethics from refinement
        cv.ethical = refinement_result.get("ethics_score", 0.95)
        
        # Security from refinement
        cv.security = refinement_result.get("security_score", 0.95)
        
        # Risk alignment from layer 6/7
        cv.risk_alignment = layer_results.get("confidence", {}).get("risk_alignment", 0.90)
        
        # Compute overall
        cv.compute_overall()
        
        return cv
    
    def _check_gates(
        self,
        persona_outputs: List[Dict[str, Any]],
        layer_results: Dict[str, Any]
    ) -> Dict[str, GateResult]:
        """Check all hard gates."""
        gates = {}
        
        # Regulatory gate (P10 veto)
        reg_violations = []
        reg_veto = False
        for po in persona_outputs:
            if po.get("persona_id") == "P10":
                if po.get("veto_flag"):
                    reg_veto = True
                    reg_violations.extend(po.get("veto_conditions", []))
        
        gates["regulatory"] = GateResult(
            gate_type=GateType.REGULATORY,
            passed=not reg_veto,
            score=1.0 if not reg_veto else 0.0,
            violations=reg_violations,
            veto=reg_veto
        )
        
        # Compliance gate (P11 veto)
        comp_violations = []
        comp_veto = False
        for po in persona_outputs:
            if po.get("persona_id") == "P11":
                if po.get("veto_flag"):
                    comp_veto = True
                    comp_violations.extend(po.get("veto_conditions", []))
        
        gates["compliance"] = GateResult(
            gate_type=GateType.COMPLIANCE,
            passed=not comp_veto,
            score=1.0 if not comp_veto else 0.0,
            violations=comp_violations,
            veto=comp_veto
        )
        
        # Security gate
        security_flags = layer_results.get("security_flags", [])
        sec_passed = len(security_flags) == 0
        
        gates["security"] = GateResult(
            gate_type=GateType.SECURITY,
            passed=sec_passed,
            score=1.0 if sec_passed else 0.0,
            violations=security_flags,
            veto=not sec_passed
        )
        
        # Ethics gate
        ethics_flags = layer_results.get("ethics_flags", [])
        eth_passed = len(ethics_flags) == 0
        
        gates["ethics"] = GateResult(
            gate_type=GateType.ETHICS,
            passed=eth_passed,
            score=1.0 if eth_passed else 0.5,
            violations=ethics_flags,
            veto=False  # Ethics is soft gate
        )
        
        return gates
    
    def _determine_outcome(
        self,
        hard_gates_passed: bool,
        threshold_met: bool,
        critical_passed: bool,
        confidence: ConfidenceVector,
        tier: int
    ) -> tuple:
        """Determine final outcome."""
        actions = []
        
        # Hard gate failure -> REFUSE or FAIL
        if not hard_gates_passed:
            if confidence.regulatory < 0.5 or confidence.security < 0.5:
                actions.append("refuse_due_to_hard_violation")
                return TruthStatus.REFUSE, False, actions
            else:
                actions.append("revise_to_address_violations")
                return TruthStatus.REVISE, False, actions
        
        # Critical dimension failure
        if not critical_passed:
            actions.append("revise_to_improve_critical_dimensions")
            return TruthStatus.REVISE, False, actions
        
        # Threshold not met
        if not threshold_met:
            if tier >= 4:
                # High tier requires threshold
                actions.append("rerun_refinement_to_improve_confidence")
                return TruthStatus.REVISE, False, actions
            else:
                # Lower tier can pass with warning
                actions.append("release_with_reduced_confidence_warning")
                return TruthStatus.PASS, True, actions
        
        # All passed
        actions.append("release_authorized")
        return TruthStatus.PASS, True, actions
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Truth Engine metrics."""
        return {
            "total_evaluations": self._evaluations,
            "pass_count": self._pass_count,
            "fail_count": self._fail_count,
            "veto_count": self._veto_count,
            "pass_rate": self._pass_count / max(1, self._evaluations)
        }


# =============================================================================
# Factory
# =============================================================================

def create_truth_engine(config: Dict[str, Any] = None) -> TruthEngine:
    """Create and configure a TruthEngine instance."""
    return TruthEngine(config)
