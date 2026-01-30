"""
Pydantic models for UKG Trace API responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============== Enums ==============

class RunStatus(str, Enum):
    RUNNING = "running"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class StageStatus(str, Enum):
    RUNNING = "running"
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIPPED = "skipped"


class StageType(str, Enum):
    LAYER = "layer"
    STEP = "step"


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    CONTESTED = "contested"


class SourceType(str, Enum):
    DOC = "doc"
    URL = "url"
    DB_RECORD = "dbRecord"
    USER_UPLOAD = "userUpload"


class AuthorityLevel(str, Enum):
    HIGH = "high"
    MED = "med"
    LOW = "low"


class PolicyDecisionType(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REDACT = "redact"
    WARN = "warn"


class MemoryTarget(str, Enum):
    WORKING = "working"
    UKG = "ukg"
    USKD = "uskd"


class MemoryEventType(str, Enum):
    RECALL = "recall"
    WRITEBACK_PROPOSED = "writebackProposed"
    WRITEBACK_COMMITTED = "writebackCommitted"
    SNAPSHOT = "snapshot"


class ChatMode(str, Enum):
    CHAT = "chat"
    EXPLAIN = "explain"
    TRACE = "trace"


# ============== Nested Models ==============

# No changes needed for api_models.py
class ModelInfo(BaseModel):
    name: str
    version: str


class PolicyPackInfo(BaseModel):
    id: Optional[str] = None
    version: Optional[str] = None


class Scores(BaseModel):
    confidence: float = 0.0
    entropy: float = 0.0
    bias_risk: float = Field(0.0, alias="biasRisk")

    class Config:
        populate_by_name = True


class DataSnapshot(BaseModel):
    ukg_snapshot_id: Optional[str] = Field(None, alias="ukgSnapshotId")
    uskd_snapshot_id: Optional[str] = Field(None, alias="uskdSnapshotId")
    index_versions: Optional[dict[str, str]] = Field(None, alias="indexVersions")

    class Config:
        populate_by_name = True


class StageTiming(BaseModel):
    start_time: Optional[datetime] = Field(None, alias="startTime")
    end_time: Optional[datetime] = Field(None, alias="endTime")
    duration_ms: Optional[int] = Field(None, alias="durationMs")

    class Config:
        populate_by_name = True


class AnswerSpan(BaseModel):
    start: Optional[int] = None
    end: Optional[int] = None


class ClaimSupport(BaseModel):
    status: ClaimStatus
    confidence: float = 0.0
    evidence_ids: Optional[list[str]] = Field(None, alias="evidenceIds")
    stage_ids: Optional[list[str]] = Field(None, alias="stageIds")

    class Config:
        populate_by_name = True


class EvidenceSource(BaseModel):
    type: Optional[SourceType] = None
    id: Optional[str] = None
    title: Optional[str] = None
    authority: AuthorityLevel = AuthorityLevel.MED


class RetrievalInfo(BaseModel):
    method: Optional[str] = None
    relevance_score: Optional[float] = Field(None, alias="relevanceScore")
    axis_match: Optional[float] = Field(None, alias="axisMatch")

    class Config:
        populate_by_name = True


class UsedBy(BaseModel):
    claims: Optional[list[str]] = None
    personas: Optional[list[str]] = None
    stages: Optional[list[str]] = None


class PersonaInputs(BaseModel):
    evidence_ids: Optional[list[str]] = Field(None, alias="evidenceIds")
    context_scope: Optional[str] = Field(None, alias="contextScope")

    class Config:
        populate_by_name = True


class PersonaDraft(BaseModel):
    text: Optional[str] = None
    confidence: float = 0.0


class KATiming(BaseModel):
    duration_ms: Optional[int] = Field(None, alias="durationMs")

    class Config:
        populate_by_name = True


class Redaction(BaseModel):
    start: int
    end: int
    reason_code: str = Field(alias="reasonCode")
    policy_rule_id: Optional[str] = Field(None, alias="policyRuleId")

    class Config:
        populate_by_name = True


# ============== Main Models ==============

class Run(BaseModel):
    """A trace run representing a complete chatbot interaction."""
    run_id: str = Field(alias="runId")
    session_id: Optional[str] = Field(None, alias="sessionId")
    tenant_id: Optional[str] = Field(None, alias="tenantId")
    user_id: Optional[int] = Field(None, alias="userId")
    status: RunStatus
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    model: ModelInfo
    policy_pack: Optional[PolicyPackInfo] = Field(None, alias="policyPack")
    data_snapshot: Optional[DataSnapshot] = Field(None, alias="dataSnapshot")
    scores: Optional[Scores] = None
    input_message: Optional[str] = Field(None, alias="inputMessage")
    final_answer: Optional[str] = Field(None, alias="finalAnswer")

    class Config:
        populate_by_name = True


class Stage(BaseModel):
    """A stage in the execution pipeline."""
    stage_id: str = Field(alias="stageId")
    run_id: str = Field(alias="runId")
    name: str
    type: Optional[StageType] = None
    layer_index: Optional[int] = Field(None, alias="layerIndex")
    step_index: Optional[int] = Field(None, alias="stepIndex")
    status: StageStatus
    timing: Optional[StageTiming] = None
    inputs: Optional[list[dict[str, Any]]] = None
    outputs: Optional[list[dict[str, Any]]] = None
    decisions: Optional[list[dict[str, Any]]] = None
    metrics: Optional[dict[str, Any]] = None

    class Config:
        populate_by_name = True


class Artifact(BaseModel):
    """An artifact (input/output blob)."""
    artifact_id: str = Field(alias="artifactId")
    run_id: str = Field(alias="runId")
    stage_id: Optional[str] = Field(None, alias="stageId")
    type: str
    label: Optional[str] = None
    content: Optional[dict[str, Any]] = None
    content_ref: Optional[str] = Field(None, alias="contentRef")
    hash: Optional[str] = None
    redactions: Optional[list[Redaction]] = None

    class Config:
        populate_by_name = True


class Claim(BaseModel):
    """A claim extracted from the final answer."""
    claim_id: str = Field(alias="claimId")
    run_id: str = Field(alias="runId")
    text: str
    answer_span: Optional[AnswerSpan] = Field(None, alias="answerSpan")
    support: Optional[ClaimSupport] = None

    class Config:
        populate_by_name = True


class Evidence(BaseModel):
    """An evidence item used in a run."""
    evidence_id: str = Field(alias="evidenceId")
    run_id: str = Field(alias="runId")
    source: EvidenceSource
    locator: Optional[dict[str, Any]] = None
    snippet: Optional[str] = None
    hash: Optional[str] = None
    retrieval: Optional[RetrievalInfo] = None
    used_by: Optional[UsedBy] = Field(None, alias="usedBy")
    conflicts_with: Optional[list[str]] = Field(None, alias="conflictsWith")

    class Config:
        populate_by_name = True


class AxisValue(BaseModel):
    """A single axis value in the coordinate vector."""
    axis_id: str = Field(alias="axisId")
    name: str
    selected_value: str = Field(alias="selectedValue")
    confidence: float
    candidates: Optional[list[dict[str, Any]]] = None
    trigger_evidence_ids: Optional[list[str]] = Field(None, alias="triggerEvidenceIds")

    class Config:
        populate_by_name = True


class AxisVector(BaseModel):
    """The 17-axis coordinate vector for a run."""
    vector_id: str = Field(alias="vectorId")
    run_id: str = Field(alias="runId")
    coordinate_hash: Optional[str] = Field(None, alias="coordinateHash")
    axes: list[AxisValue]

    class Config:
        populate_by_name = True


class Persona(BaseModel):
    """A persona execution trace."""
    persona_id: str = Field(alias="personaId")
    run_id: str = Field(alias="runId")
    persona_type: str = Field(alias="personaType")
    persona_name: Optional[str] = Field(None, alias="personaName")
    status: str
    inputs: Optional[PersonaInputs] = None
    draft: Optional[PersonaDraft] = None
    objections: Optional[list[dict[str, Any]]] = None
    consensus_impact: Optional[dict[str, Any]] = Field(None, alias="consensusImpact")

    class Config:
        populate_by_name = True


class KAInvocation(BaseModel):
    """A Knowledge Algorithm invocation trace."""
    invocation_id: str = Field(alias="invocationId")
    run_id: str = Field(alias="runId")
    stage_id: Optional[str] = Field(None, alias="stageId")
    ka_id: str = Field(alias="kaId")
    ka_name: str = Field(alias="kaName")
    ka_version: str = Field(alias="kaVersion")
    status: str
    timing: Optional[KATiming] = None
    inputs: Optional[dict[str, Any]] = None
    outputs: Optional[dict[str, Any]] = None
    routing: Optional[dict[str, Any]] = None
    side_effects: Optional[list[dict[str, Any]]] = Field(None, alias="sideEffects")

    class Config:
        populate_by_name = True


class PolicyDecision(BaseModel):
    """A policy/guardrail decision."""
    decision_id: str = Field(alias="decisionId")
    run_id: str = Field(alias="runId")
    stage_id: Optional[str] = Field(None, alias="stageId")
    policy_rule_id: Optional[str] = Field(None, alias="policyRuleId")
    type: PolicyDecisionType
    reason: Optional[str] = None
    affected: Optional[dict[str, Any]] = None
    actor: str = "system"
    timestamp: Optional[datetime] = None

    class Config:
        populate_by_name = True


class MemoryEvent(BaseModel):
    """A memory access/writeback event."""
    event_id: str = Field(alias="eventId")
    run_id: str = Field(alias="runId")
    stage_id: Optional[str] = Field(None, alias="stageId")
    type: MemoryEventType
    target: MemoryTarget
    items: Optional[list[dict[str, Any]]] = None
    gating: Optional[dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    class Config:
        populate_by_name = True


class TraceSpan(BaseModel):
    """An OpenTelemetry-style trace span."""
    span_id: str = Field(alias="spanId")
    run_id: str = Field(alias="runId")
    parent_span_id: Optional[str] = Field(None, alias="parentSpanId")
    name: str
    stage_id: Optional[str] = Field(None, alias="stageId")
    start_at: Optional[datetime] = Field(None, alias="startAt")
    end_at: Optional[datetime] = Field(None, alias="endAt")
    duration_ms: Optional[int] = Field(None, alias="durationMs")
    attributes: Optional[dict[str, Any]] = None
    events: Optional[list[dict[str, Any]]] = None

    class Config:
        populate_by_name = True


class StageLog(BaseModel):
    """A log entry for a stage."""
    log_id: str = Field(alias="logId")
    run_id: str = Field(alias="runId")
    stage_id: Optional[str] = Field(None, alias="stageId")
    level: str
    message: str
    data: Optional[dict[str, Any]] = None
    time: Optional[datetime] = None

    class Config:
        populate_by_name = True


class Export(BaseModel):
    """An export bundle."""
    export_id: str = Field(alias="exportId")
    run_id: str = Field(alias="runId")
    user_id: int = Field(alias="userId")
    status: str
    bundle_ref: Optional[str] = Field(None, alias="bundleRef")
    manifest_hash: Optional[str] = Field(None, alias="manifestHash")
    file_size_bytes: Optional[int] = Field(None, alias="fileSizeBytes")
    format: str = "json"
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")

    class Config:
        populate_by_name = True


class ChatSession(BaseModel):
    """A chat session."""
    session_id: str = Field(alias="sessionId")
    user_id: int = Field(alias="userId")
    title: Optional[str] = None
    mode: ChatMode = ChatMode.CHAT
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    constraints: Optional[dict[str, Any]] = None

    class Config:
        populate_by_name = True


class ComplianceMapping(BaseModel):
    """A compliance framework mapping."""
    mapping_id: str = Field(alias="mappingId")
    run_id: str = Field(alias="runId")
    framework: str
    control_id: str = Field(alias="controlId")
    relevance_reason: Optional[str] = Field(None, alias="relevanceReason")
    evidence_ids: Optional[list[str]] = Field(None, alias="evidenceIds")
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    class Config:
        populate_by_name = True


# ============== Response Models ==============

class PaginatedResponse(BaseModel):
    """Base paginated response."""
    total: int
    page: int
    pages: int


class RunsResponse(PaginatedResponse):
    runs: list[Run]


class SessionsResponse(PaginatedResponse):
    sessions: list[ChatSession]


class StagesResponse(BaseModel):
    stages: list[Stage]


class EvidenceResponse(BaseModel):
    evidence: list[Evidence]


class ClaimsResponse(BaseModel):
    claims: list[Claim]


class PersonasResponse(BaseModel):
    personas: list[Persona]


class KAsResponse(BaseModel):
    kas: list[KAInvocation]


class PolicyResponse(BaseModel):
    policy_decisions: list[PolicyDecision] = Field(alias="policyDecisions")

    class Config:
        populate_by_name = True


class MemoryResponse(BaseModel):
    memory_events: list[MemoryEvent] = Field(alias="memoryEvents")

    class Config:
        populate_by_name = True


class SpansResponse(BaseModel):
    spans: list[TraceSpan]


class LogsResponse(BaseModel):
    logs: list[StageLog]


class ExportsResponse(BaseModel):
    exports: list[Export]


class MetricsResponse(BaseModel):
    metrics: dict[str, Any]


class ComplianceResponse(BaseModel):
    run_id: str = Field(alias="runId")
    compliance_mappings: dict[str, list[ComplianceMapping]] = Field(alias="complianceMappings")
    total: int

    class Config:
        populate_by_name = True
