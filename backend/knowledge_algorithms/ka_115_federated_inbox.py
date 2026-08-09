"""KA-115: bounded federated-inbox admission proposal."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class FederatedInboxClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1, max_length=200)
    source_tenant_ref: str = Field(min_length=1, max_length=200)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_refs: list[str] = Field(min_length=1, max_length=1_000)
    signature_verified: bool
    source_authorized: bool


class KA115Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incoming_claims: list[FederatedInboxClaim] = Field(
        default_factory=list, max_length=1_000
    )


class KA115FederatedInbox(KnowledgeAlgorithm):
    """Admit verified claim references without ingesting content."""

    input_schema = KA115Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-115"

    def _run_logic(self, input_data: KA115Input) -> dict[str, Any]:
        accepted = []
        rejected = []
        for claim in sorted(input_data.incoming_claims, key=lambda row: row.claim_id):
            blockers = []
            if not claim.signature_verified:
                blockers.append("signature_not_verified")
            if not claim.source_authorized:
                blockers.append("source_not_authorized")
            if blockers:
                rejected.append({"claim_id": claim.claim_id, "blockers": blockers})
            else:
                accepted.append(
                    {
                        "claim_id": claim.claim_id,
                        "source_tenant_ref": claim.source_tenant_ref,
                        "content_sha256": claim.content_sha256,
                        "evidence_refs": sorted(set(claim.evidence_refs)),
                    }
                )
        proposal_id = stable_identifier("federated-inbox", accepted)
        return {
            "success": True,
            "status": "inbox_admission_evaluated",
            "proposal_id": proposal_id,
            "accepted_claims": accepted,
            "rejected_claims": rejected,
            "ingested_count": 0,
            "effect_proposal": (
                {
                    "effect_id": proposal_id,
                    "kind": "enqueue_federated_inbox",
                    "status": "proposed",
                    "service": "operations_control_service",
                    "payload": {"claims": accepted},
                }
                if accepted
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "Signature and source flags must come from authoritative services; "
                "the KA stores no claim and does not establish truth."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA115FederatedInbox(context).run(context)
