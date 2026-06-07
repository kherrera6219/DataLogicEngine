"""
backend/dmrf/models.py — DMRF control-plane data models.

Defines result and routing models for the Dynamic Multi-Route Framework (DMRF)
pipeline: route decisions, scoring, and dispatch results.

DISTINCT FROM core/persona/quad/models.py, which defines quad persona data
models (personas, confidence vectors, pod scaling) for axes 8-11. The two share
no classes; the filename overlap is coincidental.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
import uuid


TIER_ORDER = {
    "trivial": 1,
    "moderate": 2,
    "high_stakes": 3,
    "extreme": 4,
    "autonomous": 5,
}


@dataclass
class AxisVector:
    """Serializable 17-axis routing vector."""

    axes: dict[str, Any]
    confidence: float = 0.0
    active_axes: list[int] = field(default_factory=list)
    frost_layer_depth: int = 4
    truth_engine_mode: str = "standard"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TierClassification:
    """DMRF five-tier classification result."""

    tier: str
    confidence: float
    rationale: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    capped_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DMRFStep:
    """One DMRF step telemetry record."""

    name: str
    status: str = "ok"
    outputs: dict[str, Any] = field(default_factory=dict)
    snapshot_id: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None

    def complete(self) -> None:
        self.completed_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DMRFResult:
    """Top-level DMRF process result."""

    query: str
    run_id: str = field(default_factory=lambda: f"dmrf_{uuid.uuid4().hex[:16]}")
    ok: bool = True
    tier: str = "moderate"
    axis_vector: AxisVector | None = None
    steps: list[DMRFStep] = field(default_factory=list)
    dsqp_chain: dict[str, Any] = field(default_factory=dict)
    gate_result: dict[str, Any] = field(default_factory=dict)
    convergence: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_step(self, step: DMRFStep) -> None:
        self.steps.append(step)

    def export_bundle(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ok": self.ok,
            "tier": self.tier,
            "query_digest": uuid.uuid5(uuid.NAMESPACE_URL, self.query).hex[:16],
            "axis_vector": self.axis_vector.to_dict() if self.axis_vector else {},
            "steps": [step.to_dict() for step in self.steps],
            "dsqp_chain": self.dsqp_chain,
            "gate_result": self.gate_result,
            "convergence": self.convergence,
            "warnings": self.warnings,
            "created_at": self.created_at,
        }

