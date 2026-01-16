"""
Layer 10: EmergenceDetection & SafetyGate Schemas

Pydantic schemas for the final release authority and containment gate.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, UTC


class L10Decision(str, Enum):
    """Final release decisions from Layer 10."""
    RELEASE = "RELEASE"
    MODIFY = "MODIFY"
    WITHHOLD = "WITHHOLD"
    ESCALATE = "ESCALATE"
    HALT = "HALT"


class EmergenceLevel(str, Enum):
    """Severity of detected emergence."""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class EmergencePattern(BaseModel):
    """Details of a detected emergence pattern."""
    pattern_type: str  # scope_creep, sensitive_insight, novel_approach, self_referential, etc.
    location: str
    description: str
    risk_level: EmergenceLevel
    score: float = Field(ge=0.0, le=1.0)


class EmergenceAssessment(BaseModel):
    """Full report on emergent behaviors."""
    emergence_detected: bool = False
    overall_level: EmergenceLevel = EmergenceLevel.NONE
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    patterns: List[EmergencePattern] = Field(default_factory=list)
    entropy_delta: float = 0.0
    divergence_score: float = 0.0


class SafetyViolation(BaseModel):
    """Single safety policy violation."""
    module: str  # privacy, ethics, legal, etc.
    violation_type: str
    severity: str  # minor, major, critical
    location: Optional[str] = None
    description: str
    recommended_action: str  # redact, modify, withhold


class SafetyCheckResult(BaseModel):
    """Result of comprehensive safety audit."""
    passed: bool = True
    violations: List[SafetyViolation] = Field(default_factory=list)
    compliance_score: float = Field(default=1.0, ge=0.0, le=1.0)
    release_approved: bool = True


class TrustGateResult(BaseModel):
    """Final confidence/trust determination."""
    status: str  # pass, fail, warn
    domain_category: str  # standard, high_risk
    required_threshold: float
    original_confidence: float
    decayed_confidence: float
    gap: float
    action_required: str  # none, refinement, human_review


class ContainmentAction(BaseModel):
    """Specific action taken to contain/modify output."""
    action_type: str  # redaction, qualification, safe_fallback, etc.
    location: Optional[str] = None
    reason: str
    description: str
    replacement_text: Optional[str] = None


class DSQPTraceSeal(BaseModel):
    """Immutable audit seal for the reasoning trace (Axis 15)."""
    trace_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    hash_chain_root: str
    authority: str = "Layer10_Sentinel"
    compliance_status: str = "compliant"


class L10Input(BaseModel):
    """Input for Layer 10 processing."""
    simulation_id: str
    l9_result: Dict[str, Any]  # L9Result as dict
    reasoning_trace: Dict[str, Any] = Field(default_factory=dict)
    problem_spec: Dict[str, Any] = Field(default_factory=dict)
    coordinate_vector: Dict[str, Any] = Field(default_factory=dict)
    risk_domain: str = Field(default="standard")
    emergency_protocols_active: bool = False


class L10Result(BaseModel):
    """Final output from the UKG 10-Layer Stack."""
    simulation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Final Decision
    decision: L10Decision
    final_answer: Optional[str] = None
    
    # Assessments
    emergence_report: EmergenceAssessment = Field(default_factory=EmergenceAssessment)
    safety_report: SafetyCheckResult = Field(default_factory=SafetyCheckResult)
    trust_report: TrustGateResult = Field(default_factory=lambda: TrustGateResult(
        status="pass", domain_category="standard", required_threshold=0.95,
        original_confidence=1.0, decayed_confidence=0.98, gap=0.03, action_required="none"
    ))
    
    # Actions executed
    containment_actions: List[ContainmentAction] = Field(default_factory=list)
    
    # Audit & Traceability
    dsqp_seal: DSQPTraceSeal
    kas_invoked: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(default=0.0)
    
    # Metadata
    version: str = "UKG-3.0.0-rc1"
    requires_human_signoff: bool = False
    escalation_id: Optional[str] = None
