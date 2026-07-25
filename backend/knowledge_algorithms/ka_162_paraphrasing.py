"""KA-162: evidence-constrained paraphrase selection."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ParaphraseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=100_000)
    evidence_ref: str = Field(min_length=1, max_length=2_000)


class KA162Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "source_text": "The service must retain audit logs.",
                    "required_terms": ["service", "audit logs"],
                    "candidates": [
                        {
                            "candidate_id": "p1",
                            "text": "Audit logs must be retained by the service.",
                            "evidence_ref": "provider-output-1",
                        }
                    ],
                }
            ]
        },
    )

    source_text: str = Field(min_length=1, max_length=100_000)
    required_terms: list[str] = Field(default_factory=list, max_length=1_000)
    forbidden_terms: list[str] = Field(default_factory=list, max_length=1_000)
    candidates: list[ParaphraseCandidate] = Field(min_length=1, max_length=1_000)


class KA162Paraphrasing(KnowledgeAlgorithm):
    """Select a changed candidate that preserves required lexical anchors."""

    input_schema = KA162Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-162"

    def _run_logic(self, input_data: KA162Input) -> dict[str, Any]:
        source_normalized = re.sub(r"\s+", " ", input_data.source_text).strip().casefold()
        assessments = []
        for item in sorted(input_data.candidates, key=lambda row: row.candidate_id):
            normalized = re.sub(r"\s+", " ", item.text).strip().casefold()
            missing = sorted(
                term
                for term in input_data.required_terms
                if term.casefold() not in normalized
            )
            forbidden = sorted(
                term
                for term in input_data.forbidden_terms
                if term.casefold() in normalized
            )
            accepted = normalized != source_normalized and not missing and not forbidden
            assessments.append(
                {
                    "candidate_id": item.candidate_id,
                    "accepted": accepted,
                    "missing_required_terms": missing,
                    "present_forbidden_terms": forbidden,
                    "evidence_ref": item.evidence_ref,
                }
            )
        accepted_ids = [
            row["candidate_id"] for row in assessments if row["accepted"]
        ]
        selected = next(
            (
                item
                for item in sorted(
                    input_data.candidates,
                    key=lambda row: (len(row.text), row.candidate_id),
                )
                if item.candidate_id in accepted_ids
            ),
            None,
        )
        return {
            "success": True,
            "status": "paraphrase_candidates_evaluated",
            "selected_candidate_id": selected.candidate_id if selected else None,
            "paraphrased_text": selected.text if selected else None,
            "assessments": assessments,
            "provider_called": False,
            "deterministic": True,
            "limitations": (
                "Lexical constraints do not prove semantic equivalence; supplied "
                "candidates require governed generation and domain review."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA162Paraphrasing(context).run(context)
