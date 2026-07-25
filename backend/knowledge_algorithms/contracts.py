"""Typed, versioned execution contracts for the canonical KA controller."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class KAExecutionMode(StrEnum):
    PRODUCTION = "production"
    EVALUATION = "evaluation"
    DRY_RUN = "dry_run"


class KAExecutionState(StrEnum):
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class KAOutcomeType(StrEnum):
    VALUE = "value"
    VALIDATION_DECISION = "validation_decision"
    RECOMMENDATION = "recommendation"
    ARTIFACT = "artifact"
    EFFECT_PROPOSAL = "effect_proposal"
    APPLIED_EFFECT = "applied_effect"
    UNAVAILABLE_PREREQUISITE = "unavailable_prerequisite"
    BLOCKED_POLICY = "blocked_policy"
    INVALID_INPUT = "invalid_input"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    INTERNAL_FAILURE = "internal_failure"


class KAFailureCode(StrEnum):
    NOT_FOUND = "KA_NOT_FOUND"
    NOT_PRODUCTION_QUALIFIED = "KA_NOT_PRODUCTION_QUALIFIED"
    IMPLEMENTATION_UNAVAILABLE = "KA_IMPLEMENTATION_UNAVAILABLE"
    INVALID_INPUT = "KA_INVALID_INPUT"
    CANCELLED = "KA_CANCELLED"
    DEADLINE_EXCEEDED = "KA_DEADLINE_EXCEEDED"
    EXECUTION_FAILED = "KA_EXECUTION_FAILED"
    INVALID_IMPLEMENTATION_RESULT = "KA_INVALID_IMPLEMENTATION_RESULT"


class KABudget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deadline_ms: int = Field(default=1000, ge=1, le=3_600_000)
    max_dependency_executions: int = Field(default=32, ge=0, le=512)
    max_recursion_depth: int = Field(default=4, ge=0, le=32)
    max_input_bytes: int = Field(default=1_000_000, ge=1, le=100_000_000)
    max_output_bytes: int = Field(default=5_000_000, ge=1, le=100_000_000)
    max_provider_calls: int = Field(default=0, ge=0, le=1_000)
    max_effects: int = Field(default=0, ge=0, le=1_000)


class KAExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str | None = None
    principal_id: str | None = None
    scopes: set[str] = Field(default_factory=set)
    workflow: str = "direct"
    tier: str | None = None
    layer: str | None = None
    persona: str | None = None
    policy_decisions: dict[str, Any] = Field(default_factory=dict)
    capability_state: dict[str, Any] = Field(default_factory=dict)
    configuration_revision: str | None = None
    random_seed: int | None = None
    deadline_at: datetime | None = None
    cancellation_requested: bool = False
    budget: KABudget = Field(default_factory=KABudget)


class KAExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ka_id: str
    input: dict[str, Any] = Field(default_factory=dict)
    context: KAExecutionContext = Field(default_factory=KAExecutionContext)
    mode: KAExecutionMode = KAExecutionMode.PRODUCTION
    idempotency_key: str | None = Field(default=None, max_length=200)
    confirmation_token: str | None = Field(default=None, max_length=500)


class KAArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    kind: str
    media_type: str | None = None
    sha256: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    storage_receipt: dict[str, Any] | None = None


class KAEffectReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effect_id: str
    kind: str
    status: Literal["proposed", "applied", "failed", "rolled_back"]
    service: str
    idempotency_key: str | None = None
    authoritative_receipt: dict[str, Any] = Field(default_factory=dict)


class KAExecutionError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: KAFailureCode
    message: str
    retryable: bool = False
    internal_details: dict[str, Any] = Field(default_factory=dict, exclude=True)


class KAExecutionContractError(RuntimeError):
    """Raised when an internal caller requires output from a failed KA result."""

    def __init__(self, result: KAExecutionResult):
        code = result.error.code.value if result.error else "KA_RESULT_UNAVAILABLE"
        message = (
            result.error.message
            if result.error
            else "Knowledge Algorithm did not return a successful result."
        )
        super().__init__(f"{result.canonical_id} [{code}]: {message}")
        self.result = result


class KAExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "dle.ka-execution-result.v1"
    canonical_id: str
    ka_version: str
    manifest_version: str
    state: KAExecutionState
    outcome_type: KAOutcomeType
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[KAArtifact] = Field(default_factory=list)
    effects: list[KAEffectReceipt] = Field(default_factory=list)
    error: KAExecutionError | None = None
    request_id: str
    run_id: str
    trace_id: str
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime = Field(default_factory=utc_now)
    duration_ms: float = Field(default=0.0, ge=0.0)
    implementation_adapter: str | None = None

    def require_output(self) -> dict[str, Any]:
        """Return typed output or raise instead of allowing an optimistic default."""
        if not self.success:
            raise KAExecutionContractError(self)
        return self.output
