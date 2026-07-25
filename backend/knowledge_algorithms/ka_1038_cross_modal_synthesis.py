"""KA-1038: deterministic synthesis of already-extracted modal evidence."""

from __future__ import annotations

from collections import Counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import (
    normalized_tokens,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ModalEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1, max_length=200)
    modality: Literal["text", "table", "image", "audio", "video", "code"]
    extracted_content: str = Field(min_length=1, max_length=50_000)
    claims: list[str] = Field(default_factory=list, max_length=100)
    source_ref: str | None = Field(default=None, max_length=2_000)
    confidence: float | None = Field(default=None, ge=0, le=1)


class KA1038Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "evidence": [
                        {
                            "evidence_id": "text-1",
                            "modality": "text",
                            "extracted_content": "Validated evidence.",
                            "claims": ["Evidence was validated"],
                        }
                    ]
                }
            ]
        },
    )

    evidence: list[ModalEvidence] = Field(min_length=1, max_length=200)
    synthesis_purpose: str = Field(
        default="general evidence synthesis",
        min_length=1,
        max_length=1_000,
    )

    @model_validator(mode="after")
    def validate_ids(self) -> KA1038Input:
        ids = [item.evidence_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence IDs must be unique")
        if sum(len(item.extracted_content) for item in self.evidence) > 2_000_000:
            raise ValueError(
                "extracted evidence exceeds the 2,000,000 character budget"
            )
        return self


class KA1038CrossModalSynthesis(KnowledgeAlgorithm):
    """Fuse normalized evidence while retaining source and modality identity."""

    input_schema = KA1038Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1038"

    def _run_logic(self, input_data: KA1038Input) -> dict[str, Any]:
        modality_counts = Counter(item.modality for item in input_data.evidence)
        claim_support: dict[str, dict[str, Any]] = {}
        sources: list[dict[str, Any]] = []
        for item in sorted(
            input_data.evidence,
            key=lambda evidence: evidence.evidence_id,
        ):
            content_hash = stable_identifier(
                "evidence",
                {
                    "modality": item.modality,
                    "content": item.extracted_content,
                    "source_ref": item.source_ref,
                },
                length=32,
            )
            sources.append(
                {
                    "evidence_id": item.evidence_id,
                    "modality": item.modality,
                    "content_sha256_id": content_hash,
                    "source_ref": item.source_ref,
                    "confidence": item.confidence,
                }
            )
            for claim in item.claims:
                signature = " ".join(sorted(normalized_tokens(claim)))
                if not signature:
                    continue
                row = claim_support.setdefault(
                    signature,
                    {
                        "representations": set(),
                        "evidence_ids": set(),
                        "modalities": set(),
                    },
                )
                row["representations"].add(claim.strip())
                row["evidence_ids"].add(item.evidence_id)
                row["modalities"].add(item.modality)

        claims = [
            {
                "claim_signature": signature,
                "representative_claim": min(
                    row["representations"],
                    key=lambda value: (value.casefold(), value),
                ),
                "evidence_ids": sorted(row["evidence_ids"]),
                "modalities": sorted(row["modalities"]),
                "cross_modal": len(row["modalities"]) > 1,
            }
            for signature, row in sorted(claim_support.items())
        ]
        unified = {
            "synthesis_id": stable_identifier(
                "synthesis",
                {
                    "purpose": input_data.synthesis_purpose,
                    "sources": sources,
                    "claims": claims,
                },
            ),
            "purpose": input_data.synthesis_purpose,
            "sources": sources,
            "modality_coverage": dict(sorted(modality_counts.items())),
            "claims": claims,
        }
        return {
            "success": True,
            "status": "evidence_synthesized",
            "unified_evidence": unified,
            "cross_modal_claim_count": sum(
                1 for claim in claims if claim["cross_modal"]
            ),
            "extraction_performed": False,
            "deterministic": True,
            "limitations": (
                "This KA fuses caller-supplied extracted content and claims. It "
                "does not run OCR, speech recognition, image interpretation, "
                "code execution, or independent factual verification."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1038CrossModalSynthesis(context).run(context)
