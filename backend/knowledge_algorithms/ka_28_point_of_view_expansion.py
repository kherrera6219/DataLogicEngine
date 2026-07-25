"""KA-028: deterministic stakeholder point-of-view expansion."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    normalized_tokens,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA028Input(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)
    context: dict[str, Any] = Field(default_factory=dict)
    existing_personas: list[str] = Field(default_factory=list, max_length=100)
    limit: int | None = Field(default=None, ge=1, le=20)


class KA028POVExpansion(KnowledgeAlgorithm):
    """Rank configured perspectives by relevance and emit review objections."""

    input_schema = KA028Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-028"
        self.config = load_config(__file__, "ka_28_config.json")

    def _run_logic(self, input_data: KA028Input) -> dict[str, Any]:
        personas = self.config.get("extra_personas", {})
        existing = {
            value.strip().lower()
            for value in input_data.existing_personas
            if value.strip()
        }
        query_tokens = normalized_tokens(
            f"{input_data.query} {input_data.context}"
        )
        ranked: list[tuple[int, str, dict[str, Any]]] = []
        for key, info in personas.items():
            if key.lower() in existing or not isinstance(info, dict):
                continue
            persona_tokens = normalized_tokens(
                f"{key} {info.get('focus', '')} {info.get('tone', '')}"
            )
            ranked.append((len(query_tokens & persona_tokens), key, info))
        ranked.sort(key=lambda row: (-row[0], row[1]))
        limit = input_data.limit or int(self.config.get("expansion_limit", 2))
        selected = ranked[: max(0, min(limit, len(ranked)))]
        findings = [
            self._finding(key, info, relevance)
            for relevance, key, info in selected
        ]
        return {
            "success": True,
            "additional_perspectives": findings,
            "objections": [item["objection"] for item in findings],
            "selection_order": [item["persona"] for item in findings],
            "count": len(findings),
            "deterministic": True,
        }

    @staticmethod
    def _finding(
        key: str,
        info: dict[str, Any],
        relevance: int,
    ) -> dict[str, Any]:
        focus = str(info.get("focus") or "stakeholder impact")
        tone = str(info.get("tone") or "critical")
        objection = (
            f"What evidence shows the proposal addresses {focus} "
            f"from a {tone} {key.replace('_', ' ')} perspective?"
        )
        return {
            "finding_id": stable_identifier(
                "pov",
                {"persona": key, "focus": focus, "tone": tone},
            ),
            "persona": key,
            "focus": focus,
            "tone": tone,
            "relevance_terms_matched": relevance,
            "content": objection,
            "objection": objection,
            "confidence": None,
            "measurement_status": "not_measured",
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA028POVExpansion(context).run(context)
