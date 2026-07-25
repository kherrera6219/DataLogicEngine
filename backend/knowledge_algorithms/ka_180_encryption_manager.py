"""KA-180: deterministic encryption-operation admission."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class EncryptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=200)
    operation: Literal["encrypt", "decrypt", "rewrap"]
    object_ref: str = Field(min_length=1, max_length=2_000)
    key_ref: str = Field(min_length=1, max_length=2_000)
    algorithm: Literal["AES-256-GCM", "ChaCha20-Poly1305"]
    purpose: str = Field(min_length=1, max_length=1_000)
    caller_authorized: bool
    key_active: bool


class KA180Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "requests": [
                        {
                            "request_id": "enc-1",
                            "operation": "encrypt",
                            "object_ref": "artifact-1",
                            "key_ref": "key-1",
                            "algorithm": "AES-256-GCM",
                            "purpose": "at-rest protection",
                            "caller_authorized": True,
                            "key_active": True,
                        }
                    ]
                }
            ]
        },
    )

    requests: list[EncryptionRequest] = Field(min_length=1, max_length=10_000)


class KA180EncryptionManager(KnowledgeAlgorithm):
    """Admit crypto-service requests without handling plaintext or key material."""

    input_schema = KA180Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-180"

    def _run_logic(self, input_data: KA180Input) -> dict[str, Any]:
        plans = []
        for item in sorted(input_data.requests, key=lambda row: row.request_id):
            blockers = []
            if not item.caller_authorized:
                blockers.append("caller_not_authorized")
            if not item.key_active:
                blockers.append("key_not_active")
            plans.append(
                {
                    "request_id": item.request_id,
                    "decision": "admit" if not blockers else "block",
                    "blockers": blockers,
                    "crypto_request": {
                        "operation": item.operation,
                        "object_ref": item.object_ref,
                        "key_ref": item.key_ref,
                        "algorithm": item.algorithm,
                        "purpose": item.purpose,
                    }
                    if not blockers
                    else None,
                }
            )
        return {
            "success": True,
            "status": "encryption_requests_evaluated",
            "plans": plans,
            "plaintext_or_key_material_processed": False,
            "operations_applied": 0,
            "deterministic": True,
            "limitations": (
                "An authoritative OS-backed crypto service must generate nonces, "
                "use protected keys, perform operations, and return receipts."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA180EncryptionManager(context).run(context)
