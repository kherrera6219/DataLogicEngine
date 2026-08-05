"""KA-1084: measured agreement across identified UKG instance answers."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

WHITESPACE_RE = re.compile(r"\s+")


class InstanceAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instance_id: str = Field(min_length=1, max_length=200)
    answer: str = Field(min_length=1, max_length=100_000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_hashes: list[str] = Field(default_factory=list, max_length=1_000)


class KA1084Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "instance_answers": [
                        {"instance_id": "a", "answer": "approved"},
                        {"instance_id": "b", "answer": "Approved"},
                        {"instance_id": "c", "answer": "rejected"},
                    ],
                    "consensus_threshold": 0.66,
                }
            ]
        },
    )

    instance_answers: list[InstanceAnswer] = Field(
        min_length=2,
        max_length=1_000,
    )
    consensus_threshold: float = Field(default=0.67, gt=0.5, le=1)

    @model_validator(mode="after")
    def validate_instances(self) -> KA1084Input:
        ids = [item.instance_id for item in self.instance_answers]
        if len(ids) != len(set(ids)):
            raise ValueError("instance IDs must be unique")
        return self


class KA1084CrossInstanceConsensusEngine(KnowledgeAlgorithm):
    """Measure normalized answer agreement without treating it as truth."""

    input_schema = KA1084Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1084"

    @staticmethod
    def _signature(value: str) -> str:
        return WHITESPACE_RE.sub(" ", value.strip().casefold())

    def _run_logic(self, input_data: KA1084Input) -> dict[str, Any]:
        groups: dict[str, list[InstanceAnswer]] = defaultdict(list)
        for answer in input_data.instance_answers:
            groups[self._signature(answer.answer)].append(answer)
        ranked = sorted(
            groups.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )
        signature, supporters = ranked[0]
        ratio = len(supporters) / len(input_data.instance_answers)
        consensus = ratio >= input_data.consensus_threshold
        evidence_sets = [
            set(item.evidence_hashes) for item in supporters if item.evidence_hashes
        ]
        shared_evidence = (
            sorted(set.intersection(*evidence_sets)) if evidence_sets else []
        )
        return {
            "success": True,
            "status": "consensus_measured",
            "consensus_reached": consensus,
            "consensus_answer": supporters[0].answer if consensus else None,
            "consensus_signature": signature if consensus else None,
            "agreement_ratio": round(ratio, 8),
            "supporting_instance_ids": sorted(item.instance_id for item in supporters),
            "disagreement_instance_ids": sorted(
                item.instance_id
                for item in input_data.instance_answers
                if item not in supporters
            ),
            "shared_evidence_hashes": shared_evidence,
            "measurement_status": "agreement_only",
            "truth_established": False,
            "consensus_applied": False,
            "profile_updated": False,
            "external_requests": 0,
            "limitations": (
                "Agreement across instances does not establish factual truth, "
                "independence, evidence quality, or absence of shared bias."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1084CrossInstanceConsensusEngine(context).run(context)
