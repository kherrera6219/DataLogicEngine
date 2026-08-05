"""Release-gated owner boundary for knowledge-content evolution proposals."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleCoordinator,
    KnowledgeLifecycleError,
    KnowledgeLifecycleExecution,
)


@dataclass(slots=True)
class KnowledgeContentEvolutionReview:
    execution: KnowledgeLifecycleExecution
    receipts: dict[str, dict[str, Any]]

    @property
    def ok(self) -> bool:
        return self.execution.ok and set(self.execution.executed_ids).issuperset(
            self.receipts
        )


class KnowledgeLifecycleService:
    """Consume content proposals and reject effects without release authority."""

    def __init__(self, coordinator: KnowledgeLifecycleCoordinator | None = None):
        self.coordinator = coordinator or KnowledgeLifecycleCoordinator()
        self._receipts: dict[str, dict[str, Any]] = {}

    def review_content_evolution_sync(
        self,
        *,
        requested_ids: list[str],
        ka_inputs: dict[str, dict[str, Any]],
        request_id: str,
        run_id: str,
        principal_id: str,
        release_authorized: bool = False,
    ) -> KnowledgeContentEvolutionReview:
        if release_authorized:
            raise KnowledgeLifecycleError(
                "content application requires the separate release transaction"
            )
        if not principal_id.strip():
            raise KnowledgeLifecycleError("content review requires a principal")
        execution = self.coordinator.execute_operation_sync(
            owner="truthmemory_truthlink_frost",
            operation="content_evolution",
            requested_ids=requested_ids,
            ka_inputs=ka_inputs,
            request_id=request_id,
            run_id=run_id,
            max_effects=32,
            principal_id=principal_id,
            service_capabilities={
                "knowledge_lifecycle_service",
                "knowledge_store_service",
            },
            policy_decisions={"content_release_authorized": False},
        )
        receipts: dict[str, dict[str, Any]] = {}
        for canonical_id in sorted(set(requested_ids)):
            idempotency_key = sha256(
                f"{request_id}:{run_id}:{canonical_id}:content".encode()
            ).hexdigest()
            receipt = self._receipts.get(idempotency_key)
            if receipt is None:
                receipt = {
                    "schema_version": "dle.knowledge-content-review-receipt.v1",
                    "service": "KnowledgeLifecycleService",
                    "canonical_id": canonical_id,
                    "status": "release_not_authorized",
                    "applied": False,
                    "rollback_status": "not_required_no_mutation",
                    "idempotency_key": idempotency_key,
                    "plan_id": execution.plan.plan_id,
                }
                self._receipts[idempotency_key] = receipt
            receipts[canonical_id] = dict(receipt)
        return KnowledgeContentEvolutionReview(execution, receipts)
