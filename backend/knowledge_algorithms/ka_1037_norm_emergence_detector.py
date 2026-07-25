"""KA-1037: measured multi-agent convergence and dissent analysis."""

from __future__ import annotations

from itertools import combinations
from statistics import fmean
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import normalized_tokens
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PersonaOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    persona_id: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=50_000)
    position: str | None = Field(default=None, max_length=500)


class DebateTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    persona_id: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=20_000)


class KA1037Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "persona_outputs": [
                        {
                            "persona_id": "knowledge",
                            "content": "Validate the evidence.",
                            "position": "validate",
                        },
                        {
                            "persona_id": "regulatory",
                            "content": "Review the applicable control.",
                            "position": "review",
                        },
                    ]
                }
            ]
        },
    )

    persona_outputs: list[PersonaOutput] = Field(
        min_length=2,
        max_length=100,
    )
    debate_trace: list[DebateTurn] = Field(
        default_factory=list,
        max_length=1_000,
    )
    position_concentration_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1,
    )
    language_similarity_threshold: float = Field(
        default=0.75,
        ge=0,
        le=1,
    )

    @model_validator(mode="after")
    def validate_personas(self) -> KA1037Input:
        persona_ids = [item.persona_id for item in self.persona_outputs]
        if len(persona_ids) != len(set(persona_ids)):
            raise ValueError("persona outputs require unique persona IDs")
        known = set(persona_ids)
        if any(turn.persona_id not in known for turn in self.debate_trace):
            raise ValueError("debate trace references an unknown persona")
        return self


class KA1037NormEmergenceDetector(KnowledgeAlgorithm):
    """Detect measurable convergence without asserting motives or harm."""

    input_schema = KA1037Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1037"

    @staticmethod
    def _similarity(left: set[str], right: set[str]) -> float:
        union = left | right
        return 1.0 if not union else len(left & right) / len(union)

    def _run_logic(self, input_data: KA1037Input) -> dict[str, Any]:
        token_sets = {
            item.persona_id: normalized_tokens(item.content)
            for item in input_data.persona_outputs
        }
        pairwise = [
            self._similarity(
                token_sets[left.persona_id],
                token_sets[right.persona_id],
            )
            for left, right in combinations(input_data.persona_outputs, 2)
        ]
        mean_similarity = round(fmean(pairwise), 8) if pairwise else 0.0

        positions: dict[str, list[str]] = {}
        for item in input_data.persona_outputs:
            normalized = " ".join(sorted(normalized_tokens(item.position)))
            if normalized:
                positions.setdefault(normalized, []).append(item.persona_id)
        dominant_position = None
        dominant_personas: list[str] = []
        if positions:
            dominant_position, dominant_personas = min(
                positions.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )
        concentration = round(
            len(dominant_personas) / len(input_data.persona_outputs),
            8,
        )
        dissenting = sorted(
            item.persona_id
            for item in input_data.persona_outputs
            if item.persona_id not in dominant_personas
        )

        flags: list[dict[str, Any]] = []
        if concentration >= input_data.position_concentration_threshold:
            flags.append(
                {
                    "code": "position_concentration",
                    "measured_value": concentration,
                    "threshold": (input_data.position_concentration_threshold),
                }
            )
        if mean_similarity >= input_data.language_similarity_threshold:
            flags.append(
                {
                    "code": "language_convergence",
                    "measured_value": mean_similarity,
                    "threshold": input_data.language_similarity_threshold,
                }
            )
        unhealthy_suspected = len(flags) == 2 and not dissenting
        return {
            "success": True,
            "status": "convergence_measured",
            "convergence_metrics": {
                "persona_count": len(input_data.persona_outputs),
                "mean_pairwise_token_jaccard": mean_similarity,
                "dominant_position_ratio": concentration,
                "debate_turn_count": len(input_data.debate_trace),
                "dissenting_persona_count": len(dissenting),
            },
            "norm_flags": flags,
            "dominant_position_signature": dominant_position,
            "dissenting_personas": dissenting,
            "unhealthy_convergence_suspected": unhealthy_suspected,
            "measurement_status": "observational",
            "limitations": (
                "Token and position convergence can indicate similarity, not "
                "groupthink, coercion, correctness, or harm. Human review and "
                "task context are required."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1037NormEmergenceDetector(context).run(context)
