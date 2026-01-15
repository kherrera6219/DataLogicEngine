from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, conint, confloat


# -----------------------------
# Enums
# -----------------------------
class PersonaType(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    SECTOR = "SECTOR"
    REGULATORY = "REGULATORY"
    COMPLIANCE = "COMPLIANCE"
    VALIDATION = "VALIDATION"
    RISK = "RISK"


class TaskType(str, Enum):
    explain = "explain"
    compare = "compare"
    design = "design"
    evaluate = "evaluate"
    draft = "draft"
    debug = "debug"
    extract = "extract"
    classify = "classify"


class SafetyClass(str, Enum):
    public = "public"
    internal = "internal"
    cui = "cui"
    secret = "secret"


class Severity(str, Enum):
    info = "info"
    warn = "warn"
    block = "block"


class ConstraintType(str, Enum):
    policy = "policy"
    legal = "legal"
    security = "security"
    format = "format"
    scope = "scope"
    evidence = "evidence"


class ClaimType(str, Enum):
    fact = "fact"
    inference = "inference"
    recommendation = "recommendation"
    constraint = "constraint"


class Impact(str, Enum):
    low = "low"
    med = "med"
    high = "high"


class Likelihood(str, Enum):
    low = "low"
    med = "med"
    high = "high"


# -----------------------------
# Core request models
# -----------------------------
class Budget(BaseModel):
    time_ms: conint(gt=0)
    tokens: conint(gt=0)
    max_iterations: conint(ge=1, le=10)


class RiskProfile(BaseModel):
    domain_risk: Literal["low", "med", "high"]
    safety_class: SafetyClass


class ProblemSpec(BaseModel):
    task_type: TaskType
    success_criteria: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    risk_profile: Optional[RiskProfile] = None
    ambiguities: List[str] = Field(default_factory=list)
    clarifying_questions: List[str] = Field(default_factory=list)


class AxisCoord(BaseModel):
    """
    17-axis coordinate mapping.
    Keep flexible: you can store strings, IDs, or composite codes per axis.
    """
    model_config = ConfigDict(extra="allow")

    a1: Optional[str] = None
    a2: Optional[str] = None
    a3: Optional[str] = None
    a4: Optional[str] = None
    a5: Optional[str] = None
    a6: Optional[str] = None
    a7: Optional[str] = None
    a8: Optional[str] = None
    a9: Optional[str] = None
    a10: Optional[str] = None
    a11: Optional[str] = None
    a12: Optional[str] = None
    a13: Optional[str] = None
    a14: Optional[str] = None
    a15: Optional[str] = None
    a16: Optional[str] = None
    a17: Optional[str] = None


class EvidenceItem(BaseModel):
    evidence_id: str
    kind: Literal["doc", "url", "kb_node", "transcript", "dataset", "other"]
    title: Optional[str] = None
    uri: Optional[str] = None
    snippet: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextPack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)
    prior_state: Dict[str, Any] = Field(default_factory=dict)
    policies: Dict[str, Any] = Field(default_factory=dict)
    budgets: Optional[Budget] = None


class Layer5RunRequest(BaseModel):
    run_id: str
    trace_id: str
    problem_spec: ProblemSpec
    coord: AxisCoord
    context_pack: ContextPack
    gatekeeper_config: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------
# Persona output envelope models
# -----------------------------
class Claim(BaseModel):
    claim_id: str
    text: str
    claim_type: ClaimType
    axis_tags: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    confidence: confloat(ge=0.0, le=1.0)


class Constraint(BaseModel):
    constraint_id: str
    text: str
    severity: Severity
    type: ConstraintType
    applies_to: List[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    risk_id: str
    text: str
    impact: Impact
    likelihood: Likelihood
    mitigations: List[str] = Field(default_factory=list)


class SelfCheck(BaseModel):
    contradictions_found: bool
    missing_evidence: List[str] = Field(default_factory=list)
    hallucination_risk: confloat(ge=0.0, le=1.0)


class PersonaScores(BaseModel):
    confidence_overall: confloat(ge=0.0, le=1.0)
    coverage: confloat(ge=0.0, le=1.0)
    evidence_quality: confloat(ge=0.0, le=1.0)
    policy_alignment: confloat(ge=0.0, le=1.0)


class PersonaEnvelope(BaseModel):
    persona_type: PersonaType
    persona_id: str
    version: str = "1.0.0"
    claims: List[Claim] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    self_check: SelfCheck
    scores: PersonaScores
    flags: List[str] = Field(default_factory=list)


class VetoLog(BaseModel):
    vetoed: bool
    reason: str = ""
    by_persona: List[PersonaType] = Field(default_factory=list)
    redactions: List[str] = Field(default_factory=list)


class Consensus(BaseModel):
    status: Literal["FINALIZE", "ESCALATE", "BLOCK", "REDACT", "CLARIFY"]
    confidence_sys: confloat(ge=0.0, le=1.0)
    rationale: List[str] = Field(default_factory=list)
    release_threshold: confloat(ge=0.0, le=1.0) = 0.92
    escalate_threshold: confloat(ge=0.0, le=1.0) = 0.75


class Layer5RunResponse(BaseModel):
    run_id: str
    trace_id: str
    personas_spawned: List[PersonaType]
    persona_outputs: List[PersonaEnvelope]
    veto_log: VetoLog
    conflict_matrix: Dict[str, Any] = Field(default_factory=dict)
    consensus: Consensus
    timings: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------
# Error response
# -----------------------------
class ErrorResponse(BaseModel):
    error: str
    message: str
    trace_id: str
