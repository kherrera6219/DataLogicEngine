"""
Layer 8: Trust Validation Gateway Schemas

Pydantic schemas for the TrustValidationGateway service providing
structured gate decisions (PASS/WARN/FAIL) and audit artifacts.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, UTC


class GateDecision(str, Enum):
    """Gate decision outcomes from Layer 8."""
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class ContradictionItem(BaseModel):
    """A detected contradiction between two claims."""
    claim_a: str = Field(..., description="First conflicting claim")
    claim_b: str = Field(..., description="Second conflicting claim")
    source_a: str = Field(default="unknown", description="Source of claim A")
    source_b: str = Field(default="unknown", description="Source of claim B")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Contradiction severity")
    resolution_attempted: bool = Field(default=False)
    resolution_status: Optional[str] = None


class FixDirective(BaseModel):
    """Instruction for L9 on what to rerun."""
    target_layer: int = Field(..., ge=1, le=10, description="Layer to rerun")
    reason: str = Field(..., description="Why this layer needs rerun")
    priority: str = Field(default="medium", description="Urgency: low/medium/high/critical")
    suggested_action: Optional[str] = None


class DomainConfidence(BaseModel):
    """Confidence score for a specific domain/axis."""
    domain: str
    axis_id: int = Field(ge=1, le=17)
    confidence: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    passes: bool


class L8Input(BaseModel):
    """Input schema for Layer 8 TrustValidationGateway."""
    simulation_id: str
    query_text: str = Field(default="")
    
    # Artifacts from previous layers
    l5_synthesis: Optional[Dict[str, Any]] = None
    l6_quant_result: Optional[Dict[str, Any]] = None
    l7_agi_plan: Optional[Dict[str, Any]] = None
    
    # Claims and evidence
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Persona outputs
    persona_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Target requirements
    target_confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    risk_domain: str = Field(default="standard", description="standard/healthcare/finance/legal/safety")
    
    # 17-axis governance (optional)
    axis_14_threshold: Optional[float] = None  # Override confidence threshold
    axis_17_requires_human: bool = Field(default=False)


class L8GateResult(BaseModel):
    """Output schema for Layer 8 gate decision."""
    simulation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Gate decision
    status: GateDecision
    
    # Confidence metrics
    overall_confidence: float = Field(ge=0.0, le=1.0)
    target_threshold: float = Field(ge=0.0, le=1.0)
    domain_confidences: List[DomainConfidence] = Field(default_factory=list)
    
    # Quantum Trust Fidelity (legacy compatibility)
    quantum_trust_fidelity: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Consistency report
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    semantic_mismatches: List[str] = Field(default_factory=list)
    orphan_chains: List[str] = Field(default_factory=list)
    
    # Gate artifacts
    warnings: List[str] = Field(default_factory=list)
    fix_directives: List[FixDirective] = Field(default_factory=list)
    escalation_target: Optional[int] = None  # Layer to escalate to
    
    # Audit trail
    axes_evaluated: List[int] = Field(default_factory=list)
    kas_invoked: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(default=0.0)
    
    # Governance hooks (17-axis)
    requires_human_review: bool = Field(default=False)
    disclosure_required: bool = Field(default=False)
    opa_policy: Dict[str, Any] = Field(default_factory=dict)
    model_screening: Dict[str, Any] = Field(default_factory=dict)


class L8AuditArtifact(BaseModel):
    """Audit artifact written by Layer 8 for compliance."""
    simulation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    gate_result: L8GateResult
    
    # Provenance
    evidence_fidelity_ratio: float = Field(ge=0.0, le=1.0)
    compliance_pass_factor: float = Field(ge=0.0, le=1.0)
    cross_domain_checks: List[Dict[str, Any]] = Field(default_factory=list)
    
    # For immutable audit trail
    hash_input: Optional[str] = None
