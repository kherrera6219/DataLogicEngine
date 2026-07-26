"""KA-013: deterministic persona weighting, dissent, and sufficiency."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

DEFAULT_PERSONAS = ["knowledge", "sector", "regulatory", "compliance"]


class KA013Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    persona_results: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=8,
    )
    domain: str = Field(default="GENERAL", min_length=1, max_length=100)
    required_personas: list[str] = Field(
        default_factory=lambda: list(DEFAULT_PERSONAS),
        min_length=1,
        max_length=8,
    )
    minimum_profile_coverage: float = Field(default=0.70, ge=0, le=1)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("required_personas")
    @classmethod
    def normalize_required_personas(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower() for item in value if item.strip()]
        if len(normalized) != len(set(normalized)):
            raise ValueError("required_personas must be unique")
        unsupported = sorted(set(normalized) - set(DEFAULT_PERSONAS))
        if unsupported:
            raise ValueError("unsupported persona types: " + ", ".join(unsupported))
        return normalized


class KA013PersonaWeighting(KnowledgeAlgorithm):
    """Weight measured profile coverage without inventing confidence."""

    input_schema = KA013Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-013"
        self.config = load_config(__file__, "ka_13_config.json")

    def _run_logic(self, input_data: KA013Input) -> dict[str, Any]:
        dependency = input_data.dependency_results.get("KA-012", {})
        persona_results = (
            input_data.persona_results
            or dependency.get("persona_results")
            or dependency.get("persona_findings")
            or []
        )
        domain = input_data.domain.strip().upper()
        configured = self.config.get("domain_weights", {})
        raw_weights = configured.get(domain) or configured.get("GENERAL") or {}

        by_persona: dict[str, dict[str, Any]] = {}
        for result in persona_results:
            if not isinstance(result, dict):
                continue
            persona = str(result.get("persona_type") or "").strip().lower()
            if persona in input_data.required_personas and persona not in by_persona:
                by_persona[persona] = result

        active_weight_total = sum(
            max(0.0, float(raw_weights.get(persona, 0.0))) for persona in by_persona
        )
        if by_persona and active_weight_total <= 0:
            active_weight_total = float(len(by_persona))
            raw_weights = {persona: 1.0 for persona in by_persona}

        weighted_results: list[dict[str, Any]] = []
        dissent: list[dict[str, Any]] = []
        coverage_contribution = 0.0
        for persona in input_data.required_personas:
            result = by_persona.get(persona)
            if result is None:
                continue
            authority_weight = (
                float(raw_weights.get(persona, 0.0)) / active_weight_total
            )
            coverage = result.get("profile_coverage")
            measured_coverage = float(coverage) if coverage is not None else None
            if measured_coverage is not None:
                coverage_contribution += authority_weight * measured_coverage
            weighted_results.append(
                {
                    **result,
                    "authority_weight": round(authority_weight, 8),
                    "weighted_profile_coverage": (
                        round(authority_weight * measured_coverage, 8)
                        if measured_coverage is not None
                        else None
                    ),
                    "confidence": None,
                    "confidence_status": "not_measured",
                }
            )
            for objection in result.get("objections") or []:
                if not isinstance(objection, dict):
                    continue
                dissent.append(
                    {
                        "dissent_id": objection.get("id")
                        or stable_identifier(
                            "dissent",
                            {
                                "persona": persona,
                                "text": objection.get("text"),
                            },
                        ),
                        "persona": persona,
                        "text": str(objection.get("text") or ""),
                        "status": "retained",
                        "resolution": "mandatory_prompt_constraint",
                    }
                )

        missing_personas = sorted(set(input_data.required_personas) - set(by_persona))
        insufficient_coverage = sorted(
            item["persona_type"]
            for item in weighted_results
            if item.get("profile_validation_status") != "validated"
            or (
                item.get("profile_coverage") is not None
                and float(item["profile_coverage"])
                < input_data.minimum_profile_coverage
            )
        )
        unmeasured_coverage = sorted(
            item["persona_type"]
            for item in weighted_results
            if item.get("profile_coverage") is None
        )
        missing_objections = sorted(
            item["persona_type"]
            for item in weighted_results
            if not item.get("objections")
        )
        sufficient = not (
            missing_personas or insufficient_coverage or missing_objections
        )
        priority_map = [
            {
                "persona": item["persona_type"],
                "authority_weight": item["authority_weight"],
            }
            for item in sorted(
                weighted_results,
                key=lambda row: (
                    -float(row["authority_weight"]),
                    str(row["persona_type"]),
                ),
            )
        ]
        return {
            "success": True,
            "domain": domain,
            "weighted_results": weighted_results,
            "priority_map": priority_map,
            "dissent": dissent,
            "dissent_count": len(dissent),
            "silent_dissent_count": 0,
            "dissent_resolution": "retained_as_mandatory_prompt_constraints",
            "sufficiency": {
                "sufficient": sufficient,
                "required_personas": list(input_data.required_personas),
                "observed_personas": sorted(by_persona),
                "missing_personas": missing_personas,
                "insufficient_coverage": insufficient_coverage,
                "unmeasured_coverage": unmeasured_coverage,
                "missing_objections": missing_objections,
                "minimum_profile_coverage": input_data.minimum_profile_coverage,
                "weighted_profile_coverage": (
                    round(coverage_contribution, 8)
                    if weighted_results and not unmeasured_coverage
                    else None
                ),
                "measurement_status": (
                    "profile_validation_and_coverage"
                    if not unmeasured_coverage
                    else "profile_validation_threshold_only"
                ),
            },
            "final_consensus_confidence": None,
            "confidence_status": "not_measured",
            "limitations": (
                "Authority weights prioritize review lenses. Profile coverage "
                "measures DSQP completeness, not factual correctness, persona "
                "confidence, or consensus."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA013PersonaWeighting(context).run(context)
