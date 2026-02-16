"""
POV Policy & Roster Service

Enterprise-grade decisioning engine that determines POV execution mode and
selects the viewpoint roster based on scoring signals and budget constraints.

This service answers: "How much POV should we apply to this query?"
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================

class POVMode(Enum):
    """POV execution modes."""
    BYPASS = "bypass"           # Skip POV entirely (trivial queries)
    LIGHT = "light"             # 1-2 stakeholder lenses + auditor
    STANDARD = "standard"       # Base quad + 2-3 viewpoints
    COMMITTEE = "committee"     # Full pod expansion (high-stakes)


class SignalLevel(Enum):
    """Signal intensity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ScoringSignals:
    """
    Signals used to determine POV mode and roster.
    
    All scores are normalized 0-100 for consistency.
    """
    breadth_score: float = 0.0      # Number of activated pillars/sectors
    stakes_score: float = 0.0       # Safety-critical / defense / regulated
    conflict_score: float = 0.0     # Unresolved contradictions (0-1)
    coverage_score: float = 0.0     # Required artifacts present (0-1)
    
    # Domain flags
    is_defense: bool = False
    is_safety_critical: bool = False
    is_export_controlled: bool = False
    is_heavily_regulated: bool = False
    
    # Counts
    pillars_activated: int = 0
    sectors_activated: int = 0
    subsystems_detected: int = 0
    
    def overall_complexity(self) -> float:
        """Calculate overall complexity score."""
        return (self.breadth_score * 0.3 + 
                self.stakes_score * 0.4 + 
                self.conflict_score * 100 * 0.15 +
                (1 - self.coverage_score) * 100 * 0.15)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "breadth_score": self.breadth_score,
            "stakes_score": self.stakes_score,
            "conflict_score": self.conflict_score,
            "coverage_score": self.coverage_score,
            "is_defense": self.is_defense,
            "is_safety_critical": self.is_safety_critical,
            "is_export_controlled": self.is_export_controlled,
            "is_heavily_regulated": self.is_heavily_regulated,
            "pillars_activated": self.pillars_activated,
            "sectors_activated": self.sectors_activated,
            "subsystems_detected": self.subsystems_detected,
            "overall_complexity": self.overall_complexity()
        }


@dataclass
class POVBudget:
    """Budget constraints for POV execution."""
    max_ms: int = 5000              # Wall-clock timeout
    max_viewpoints: int = 12        # Maximum viewpoints to execute
    max_recursions: int = 3         # Maximum recursive passes
    max_parallel: int = 4           # Concurrent viewpoint execution
    
    # Per-lane caps
    knowledge_max: int = 6
    sector_max: int = 6
    regulatory_max: int = 3
    compliance_max: int = 3
    stakeholder_max: int = 4
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "max_ms": self.max_ms,
            "max_viewpoints": self.max_viewpoints,
            "max_recursions": self.max_recursions,
            "max_parallel": self.max_parallel,
            "knowledge_max": self.knowledge_max,
            "sector_max": self.sector_max,
            "regulatory_max": self.regulatory_max,
            "compliance_max": self.compliance_max,
            "stakeholder_max": self.stakeholder_max
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POVBudget":
        """Create from dictionary."""
        return cls(
            max_ms=data.get("max_ms", 5000),
            max_viewpoints=data.get("max_viewpoints", 12),
            max_recursions=data.get("max_recursions", 3),
            max_parallel=data.get("max_parallel", 4),
            knowledge_max=data.get("knowledge_max", 6),
            sector_max=data.get("sector_max", 6),
            regulatory_max=data.get("regulatory_max", 3),
            compliance_max=data.get("compliance_max", 3),
            stakeholder_max=data.get("stakeholder_max", 4)
        )


@dataclass
class ViewpointSelection:
    """A selected viewpoint for execution."""
    viewpoint_id: str
    name: str
    lane: str                       # Knowledge/Sector/Regulatory/Compliance/Stakeholder
    priority: int = 1               # 1=highest priority
    reason: str = ""                # Why selected
    timeout_ms: int = 1000          # Per-viewpoint timeout


@dataclass
class POVPlan:
    """
    Complete POV execution plan.
    
    Output of the POV Policy Service.
    """
    plan_id: str = ""
    mode: POVMode = POVMode.STANDARD
    policy_mode: str = "standard"   # standard | high_assurance
    
    # Selected viewpoints
    viewpoints: List[ViewpointSelection] = field(default_factory=list)
    
    # Per-lane counts
    lane_counts: Dict[str, int] = field(default_factory=dict)
    
    # Signals used for decision
    signals: Optional[ScoringSignals] = None
    
    # Budget applied
    budget: Optional[POVBudget] = None
    
    # Stop conditions
    target_confidence: float = 0.995
    stop_on_critical_conflict: bool = True
    
    # Metadata
    created_at: str = ""
    decision_reasons: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.plan_id:
            import uuid
            self.plan_id = f"pov_plan_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        if not self.lane_counts:
            self.lane_counts = {
                "knowledge": 0,
                "sector": 0,
                "regulatory": 0,
                "compliance": 0,
                "stakeholder": 0
            }
    
    @property
    def total_viewpoints(self) -> int:
        """Total viewpoints in plan."""
        return len(self.viewpoints)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "plan_id": self.plan_id,
            "mode": self.mode.value,
            "policy_mode": self.policy_mode,
            "viewpoints": [
                {
                    "viewpoint_id": v.viewpoint_id,
                    "name": v.name,
                    "lane": v.lane,
                    "priority": v.priority,
                    "reason": v.reason
                }
                for v in self.viewpoints
            ],
            "lane_counts": self.lane_counts,
            "total_viewpoints": self.total_viewpoints,
            "signals": self.signals.to_dict() if self.signals else None,
            "budget": self.budget.to_dict() if self.budget else None,
            "target_confidence": self.target_confidence,
            "decision_reasons": self.decision_reasons,
            "created_at": self.created_at
        }


# =============================================================================
# POV Policy Service
# =============================================================================

class POVPolicyService:
    """
    Enterprise POV Policy & Roster Service.
    
    Decides whether POV runs in light, standard, or committee mode and
    selects which viewpoints to execute based on scoring signals and budget.
    """
    
    # Mode thresholds
    BYPASS_THRESHOLD = 15           # Below this = skip POV
    LIGHT_THRESHOLD = 35            # Below this = light mode
    STANDARD_THRESHOLD = 60         # Below this = standard mode
    # Above STANDARD_THRESHOLD = committee mode
    
    # High-assurance adjustments
    HIGH_ASSURANCE_THRESHOLD_REDUCTION = 15
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the policy service."""
        self.config = config or {}
        
        # Load threshold overrides from config
        if "thresholds" in self.config:
            t = self.config["thresholds"]
            self.BYPASS_THRESHOLD = t.get("bypass", self.BYPASS_THRESHOLD)
            self.LIGHT_THRESHOLD = t.get("light", self.LIGHT_THRESHOLD)
            self.STANDARD_THRESHOLD = t.get("standard", self.STANDARD_THRESHOLD)
        
        # Default budgets by policy mode
        self.default_budgets = {
            "standard": POVBudget(
                max_ms=5000,
                max_viewpoints=8,
                max_recursions=2
            ),
            "high_assurance": POVBudget(
                max_ms=10000,
                max_viewpoints=16,
                max_recursions=5
            )
        }
        
        logger.info("POVPolicyService initialized")
    
    def evaluate(
        self,
        query: str,
        context: Dict[str, Any],
        quad_outputs: Dict[str, Any] = None,
        budget: POVBudget = None,
        policy_mode: str = "standard"
    ) -> POVPlan:
        """
        Evaluate query and generate POV execution plan.
        
        Args:
            query: Query text
            context: Query context with coordinate mappings
            quad_outputs: Results from base quad persona processing
            budget: Optional budget constraints
            policy_mode: "standard" or "high_assurance"
            
        Returns:
            POVPlan with mode, viewpoints, and execution parameters
        """
        logger.info(f"Evaluating POV policy for query: {query[:50]}...")
        
        # Use default budget if not provided
        if budget is None:
            budget = self.default_budgets.get(policy_mode, self.default_budgets["standard"])
        
        # Step 1: Compute scoring signals
        signals = self._compute_signals(query, context, quad_outputs)
        
        # Step 2: Determine if high-assurance mode should be forced
        if self._should_force_high_assurance(signals):
            policy_mode = "high_assurance"
            budget = self.default_budgets["high_assurance"]
        
        # Step 3: Select POV mode based on signals
        mode = self._select_mode(signals, policy_mode)
        
        # Step 4: Select viewpoints based on mode
        viewpoints, lane_counts = self._select_viewpoints(
            signals, mode, context, budget
        )
        
        # Step 5: Build plan
        plan = POVPlan(
            mode=mode,
            policy_mode=policy_mode,
            viewpoints=viewpoints,
            lane_counts=lane_counts,
            signals=signals,
            budget=budget,
            target_confidence=0.995 if policy_mode == "high_assurance" else 0.95
        )
        
        # Add decision reasons
        plan.decision_reasons = self._generate_decision_reasons(signals, mode)
        
        logger.info(f"POV plan created: mode={mode.value}, viewpoints={plan.total_viewpoints}")
        
        return plan
    
    def _compute_signals(
        self,
        query: str,
        context: Dict[str, Any],
        quad_outputs: Dict[str, Any]
    ) -> ScoringSignals:
        """Compute all scoring signals from query and context."""
        signals = ScoringSignals()
        query_lower = query.lower()
        
        # Domain flags - check for high-stakes domains
        defense_keywords = {
            "weapon", "military", "defense", "dod", "classified",
            "fighter", "bomber", "missile", "f-22", "f-35", "b-21"
        }
        safety_keywords = {
            "safety", "safety-critical", "airworthiness", "do-178",
            "hazard", "catastrophic", "life-critical"
        }
        export_keywords = {
            "itar", "ear", "export control", "technology control",
            "classified", "cui", "noforn"
        }
        regulated_keywords = {
            "hipaa", "gdpr", "pci", "sox", "far", "dfars",
            "fda", "sec", "finra", "nerc"
        }
        
        signals.is_defense = any(kw in query_lower for kw in defense_keywords)
        signals.is_safety_critical = any(kw in query_lower for kw in safety_keywords)
        signals.is_export_controlled = any(kw in query_lower for kw in export_keywords)
        signals.is_heavily_regulated = any(kw in query_lower for kw in regulated_keywords)
        
        # Check context domain
        domain = context.get("domain", "").lower()
        if domain in ("defense", "military", "aerospace"):
            signals.is_defense = True
        
        # Breadth score - based on activated dimensions
        axis_vector = context.get("axis_vector", {})
        signals.pillars_activated = sum(1 for k, v in axis_vector.items() if k == 1 and v)
        signals.sectors_activated = sum(1 for k, v in axis_vector.items() if k == 2 and v)
        
        # Count active axes
        active_axes = sum(1 for v in axis_vector.values() if v)
        signals.breadth_score = min(100, active_axes * 8)
        
        # Complexity from query structure
        words = query.split()
        if len(words) > 30:
            signals.breadth_score += 10
        if len(words) > 50:
            signals.breadth_score += 10
        
        # Cross-domain indicators
        cross_keywords = ["and", "plus", "with", "including", "combined"]
        cross_count = sum(1 for kw in cross_keywords if kw in query_lower)
        signals.breadth_score += min(20, cross_count * 5)
        signals.breadth_score = min(100, signals.breadth_score)
        
        # Stakes score
        if signals.is_defense:
            signals.stakes_score += 30
        if signals.is_safety_critical:
            signals.stakes_score += 30
        if signals.is_export_controlled:
            signals.stakes_score += 20
        if signals.is_heavily_regulated:
            signals.stakes_score += 20
        signals.stakes_score = min(100, signals.stakes_score)
        
        # Conflict and coverage from quad outputs
        if quad_outputs:
            confidences = []
            gaps = 0
            
            for lane, output in quad_outputs.items():
                if isinstance(output, dict):
                    conf = output.get("confidence", 0.5)
                    confidences.append(conf)
                    if output.get("has_gaps") or output.get("needs_more_info"):
                        gaps += 1
            
            if confidences:
                # Conflict = variance in confidences
                avg_conf = sum(confidences) / len(confidences)
                variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences)
                signals.conflict_score = min(1.0, variance * 10)
                
                # Coverage = average confidence, penalized by gaps
                signals.coverage_score = avg_conf * (1 - gaps * 0.1)
        else:
            signals.coverage_score = 0.5
        
        return signals
    
    def _should_force_high_assurance(self, signals: ScoringSignals) -> bool:
        """Check if high-assurance mode should be forced."""
        return (
            signals.is_defense or
            signals.is_safety_critical or
            signals.is_export_controlled or
            signals.stakes_score >= 60
        )
    
    def _select_mode(
        self,
        signals: ScoringSignals,
        policy_mode: str
    ) -> POVMode:
        """Select POV mode based on signals."""
        complexity = signals.overall_complexity()
        
        # Adjust thresholds for high-assurance
        bypass_t = self.BYPASS_THRESHOLD
        light_t = self.LIGHT_THRESHOLD
        standard_t = self.STANDARD_THRESHOLD
        
        if policy_mode == "high_assurance":
            bypass_t -= self.HIGH_ASSURANCE_THRESHOLD_REDUCTION
            light_t -= self.HIGH_ASSURANCE_THRESHOLD_REDUCTION
            standard_t -= self.HIGH_ASSURANCE_THRESHOLD_REDUCTION
        
        if complexity < bypass_t:
            return POVMode.BYPASS
        elif complexity < light_t:
            return POVMode.LIGHT
        elif complexity < standard_t:
            return POVMode.STANDARD
        else:
            return POVMode.COMMITTEE
    
    def _select_viewpoints(
        self,
        signals: ScoringSignals,
        mode: POVMode,
        context: Dict[str, Any],
        budget: POVBudget
    ) -> tuple:
        """Select viewpoints based on mode and signals."""
        viewpoints = []
        lane_counts = {
            "knowledge": 0,
            "sector": 0,
            "regulatory": 0,
            "compliance": 0,
            "stakeholder": 0
        }
        
        if mode == POVMode.BYPASS:
            return viewpoints, lane_counts
        
        # Always include auditor viewpoint
        viewpoints.append(ViewpointSelection(
            viewpoint_id="auditor",
            name="Audit & Verification",
            lane="compliance",
            priority=1,
            reason="Standard audit perspective"
        ))
        lane_counts["compliance"] += 1
        
        if mode == POVMode.LIGHT:
            # Add 1-2 stakeholder perspectives
            viewpoints.append(ViewpointSelection(
                viewpoint_id="operator",
                name="Operator/End User",
                lane="stakeholder",
                priority=2,
                reason="Operational feasibility check"
            ))
            lane_counts["stakeholder"] += 1
            
        elif mode == POVMode.STANDARD:
            # Base quad enhancement
            viewpoints.append(ViewpointSelection(
                viewpoint_id="operator",
                name="Operator/End User",
                lane="stakeholder",
                priority=2,
                reason="Operational feasibility check"
            ))
            lane_counts["stakeholder"] += 1
            
            if signals.is_defense or signals.is_heavily_regulated:
                viewpoints.append(ViewpointSelection(
                    viewpoint_id="external_validator",
                    name="External Validator",
                    lane="regulatory",
                    priority=2,
                    reason="Regulatory validation"
                ))
                lane_counts["regulatory"] += 1
                
        elif mode == POVMode.COMMITTEE:
            # Full pod expansion - delegate to persona scaling
            # This will be integrated with KA-21
            
            # Knowledge pod
            if signals.subsystems_detected > 0:
                count = min(budget.knowledge_max, signals.subsystems_detected + 2)
            else:
                count = min(budget.knowledge_max, 3)
            lane_counts["knowledge"] = count
            
            # Sector pod
            lane_counts["sector"] = min(budget.sector_max, 2)
            
            # Regulatory pod
            if signals.is_defense or signals.is_export_controlled:
                lane_counts["regulatory"] = min(budget.regulatory_max, 2)
            else:
                lane_counts["regulatory"] = 1
            
            # Compliance pod
            lane_counts["compliance"] = min(budget.compliance_max, 2)
            
            # Stakeholder viewpoints
            stakeholder_roles = ["operator", "decision_maker", "administrator"]
            if signals.is_safety_critical:
                stakeholder_roles.append("safety_advocate")
            
            for role in stakeholder_roles[:budget.stakeholder_max]:
                viewpoints.append(ViewpointSelection(
                    viewpoint_id=role,
                    name=role.replace("_", " ").title(),
                    lane="stakeholder",
                    priority=3,
                    reason=f"Committee stakeholder: {role}"
                ))
                lane_counts["stakeholder"] += 1
        
        return viewpoints, lane_counts
    
    def _generate_decision_reasons(
        self,
        signals: ScoringSignals,
        mode: POVMode
    ) -> List[str]:
        """Generate human-readable decision reasons."""
        reasons = []
        
        if signals.is_defense:
            reasons.append("Defense domain detected - elevated scrutiny")
        if signals.is_safety_critical:
            reasons.append("Safety-critical context - additional validation required")
        if signals.is_export_controlled:
            reasons.append("Export control implications - regulatory review needed")
        if signals.breadth_score > 50:
            reasons.append(f"High complexity (breadth={signals.breadth_score:.0f})")
        if signals.conflict_score > 0.2:
            reasons.append(f"Quad persona conflict detected ({signals.conflict_score:.2f})")
        if signals.coverage_score < 0.8:
            reasons.append(f"Coverage gaps detected ({signals.coverage_score:.2f})")
        
        reasons.append(f"Selected mode: {mode.value}")
        
        return reasons


# =============================================================================
# Factory Function
# =============================================================================

def create_pov_policy_service(config: Dict[str, Any] = None) -> POVPolicyService:
    """Create and configure a POVPolicyService instance."""
    return POVPolicyService(config)
