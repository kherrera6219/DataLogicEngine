"""KA-057: deterministic persona and emotional-context style planning."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA057Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_object: dict[str, Any] = Field(default_factory=dict)
    persona: Literal[
        "general",
        "technical_expert",
        "business_leader",
        "end_user",
        "skeptic",
    ] = "general"
    emotional_context: Literal[
        "neutral",
        "uncertain",
        "distressed",
        "positive",
    ] = "neutral"


class KA057PersonaEmotionAdaptation(KnowledgeAlgorithm):
    """Return bounded style constraints without rewriting response content."""

    input_schema = KA057Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-057"

    def _run_logic(self, input_data: KA057Input) -> dict[str, Any]:
        persona_settings = {
            "general": ("medium", "balanced", "plain_language"),
            "technical_expert": ("high", "concise", "technical_detail"),
            "business_leader": ("medium", "concise", "decision_summary"),
            "end_user": ("low", "supportive", "step_by_step"),
            "skeptic": ("high", "neutral", "evidence_first"),
        }
        emotional_settings = {
            "neutral": ("standard", False),
            "uncertain": ("clarifying", True),
            "distressed": ("calm", True),
            "positive": ("warm", False),
        }
        complexity, tone, structure = persona_settings[input_data.persona]
        emotional_tone, acknowledge_uncertainty = emotional_settings[
            input_data.emotional_context
        ]
        source_id = input_data.output_object.get("id")
        return {
            "success": True,
            "status": "persona_style_proposed",
            "adapted_style_plan": {
                "persona_applied": input_data.persona,
                "persona": input_data.persona,
                "emotional_context": input_data.emotional_context,
                "complexity": complexity,
                "tone": tone,
                "emotional_tone": emotional_tone,
                "structure": structure,
                "acknowledge_uncertainty": acknowledge_uncertainty,
                "source_object_id": str(source_id) if source_id is not None else None,
            },
            "content_inspected": False,
            "content_rewritten": False,
            "profile_updated": False,
            "context_applied": False,
            "deterministic": True,
            "limitations": (
                "The result is a style proposal from explicit persona and emotional "
                "context. It does not infer emotion, rewrite content, or update a profile."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA057PersonaEmotionAdaptation(context).run(context)
