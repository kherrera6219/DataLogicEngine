"""Canonical governed execution contracts.

These contracts are intentionally transport-neutral. Flask routes, desktop chat,
replay, compatible facades, simulations, and SDK clients all adapt to this
versioned shape instead of owning an execution pipeline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Any
import uuid


GOVERNED_CONTRACT_VERSION = "governed.v1"


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class GovernedMode(StrEnum):
    """Supported product execution modes."""

    STANDARD = "standard"
    ENHANCED = "enhanced"
    LOCAL_REVIEW = "local_review"
    SIMULATION = "simulation"

    @classmethod
    def normalize(cls, value: Any) -> "GovernedMode":
        normalized = str(value or "standard").strip().lower()
        compatibility = {
            "chat": cls.STANDARD,
            "trace": cls.STANDARD,
            "explain": cls.STANDARD,
            "quad": cls.ENHANCED,
        }
        if normalized in compatibility:
            return compatibility[normalized]
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported governed execution mode: {normalized}") from exc


class GovernedFailureKind(StrEnum):
    POLICY_BLOCK = "policy_block"
    VALIDATION_FAILURE = "validation_failure"
    PROVIDER_FAILURE = "provider_failure"
    CANCELLED = "cancelled"
    INTERNAL_FAILURE = "internal_failure"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"


class GovernedStageStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass(slots=True)
class GovernedRequest:
    """One admitted request, independent of Flask or SDK transport details."""

    messages: list[dict[str, Any]]
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    contract_version: str = GOVERNED_CONTRACT_VERSION
    mode: GovernedMode = GovernedMode.STANDARD
    source: str = "unknown"
    principal_kind: str = "desktop"
    principal_id: str | None = None
    user_id: int | None = None
    session_id: str | None = None
    api_key_id: str | None = None
    provider: str | None = None
    model: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    temperature: float = 0.7
    max_tokens: int = 1024
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        if self.contract_version != GOVERNED_CONTRACT_VERSION:
            raise ValueError(f"Unsupported governed contract version: {self.contract_version}")
        self.mode = GovernedMode.normalize(self.mode)
        if not isinstance(self.messages, list) or not self.messages:
            raise ValueError("GovernedRequest.messages must contain at least one message")
        if not any(
            isinstance(message, dict) and message.get("role") == "user"
            for message in self.messages
        ):
            raise ValueError("GovernedRequest requires a user message")
        if not isinstance(self.constraints, dict):
            raise ValueError("GovernedRequest.constraints must be an object")
        if not isinstance(self.metadata, dict):
            raise ValueError("GovernedRequest.metadata must be an object")
        self.max_tokens = max(1, min(int(self.max_tokens or 1024), 64_000))
        self.temperature = max(0.0, min(float(self.temperature), 2.0))
        self.source = str(self.source or "unknown")
        self.principal_kind = str(self.principal_kind or "unknown")

    @classmethod
    def from_gateway(cls, request: Any) -> "GovernedRequest":
        """Adapt the pre-v1 gateway request without allowing a bypass."""

        metadata = dict(getattr(request, "meta", None) or {})
        if getattr(request, "run_ukg_pipeline", True) is False:
            metadata.setdefault("compatibility_warnings", []).append(
                "run_ukg_pipeline=false is deprecated and does not bypass governance"
            )
        source = str(metadata.get("source") or "gateway_compatibility")
        principal_kind = str(
            metadata.get("principal_kind")
            or ("external_client" if getattr(request, "api_key_id", None) else "desktop")
        )
        principal_id = metadata.get("principal_id")
        if principal_id is None:
            principal_id = getattr(request, "api_key_id", None) or getattr(request, "user_id", None)
        return cls(
            messages=list(getattr(request, "messages", None) or []),
            mode=GovernedMode.normalize(getattr(request, "mode", None)),
            source=source,
            principal_kind=principal_kind,
            principal_id=str(principal_id) if principal_id is not None else None,
            user_id=getattr(request, "user_id", None),
            session_id=getattr(request, "session_id", None),
            api_key_id=getattr(request, "api_key_id", None),
            provider=getattr(request, "provider", None),
            model=getattr(request, "model", None),
            constraints=dict(getattr(request, "constraints", None) or {}),
            metadata=metadata,
            temperature=getattr(request, "temperature", 0.7),
            max_tokens=getattr(request, "max_tokens", None) or 1024,
        )

    def query_text(self) -> str:
        for message in reversed(self.messages):
            if not isinstance(message, dict) or message.get("role") != "user":
                continue
            content = message.get("content", "")
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                parts = [
                    str(part.get("text") or "").strip()
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                ]
                return " ".join(part for part in parts if part).strip()
        return ""

    @property
    def meta(self) -> dict[str, Any]:
        """Compatibility alias used by the existing policy engine."""

        return self.metadata

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        payload["created_at"] = _iso(self.created_at)
        return payload


@dataclass(slots=True)
class SourceRecord:
    """Stable source identity and provenance independent of retrieval rank."""

    source_id: str
    source_type: str
    origin: str | None = None
    title: str | None = None
    author_publisher: str | None = None
    captured_at: str | None = None
    effective_at: str | None = None
    permissions: dict[str, Any] = field(default_factory=dict)
    transformation_chain: list[dict[str, Any]] = field(default_factory=list)
    embedding_revision: str | None = None
    content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceRecord:
    source_id: str
    citation_label: str
    text: str
    source_type: str = "vector"
    title: str | None = None
    score: float | None = None
    content_hash: str | None = None
    locator: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence_id: str | None = None
    source: SourceRecord | None = None
    retrieved_at: str = field(default_factory=lambda: _now().isoformat())
    quality_score: float | None = None
    freshness_score: float | None = None
    provenance_completeness: float | None = None

    def __post_init__(self) -> None:
        self.source_id = str(self.source_id)
        self.citation_label = str(self.citation_label)
        self.text = str(self.text)
        if self.content_hash is None:
            self.content_hash = sha256(self.text.encode("utf-8")).hexdigest()
        if self.source is None:
            self.source = SourceRecord(
                source_id=self.source_id,
                source_type=self.source_type,
                title=self.title,
                content_hash=self.content_hash,
            )
        else:
            self.source.source_id = self.source_id
            self.source.source_type = self.source.source_type or self.source_type
            self.source.content_hash = self.source.content_hash or self.content_hash
            self.source_type = self.source.source_type
            self.title = self.title or self.source.title

    def bind_to_trace(self, trace_id: str) -> str:
        """Assign the stable per-run evidence ID used by claim/citation rows."""

        if self.evidence_id is None:
            self.evidence_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"datalogicengine:{trace_id}:evidence:{self.source_id}:{self.content_hash}",
                )
            )
        return self.evidence_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "citation_label": self.citation_label,
            "text": self.text,
            "source_type": self.source_type,
            "title": self.title,
            "score": self.score,
            "content_hash": self.content_hash,
            "locator": dict(self.locator),
            "metadata": dict(self.metadata),
            "source": self.source.to_dict() if self.source else None,
            "retrieved_at": self.retrieved_at,
            "quality_score": self.quality_score,
            "freshness_score": self.freshness_score,
            "provenance_completeness": self.provenance_completeness,
        }


@dataclass(slots=True)
class EvidenceLinkRecord:
    evidence_id: str
    source_id: str
    relationship: str
    rationale: str
    validator_id: str
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CitationRecord:
    citation_id: str
    label: str
    evidence_id: str
    source_id: str
    claim_id: str | None = None
    answer_span_start: int | None = None
    answer_span_end: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ClaimRecord:
    claim_id: str
    text: str
    evidence_ids: list[str] = field(default_factory=list)
    status: str = "insufficient"
    confidence: float | None = None
    answer_span_start: int | None = None
    answer_span_end: int | None = None
    claim_type: str = "factual"
    evidence_links: list[EvidenceLinkRecord] = field(default_factory=list)
    citation_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "evidence_ids": list(self.evidence_ids),
            "status": self.status,
            "confidence": self.confidence,
            "answer_span_start": self.answer_span_start,
            "answer_span_end": self.answer_span_end,
            "claim_type": self.claim_type,
            "evidence_links": [link.to_dict() for link in self.evidence_links],
            "citation_ids": list(self.citation_ids),
        }


@dataclass(slots=True)
class ValidatorRecord:
    validator_id: str
    validator_type: str
    version: str
    status: str
    claim_id: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    missing_inputs: list[str] = field(default_factory=list)
    duration_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConfidenceMeasurement:
    formula_version: str
    value: float | None
    status: str
    components: dict[str, float | None] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)
    missing_components: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConvergenceDecision:
    action: str
    reason: str
    iteration: int
    max_iterations: int
    terminal: bool
    unsupported_claim_ids: list[str] = field(default_factory=list)
    contradicted_claim_ids: list[str] = field(default_factory=list)
    failed_validator_ids: list[str] = field(default_factory=list)
    decision_version: str = "dle-convergence.v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GovernedStage:
    name: str
    stage_type: str
    status: GovernedStageStatus = GovernedStageStatus.RUNNING
    stage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=_now)
    completed_at: datetime | None = None
    duration_ms: int | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None

    def finish(
        self,
        status: GovernedStageStatus,
        *,
        outputs: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        self.status = status
        self.completed_at = _now()
        self.duration_ms = max(
            0,
            int((self.completed_at - self.started_at).total_seconds() * 1000),
        )
        if outputs is not None:
            self.outputs = outputs
        if metrics is not None:
            self.metrics = metrics
        self.error_code = error_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_name": self.name,
            "ka_id": self.outputs.get("ka_id") or self.name,
            "stage_type": self.stage_type,
            "status": self.status.value,
            "start_time": _iso(self.started_at),
            "end_time": _iso(self.completed_at),
            "duration_ms": self.duration_ms,
            "input": self.inputs,
            "output": self.outputs,
            "metrics": self.metrics,
            "error_code": self.error_code,
        }


@dataclass(slots=True)
class GovernedFailure:
    kind: GovernedFailureKind
    code: str
    message: str
    stage: str
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        return payload


@dataclass(slots=True)
class GovernedContext:
    request: GovernedRequest
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    stages: list[GovernedStage] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    claims: list[ClaimRecord] = field(default_factory=list)
    citations: list[CitationRecord] = field(default_factory=list)
    validators: list[ValidatorRecord] = field(default_factory=list)
    confidence_measurement: ConfidenceMeasurement | None = None
    convergence_decisions: list[ConvergenceDecision] = field(default_factory=list)
    refinement_cycles: int = 0
    policy_decisions: list[dict[str, Any]] = field(default_factory=list)
    routing: dict[str, Any] = field(default_factory=dict)
    dsqp: dict[str, Any] = field(default_factory=dict)
    truthcore: dict[str, Any] = field(default_factory=dict)
    provider_messages: list[dict[str, Any]] = field(default_factory=list)
    provider_call_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def add_stage(self, name: str, stage_type: str, inputs: dict[str, Any] | None = None) -> GovernedStage:
        stage = GovernedStage(name=name, stage_type=stage_type, inputs=inputs or {})
        self.stages.append(stage)
        return stage


@dataclass(slots=True)
class GovernedResult:
    trace_id: str
    ok: bool
    status: str
    mode: GovernedMode
    answer: str = ""
    contract_version: str = GOVERNED_CONTRACT_VERSION
    provider_used: str | None = None
    model_used: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    coordinate: dict[str, Any] | None = None
    tier: str | None = None
    stages: list[GovernedStage] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    claims: list[ClaimRecord] = field(default_factory=list)
    citations: list[CitationRecord] = field(default_factory=list)
    validators: list[ValidatorRecord] = field(default_factory=list)
    confidence_measurement: ConfidenceMeasurement | None = None
    convergence: ConvergenceDecision | None = None
    warnings: list[str] = field(default_factory=list)
    failure: GovernedFailure | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "trace_id": self.trace_id,
            "ok": self.ok,
            "status": self.status,
            "mode": self.mode.value,
            "answer": self.answer,
            "provider_used": self.provider_used,
            "model_used": self.model_used,
            "usage": self.usage,
            "confidence": self.confidence,
            "coordinate": self.coordinate,
            "tier": self.tier,
            "trace": [stage.to_dict() for stage in self.stages],
            "evidence": [item.to_dict() for item in self.evidence],
            "claims": [claim.to_dict() for claim in self.claims],
            "citations": [citation.to_dict() for citation in self.citations],
            "validators": [validator.to_dict() for validator in self.validators],
            "confidence_measurement": self.confidence_measurement.to_dict()
            if self.confidence_measurement
            else None,
            "convergence": self.convergence.to_dict() if self.convergence else None,
            "warnings": list(self.warnings),
            "failure": self.failure.to_dict() if self.failure else None,
            "metadata": dict(self.metadata),
        }
