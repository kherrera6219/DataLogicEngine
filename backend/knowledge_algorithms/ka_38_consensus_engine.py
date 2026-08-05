"""KA-038: deterministic DSQP consensus-readiness assessment."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PersonaClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=20_000)
    persona_type: str = Field(min_length=1, max_length=100)
    support_score: float | None = Field(default=None, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KA038Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claims: list[PersonaClaim] = Field(default_factory=list, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    conflict_threshold: float = Field(default=0.4, ge=0, le=1)


class KA038ConsensusEngine(KnowledgeAlgorithm):
    """Report consensus readiness without inventing confidence or resolving dissent."""

    input_schema = KA038Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-038"

    def _run_logic(self, input_data: KA038Input) -> dict[str, Any]:
        weighting = input_data.dependency_results.get("KA-013", {})
        disposition = input_data.dependency_results.get("KA-030", {})
        sufficiency = weighting.get("sufficiency") or {}
        retained_dissent = disposition.get("resolved_findings") or []

        by_claim: dict[str, list[PersonaClaim]] = {}
        for claim in input_data.claims:
            by_claim.setdefault(claim.claim_id, []).append(claim)
        claim_measurements: list[dict[str, Any]] = []
        claim_conflicts: list[str] = []
        for claim_id, group in sorted(by_claim.items()):
            measured = [
                claim.support_score
                for claim in group
                if claim.support_score is not None
            ]
            delta = max(measured) - min(measured) if len(measured) > 1 else None
            conflict = delta is not None and delta > input_data.conflict_threshold
            if conflict:
                claim_conflicts.append(claim_id)
            claim_measurements.append(
                {
                    "claim_id": claim_id,
                    "persona_count": len({claim.persona_type for claim in group}),
                    "measured_support_count": len(measured),
                    "support_range": (
                        [round(min(measured), 8), round(max(measured), 8)]
                        if measured
                        else None
                    ),
                    "maximum_support_delta": (
                        round(delta, 8) if delta is not None else None
                    ),
                    "conflict_detected": conflict,
                }
            )

        dependencies_complete = set(input_data.dependency_results) == {
            "KA-013",
            "KA-030",
        }
        consensus_ready = bool(
            dependencies_complete
            and sufficiency.get("sufficient") is True
            and weighting.get("silent_dissent_count") == 0
            and disposition.get("silent_dissent_count") == 0
            and not retained_dissent
            and not claim_conflicts
        )
        return {
            "success": True,
            "status": "consensus_ready" if consensus_ready else "consensus_blocked",
            "consensus_ready": consensus_ready,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "persona_sufficient": sufficiency.get("sufficient") is True,
            "retained_dissent_count": len(retained_dissent),
            "claim_measurements": claim_measurements,
            "claim_conflict_ids": claim_conflicts,
            "calibrated_confidence": None,
            "substantive_consensus_claimed": False,
            "context_applied": False,
            "deterministic": True,
            "limitations": (
                "Consensus readiness means required persona coverage and dissent "
                "handling are complete. It is not factual agreement, calibrated "
                "confidence, or authority to suppress an objection."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA038ConsensusEngine(context).run(context)
