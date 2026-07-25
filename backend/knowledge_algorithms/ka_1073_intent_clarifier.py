"""KA-1073: bounded intent-candidate matching and clarification planning."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import normalized_tokens
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class IntentCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent_id: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2_000)
    keywords: list[str] = Field(min_length=1, max_length=100)
    required_slots: list[str] = Field(default_factory=list, max_length=50)


class KA1073Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "utterance": "restore the most recent backup",
                    "candidate_intents": [
                        {
                            "intent_id": "restore_backup",
                            "description": "Restore a backup",
                            "keywords": ["restore", "backup"],
                            "required_slots": ["backup_id"],
                        }
                    ],
                    "provided_slots": {"backup_id": "latest"},
                }
            ]
        },
    )

    utterance: str = Field(min_length=1, max_length=20_000)
    candidate_intents: list[IntentCandidate] = Field(
        min_length=1,
        max_length=200,
    )
    provided_slots: dict[str, Any] = Field(default_factory=dict)
    minimum_match: float = Field(default=0.5, ge=0, le=1)
    ambiguity_margin: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_candidates(self) -> KA1073Input:
        ids = [item.intent_id for item in self.candidate_intents]
        if len(ids) != len(set(ids)):
            raise ValueError("intent candidate IDs must be unique")
        return self


class KA1073IntentClarifier(KnowledgeAlgorithm):
    """Resolve only sufficiently distinct declared intent candidates."""

    input_schema = KA1073Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1073"

    def _run_logic(self, input_data: KA1073Input) -> dict[str, Any]:
        utterance_tokens = normalized_tokens(input_data.utterance)
        ranked = []
        for candidate in input_data.candidate_intents:
            candidate_tokens = normalized_tokens(
                " ".join([candidate.description, *candidate.keywords])
            )
            score = (
                len(utterance_tokens & candidate_tokens) / len(candidate_tokens)
                if candidate_tokens
                else 0
            )
            ranked.append(
                {
                    "intent_id": candidate.intent_id,
                    "match_score": round(score, 8),
                    "required_slots": candidate.required_slots,
                }
            )
        ranked.sort(key=lambda item: (-item["match_score"], item["intent_id"]))
        best = ranked[0]
        second_score = ranked[1]["match_score"] if len(ranked) > 1 else 0
        distinct = (
            best["match_score"] >= input_data.minimum_match
            and best["match_score"] - second_score >= input_data.ambiguity_margin
        )
        missing_slots = sorted(
            slot
            for slot in best["required_slots"]
            if slot not in input_data.provided_slots
        )
        resolved = distinct and not missing_slots
        questions = []
        if not distinct:
            questions.append(
                {
                    "code": "intent_ambiguous",
                    "prompt": "Select the intended operation.",
                    "options": [item["intent_id"] for item in ranked[:5]],
                }
            )
        questions.extend(
            {
                "code": "required_slot_missing",
                "slot": slot,
                "prompt": f"Provide {slot}.",
            }
            for slot in missing_slots
        )
        return {
            "success": True,
            "status": ("intent_resolved" if resolved else "clarification_required"),
            "resolved_intent": best["intent_id"] if resolved else None,
            "ranked_candidates": ranked,
            "extracted_slots": {
                key: input_data.provided_slots[key]
                for key in sorted(input_data.provided_slots)
            },
            "clarification_questions": questions,
            "deterministic": True,
            "limitations": (
                "Matching uses declared keywords and provided slots; it does "
                "not infer unstated intent or execute the selected operation."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1073IntentClarifier(context).run(context)
