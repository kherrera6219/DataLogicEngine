"""
Layer 9: MetaReasoningController Schemas

Pydantic schemas for the MetaReasoningController service providing
FINALIZE/REFINE gate decisions and structured handoffs to L8 or L10.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, UTC


class L9Decision(str, Enum):
    """Gate decision outcomes from Layer 9."""
    FINALIZE = "FINALIZE"
    REFINE = "REFINE"


class RefinementSeverity(str, Enum):
    """Severity of refinement needed."""
    MINOR = "minor"
    MAJOR = "major"


class BeliefDriftReport(BaseModel):
    """Report on belief drift between query and solution."""
    drift_detected: bool = False
    drift_score: float = Field(default=0.0, ge=0.0, le=1.0, description="0=aligned, 1=drifted")
    drift_type: Optional[str] = None  # "semantic", "numerical", "scope"
    original_intent: Optional[str] = None
    current_output: Optional[str] = None
    details: Optional[str] = None


class PersonaAgreementItem(BaseModel):
    """Single cell in persona agreement matrix."""
    persona: str
    component: str
    score: float = Field(ge=0.0, le=1.0)
    concern: Optional[str] = None


class PersonaAgreementMatrix(BaseModel):
    """Persona agreement audit result."""
    matrix: List[PersonaAgreementItem] = Field(default_factory=list)
    min_score: float = Field(default=1.0)
    threshold_required: float = Field(default=0.95)
    threshold_met: bool = True
    flagged_combinations: List[PersonaAgreementItem] = Field(default_factory=list)


class TraceIntegrityReport(BaseModel):
    """Report on reasoning trace integrity."""
    integrity_score: float = Field(default=1.0, ge=0.0, le=1.0)
    layers_reviewed: List[int] = Field(default_factory=list)
    issues_found: List[Dict[str, Any]] = Field(default_factory=list)
    orphan_claims: int = 0
    unresolved_branches: int = 0


class MetaEvaluationReport(BaseModel):
    """Result of meta-cognitive self-evaluation."""
    evaluation_score: float = Field(default=0.9, ge=0.0, le=1.0)
    weakness_hotspots: List[Dict[str, Any]] = Field(default_factory=list)
    failure_modes: List[Dict[str, Any]] = Field(default_factory=list)
    alternative_approaches: List[str] = Field(default_factory=list)


class RefinementDirective(BaseModel):
    """Instruction for refinement loop."""
    focus: str
    required_changes: List[str] = Field(default_factory=list)
    success_criteria: str = ""
    additional_context: Optional[str] = None


class RefinementPlan(BaseModel):
    """Plan for recursive refinement."""
    target_layer: int = Field(ge=2, le=8, description="Layer to recurse to")
    preserve_layers: List[int] = Field(default_factory=list)
    rerun_layers: List[int] = Field(default_factory=list)
    directives: RefinementDirective
    iteration_count: int = Field(default=1)
    max_iterations: int = Field(default=5)
    expected_improvement: float = Field(default=0.0)


class EpistemicReport(BaseModel):
    """Epistemic review report for audit trail (Axis 15)."""
    review_conducted: str = "full_meta_analysis"
    issues_found: int = 0
    approval_authority: str = "Layer9_MetaReasoning"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_integrity: float = Field(default=1.0)
    belief_alignment: str = "strong"
    persona_consensus: str = "unanimous"
    robustness: str = "high"


class L9Input(BaseModel):
    """Input schema for Layer 9 MetaReasoningController."""
    simulation_id: str
    
    # From Layer 8
    l8_gate_result: Dict[str, Any]  # L8GateResult as dict
    
    # Complete reasoning trace L1-L8
    reasoning_trace: Dict[str, Any] = Field(default_factory=dict)
    
    # Original problem specification
    problem_spec: Dict[str, Any] = Field(default_factory=dict)
    
    # Iteration state
    iteration_state: Dict[str, Any] = Field(default_factory=lambda: {
        "current_iteration": 1,
        "max_iterations": 5,
        "prior_fixes_attempted": [],
        "previous_readiness_scores": []
    })
    
    # Risk classification
    risk_domain: str = Field(default="standard")


class L9Result(BaseModel):
    """Output schema for Layer 9 gate decision."""
    simulation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Gate decision
    decision: L9Decision
    severity: Optional[RefinementSeverity] = None
    
    # Readiness metrics
    readiness_score: float = Field(ge=0.0, le=1.0)
    readiness_components: Dict[str, float] = Field(default_factory=dict)
    
    # Analysis reports
    trace_report: TraceIntegrityReport = Field(default_factory=TraceIntegrityReport)
    drift_report: BeliefDriftReport = Field(default_factory=BeliefDriftReport)
    persona_report: PersonaAgreementMatrix = Field(default_factory=PersonaAgreementMatrix)
    meta_report: MetaEvaluationReport = Field(default_factory=MetaEvaluationReport)
    
    # For REFINE path
    refinement_plan: Optional[RefinementPlan] = None
    
    # For FINALIZE path
    epistemic_report: Optional[EpistemicReport] = None
    
    # Governance
    requires_human_review: bool = False
    disclosure_flags: List[str] = Field(default_factory=list)
    
    # Audit
    kas_invoked: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(default=0.0)
