"""KA-114: validated federated-outbox proposal."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class FederatedOutboxClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1, max_length=200)
    source_tenant_ref: str = Field(min_length=1, max_length=200)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_refs: list[str] = Field(min_length=1, max_length=1_000)
    release_approved: bool
    recipient_refs: list[str] = Field(min_length=1, max_length=1_000)


class KA114Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claims: list[FederatedOutboxClaim] = Field(default_factory=list, max_length=1_000)


class KA114FederatedOutbox(KnowledgeAlgorithm):
    """Package explicitly released claim references without broadcasting."""

    input_schema = KA114Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-114"

    def _run_logic(self, input_data: KA114Input) -> dict[str, Any]:
        accepted = [claim for claim in input_data.claims if claim.release_approved]
        rejected_ids = sorted(
            claim.claim_id for claim in input_data.claims if not claim.release_approved
        )
        packets = [
            {
                "claim_id": claim.claim_id,
                "source_tenant_ref": claim.source_tenant_ref,
                "content_sha256": claim.content_sha256,
                "evidence_refs": sorted(set(claim.evidence_refs)),
                "recipient_refs": sorted(set(claim.recipient_refs)),
            }
            for claim in sorted(accepted, key=lambda row: row.claim_id)
        ]
        proposal_id = stable_identifier("federated-outbox", packets)
        return {
            "success": True,
            "proposal_id": proposal_id,
            "packets": packets,
            "rejected_claim_ids": rejected_ids,
            "claims_shared": 0,
            "broadcast_status": "not_started",
            "effect_proposal": (
                {
                    "effect_id": proposal_id,
                    "kind": "enqueue_federated_outbox",
                    "status": "proposed",
                    "service": "operations_control_service",
                    "payload": {"packets": packets},
                }
                if packets
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "Only released content hashes and evidence references are packaged; "
                "the KA performs no tenant lookup, database read, or broadcast."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA114FederatedOutbox(context).run(context)
