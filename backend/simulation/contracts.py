"""Versioned contracts for the authoritative Phase 10 simulation path."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


SIMULATION_CONTRACT_VERSION = "dle-simulation.v1"
SIMULATION_ENGINE_ID = "multi-agent-debate"
SIMULATION_ENGINE_VERSION = "3.0.0"


class SimulationDepth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class SimulationParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(..., min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    role: str = Field(..., min_length=1, max_length=64)
    perspective: str | None = Field(default=None, max_length=500)


class SimulationExpectedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    required: bool = True
    schema_version: str = Field(default="simulation-artifact.v1", max_length=64)


class SimulationScenario(BaseModel):
    """Versioned, bounded scenario accepted by the selected engine."""

    model_config = ConfigDict(extra="forbid")

    contract_version: str = Field(default=SIMULATION_CONTRACT_VERSION, frozen=True)
    query: str = Field(..., min_length=1, max_length=5_000)
    context: dict[str, Any] = Field(default_factory=dict)
    execution_mode: Literal["live", "fixed_seed_local"] = "live"
    provider: str | None = Field(default=None, max_length=32)
    model: str | None = Field(default=None, max_length=128)
    depth: SimulationDepth = SimulationDepth.STANDARD
    seed: int = Field(default=0, ge=0, le=2_147_483_647)
    participants: list[SimulationParticipant] = Field(default_factory=list, max_length=12)
    input_corpus: list[str] = Field(default_factory=list, max_length=100)
    max_total_tokens: int = Field(default=10_000, ge=1_000, le=100_000)
    max_tool_calls: int = Field(default=0, ge=0, le=100)
    max_cost_usd: float | None = Field(default=None, ge=0.0, le=10_000.0)
    timeout_seconds: int = Field(default=300, ge=30, le=1_800)
    expected_artifacts: list[SimulationExpectedArtifact] = Field(
        default_factory=lambda: [
            SimulationExpectedArtifact(type="transcript"),
            SimulationExpectedArtifact(type="result"),
        ],
        min_length=1,
        max_length=20,
    )

    @model_validator(mode="after")
    def _validate_stable_ids(self) -> "SimulationScenario":
        encoded_context = json.dumps(
            self.context,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        if len(encoded_context.encode("utf-8")) > 10_000:
            raise ValueError("simulation_context_exceeds_10000_bytes")
        participant_ids = [participant.id for participant in self.participants]
        if len(participant_ids) != len(set(participant_ids)):
            raise ValueError("participant_ids_must_be_unique")
        corpus_ids = [str(value).strip() for value in self.input_corpus]
        if any(not value for value in corpus_ids) or len(corpus_ids) != len(set(corpus_ids)):
            raise ValueError("input_corpus_ids_must_be_nonempty_and_unique")
        artifact_types = [artifact.type for artifact in self.expected_artifacts]
        if len(artifact_types) != len(set(artifact_types)):
            raise ValueError("expected_artifact_types_must_be_unique")
        if set(artifact_types) != {"transcript", "result"}:
            raise ValueError("expected_artifacts_must_be_transcript_and_result")
        return self

    @property
    def plan(self) -> "SimulationPlan":
        default_plan = SimulationPlan.for_depth(self.depth)
        if not self.participants:
            return default_plan
        return SimulationPlan(
            depth=default_plan.depth,
            debate_turns=default_plan.debate_turns,
            participants=tuple(participant.id for participant in self.participants),
            max_provider_calls=default_plan.max_provider_calls,
            max_tokens_per_call=default_plan.max_tokens_per_call,
        )


@dataclass(frozen=True, slots=True)
class SimulationPlan:
    """Immutable preflight plan and hard provider ceiling for one run."""

    depth: SimulationDepth
    debate_turns: int
    participants: tuple[str, ...]
    max_provider_calls: int
    max_tokens_per_call: int = 500

    @classmethod
    def for_depth(cls, depth: SimulationDepth | str) -> "SimulationPlan":
        try:
            normalized = depth if isinstance(depth, SimulationDepth) else SimulationDepth(depth)
        except ValueError as exc:
            raise ValueError(
                f"Invalid depth '{depth}'. Must be 'quick', 'standard', or 'deep'."
            ) from exc

        debate_turns = {
            SimulationDepth.QUICK: 2,
            SimulationDepth.STANDARD: 3,
            SimulationDepth.DEEP: 5,
        }[normalized]
        all_participants = (
            "Knowledge_Expert",
            "Regulatory_Advisor",
            "Sector_Specialist",
        )
        participants = (
            all_participants[:2]
            if normalized is SimulationDepth.QUICK
            else all_participants
        )
        # One contextualization call, one call per debate turn, one synthesis.
        max_provider_calls = debate_turns + 2
        return cls(
            depth=normalized,
            debate_turns=debate_turns,
            participants=participants,
            max_provider_calls=max_provider_calls,
        )

    @property
    def max_output_tokens(self) -> int:
        return self.max_provider_calls * self.max_tokens_per_call

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": SIMULATION_CONTRACT_VERSION,
            "engine": SIMULATION_ENGINE_ID,
            "engine_version": SIMULATION_ENGINE_VERSION,
            "depth": self.depth.value,
            "debate_turns": self.debate_turns,
            "participants": list(self.participants),
            "max_provider_calls": self.max_provider_calls,
            "max_tokens_per_call": self.max_tokens_per_call,
            "max_output_tokens": self.max_output_tokens,
        }
