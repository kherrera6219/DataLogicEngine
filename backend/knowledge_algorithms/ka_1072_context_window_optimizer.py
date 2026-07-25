"""KA-1072: deterministic context selection under a declared token budget."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ContextElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element_id: str = Field(min_length=1, max_length=200)
    token_count: int = Field(ge=1, le=200_000)
    relevance: float = Field(ge=0, le=1)
    priority: float = Field(default=1, ge=0, le=10)
    required: bool = False
    content_ref: str | None = Field(default=None, max_length=2_000)


class KA1072Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "context_elements": [
                        {
                            "element_id": "policy",
                            "token_count": 200,
                            "relevance": 1,
                            "required": True,
                        },
                        {
                            "element_id": "history",
                            "token_count": 500,
                            "relevance": 0.7,
                        },
                    ],
                    "token_budget": 600,
                }
            ]
        },
    )

    context_elements: list[ContextElement] = Field(
        min_length=1,
        max_length=2_000,
    )
    token_budget: int = Field(ge=1, le=2_000_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1072Input:
        ids = [item.element_id for item in self.context_elements]
        if len(ids) != len(set(ids)):
            raise ValueError("context element IDs must be unique")
        return self


class KA1072ContextWindowOptimizer(KnowledgeAlgorithm):
    """Select required then highest utility-density context elements."""

    input_schema = KA1072Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1072"

    def _run_logic(self, input_data: KA1072Input) -> dict[str, Any]:
        required = sorted(
            (item for item in input_data.context_elements if item.required),
            key=lambda item: item.element_id,
        )
        required_tokens = sum(item.token_count for item in required)
        if required_tokens > input_data.token_budget:
            return {
                "success": False,
                "status": "required_context_exceeds_budget",
                "required_tokens": required_tokens,
                "token_budget": input_data.token_budget,
                "required_element_ids": [item.element_id for item in required],
            }
        optional = sorted(
            (item for item in input_data.context_elements if not item.required),
            key=lambda item: (
                -((item.relevance * item.priority) / item.token_count),
                -item.relevance,
                item.token_count,
                item.element_id,
            ),
        )
        selected = list(required)
        remaining = input_data.token_budget - required_tokens
        excluded: list[dict[str, Any]] = []
        for item in optional:
            if item.token_count <= remaining:
                selected.append(item)
                remaining -= item.token_count
            else:
                excluded.append(
                    {
                        "element_id": item.element_id,
                        "reason": "token_budget",
                    }
                )
        selected_ids = {item.element_id for item in selected}
        ordered = [
            item.element_id
            for item in input_data.context_elements
            if item.element_id in selected_ids
        ]
        return {
            "success": True,
            "status": "context_selected",
            "selected_element_ids": ordered,
            "selected_token_count": (input_data.token_budget - remaining),
            "remaining_tokens": remaining,
            "excluded": excluded,
            "selection_method": "required_then_utility_density",
            "deterministic": True,
            "limitations": (
                "Utility density is a bounded deterministic heuristic, not a "
                "proof of globally optimal semantic context."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1072ContextWindowOptimizer(context).run(context)
