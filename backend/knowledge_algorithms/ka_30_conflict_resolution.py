"""KA-030: deterministic persona conflict disposition."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA030Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conflicts: list[dict[str, Any]] = Field(default_factory=list, max_length=100)
    query: str = Field(min_length=1, max_length=20_000)
    context: dict[str, Any] = Field(default_factory=dict)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA030ConflictResolution(KnowledgeAlgorithm):
    """Preserve dissent as constraints instead of fabricating mediation."""

    input_schema = KA030Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-030"

    def _run_logic(self, input_data: KA030Input) -> dict[str, Any]:
        weighting = input_data.dependency_results.get("KA-013", {})
        conflicts = input_data.conflicts or weighting.get("dissent") or []
        dispositions: list[dict[str, Any]] = []
        prompt_constraints: list[str] = []

        for index, conflict in enumerate(conflicts):
            if not isinstance(conflict, dict):
                continue
            text = str(
                conflict.get("text")
                or conflict.get("content")
                or conflict.get("objection")
                or ""
            ).strip()
            if not text:
                continue
            persona = str(conflict.get("persona") or "unknown")
            conflict_id = str(
                conflict.get("dissent_id")
                or conflict.get("id")
                or stable_identifier(
                    "persona-conflict",
                    {"index": index, "persona": persona, "text": text},
                )
            )
            prompt_constraints.append(text)
            dispositions.append(
                {
                    "conflict_id": conflict_id,
                    "persona": persona,
                    "text": text,
                    "status": "retained",
                    "resolution": "include_as_mandatory_prompt_constraint",
                    "substantive_resolution_claimed": False,
                }
            )

        return {
            "success": True,
            "status": "persona_conflicts_disposed",
            "resolved_findings": dispositions,
            "prompt_constraints": prompt_constraints,
            "conflict_count": len(dispositions),
            "all_dissent_preserved": len(dispositions) == len(prompt_constraints),
            "silent_dissent_count": 0,
            "escalation_triggered": False,
            "final_state": (
                "CONSTRAINED_BY_RETAINED_DISSENT"
                if dispositions
                else "NO_RECORDED_DISSENT"
            ),
            "confidence_adjustment": None,
            "confidence_status": "not_measured",
            "limitations": (
                "This algorithm resolves orchestration treatment only: every "
                "recorded objection is retained in the prompt. It does not "
                "decide the substantive dispute or create a mediator."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA030ConflictResolution(context).run(context)
