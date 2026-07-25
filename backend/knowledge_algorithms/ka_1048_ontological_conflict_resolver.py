"""KA-1048: deterministic ontological conflict resolution proposals."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

WHITESPACE_RE = re.compile(r"\s+")


class OntologyAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assertion_id: str = Field(min_length=1, max_length=200)
    concept_id: str = Field(min_length=1, max_length=200)
    definition: str = Field(min_length=1, max_length=20_000)
    source_ontology: str = Field(min_length=1, max_length=500)
    authority_priority: int = Field(ge=0, le=1_000)
    confidence: float = Field(ge=0, le=1)
    evidence_refs: list[str] = Field(default_factory=list, max_length=500)


class KA1048Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "assertions": [
                        {
                            "assertion_id": "a",
                            "concept_id": "control",
                            "definition": "A verified risk-reduction measure.",
                            "source_ontology": "approved",
                            "authority_priority": 10,
                            "confidence": 0.9,
                            "evidence_refs": ["policy-1"],
                        },
                        {
                            "assertion_id": "b",
                            "concept_id": "control",
                            "definition": "Any documented process.",
                            "source_ontology": "legacy",
                            "authority_priority": 5,
                            "confidence": 0.8,
                        },
                    ]
                }
            ]
        },
    )

    assertions: list[OntologyAssertion] = Field(min_length=2, max_length=5_000)

    @model_validator(mode="after")
    def validate_identity(self) -> KA1048Input:
        assertion_ids = [item.assertion_id for item in self.assertions]
        if len(assertion_ids) != len(set(assertion_ids)):
            raise ValueError("ontology assertion IDs must be unique")
        return self


class KA1048OntologicalConflictResolver(KnowledgeAlgorithm):
    """Rank conflicting definitions while retaining ties for human review."""

    input_schema = KA1048Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1048"

    @staticmethod
    def _normalized_definition(value: str) -> str:
        return WHITESPACE_RE.sub(" ", value.casefold().strip())

    @staticmethod
    def _rank(item: OntologyAssertion) -> tuple[int, float, int]:
        return (
            item.authority_priority,
            item.confidence,
            len(set(item.evidence_refs)),
        )

    def _run_logic(self, input_data: KA1048Input) -> dict[str, Any]:
        by_concept: dict[str, list[OntologyAssertion]] = defaultdict(list)
        for assertion in input_data.assertions:
            by_concept[assertion.concept_id].append(assertion)

        proposals: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        consistent: list[str] = []
        for concept_id in sorted(by_concept):
            assertions = by_concept[concept_id]
            definitions = {
                self._normalized_definition(item.definition) for item in assertions
            }
            if len(definitions) <= 1:
                consistent.append(concept_id)
                continue
            ranked = sorted(
                assertions,
                key=lambda item: (
                    -item.authority_priority,
                    -item.confidence,
                    -len(set(item.evidence_refs)),
                    item.assertion_id,
                ),
            )
            top_rank = self._rank(ranked[0])
            tied = [item for item in ranked if self._rank(item) == top_rank]
            tied_definitions = {
                self._normalized_definition(item.definition) for item in tied
            }
            if len(tied_definitions) > 1:
                unresolved.append(
                    {
                        "concept_id": concept_id,
                        "reason": "equal_authority_confidence_and_evidence",
                        "assertion_ids": sorted(item.assertion_id for item in tied),
                    }
                )
                continue
            winner = ranked[0]
            proposals.append(
                {
                    "concept_id": concept_id,
                    "preferred_assertion_id": winner.assertion_id,
                    "preferred_definition": winner.definition,
                    "preferred_source_ontology": winner.source_ontology,
                    "superseded_assertion_ids": sorted(
                        item.assertion_id
                        for item in assertions
                        if item.assertion_id != winner.assertion_id
                    ),
                    "resolution_basis": [
                        "authority_priority",
                        "confidence",
                        "evidence_count",
                    ],
                    "requires_owner_approval": True,
                }
            )

        return {
            "success": True,
            "status": "ontological_conflicts_evaluated",
            "resolution_proposals": proposals,
            "unresolved_conflicts": unresolved,
            "consistent_concept_ids": consistent,
            "conflict_count": len(proposals) + len(unresolved),
            "mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Ranking resolves declared authority, confidence, and evidence "
                "precedence only. It does not establish truth or mutate either "
                "ontology."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1048OntologicalConflictResolver(context).run(context)
