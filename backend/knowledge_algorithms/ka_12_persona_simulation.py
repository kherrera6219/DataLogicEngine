"""KA-012: bounded deterministic multi-persona analysis planning."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.knowledge_algorithms.production_utils import (
    load_config,
    normalized_tokens,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

DEFAULT_PERSONAS = ["knowledge", "sector", "regulatory", "compliance"]


class KA012Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=20_000)
    active_personas: list[str] = Field(
        default_factory=lambda: list(DEFAULT_PERSONAS),
        min_length=1,
        max_length=8,
    )
    context: dict[str, Any] = Field(default_factory=dict)
    dsqp_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @field_validator("active_personas")
    @classmethod
    def normalize_personas(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower() for item in value if item.strip()]
        if len(normalized) != len(set(normalized)):
            raise ValueError("active_personas must be unique")
        unsupported = sorted(set(normalized) - set(DEFAULT_PERSONAS))
        if unsupported:
            raise ValueError("unsupported persona types: " + ", ".join(unsupported))
        return normalized


class KA012PersonaSimulation(KnowledgeAlgorithm):
    """Produce traceable perspective findings without fabricated confidence."""

    input_schema = KA012Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-012"
        self.config = load_config(__file__, "ka_12_config.json")

    def _run_logic(self, input_data: KA012Input) -> dict[str, Any]:
        persona_configs = self.config.get("personas", {})
        query_terms = sorted(normalized_tokens(input_data.query))
        results: list[dict[str, Any]] = []
        constraints: list[dict[str, str]] = []
        objections: list[dict[str, str]] = []
        for persona in input_data.active_personas:
            configured = persona_configs.get(persona, {})
            profile = input_data.dsqp_profiles.get(persona, {})
            validation = (
                profile.get("validation")
                if isinstance(profile.get("validation"), dict)
                else {}
            )
            focus = (
                profile.get("components", {}).get("job_role", {}).get("focus_area")
                or configured.get("focus")
                or "general evidence and operational impact"
            )
            name = profile.get("name") or configured.get("name") or persona.title()
            finding = self._finding(persona, str(name), str(focus), query_terms)
            results.append(
                {
                    **finding,
                    "persona_type": persona,
                    "name": name,
                    "axis_number": profile.get("axis_number"),
                    "dsqp_profile_id": (
                        profile.get("persona_id") or profile.get("profile_id")
                    ),
                    "profile_coverage": (
                        validation.get("coverage_score")
                        if validation.get("coverage_score") is not None
                        else profile.get("coverage_score")
                    ),
                    "profile_validation_status": (
                        "validated"
                        if validation.get("valid") is True
                        else "not_supplied"
                        if not profile
                        else "invalid"
                    ),
                    "confidence": None,
                    "measurement_status": "not_measured",
                    "success": True,
                }
            )
            constraints.extend(finding["constraints"])
            objections.extend(finding["objections"])
        return {
            "success": True,
            "persona_results": results,
            "persona_findings": results,
            "constraints": constraints,
            "objections": objections,
            "dsqp_profiles": input_data.dsqp_profiles,
            "claims": [],
            "provider_subcalls_used": 0,
            "provider_subcall_budget": 0,
            "deterministic": True,
            "summary": f"Prepared {len(results)} bounded perspective findings.",
            "limitations": (
                "Findings are deterministic review prompts, not factual claims "
                "or measured persona confidence."
            ),
        }

    @staticmethod
    def _finding(
        persona: str,
        name: str,
        focus: str,
        query_terms: list[str],
    ) -> dict[str, Any]:
        focus_terms = sorted(normalized_tokens(focus))
        topic_terms = query_terms[:12]
        constraint = {
            "id": stable_identifier(
                "constraint",
                {"persona": persona, "focus": focus, "terms": topic_terms},
            ),
            "persona": persona,
            "text": f"Evaluate {', '.join(topic_terms) or 'the request'} for {focus}.",
        }
        objection = {
            "id": stable_identifier(
                "objection",
                {"persona": persona, "focus": focus},
            ),
            "persona": persona,
            "text": (
                f"What evidence would satisfy the {name} perspective for "
                f"{', '.join(focus_terms[:8]) or 'the stated focus'}?"
            ),
        }
        return {
            "focus": focus,
            "topic_terms": topic_terms,
            "constraints": [constraint],
            "objections": [objection],
            "response": constraint["text"],
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA012PersonaSimulation(context).run(context)
