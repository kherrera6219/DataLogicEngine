"""Retention policy registry and fail-closed cross-store deletion reconciliation."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from models import DataDeletionTombstone

RETENTION_POLICY_VERSION = "2026.07.13-v1"
RETENTION_CLASSES = {
    "chats": "owner_delete_or_configured_history_expiry",
    "traces": "owner_delete_except_explicit_regulatory_hold",
    "prompts": "owner_delete_or_template_governance_policy",
    "provider_responses": "owner_delete_or_minimized_noncontent_usage_record",
    "external_client_requests": "owner_delete_or_security_audit_hold",
    "idempotency_state": "operational_expiry",
    "gateway_jobs_results": "owner_delete_or_operational_expiry",
    "usage": "minimized_financial_and_security_policy",
    "client_key_metadata": "revocation_plus_security_audit_policy",
    "gateway_audits": "immutable_only_for_disclosed_security_or_regulatory_basis",
    "evidence": "trace_policy",
    "logs": "rotation_policy_with_no_prompt_or_response_content",
    "simulations": "owner_delete",
    "ingested_content": "owner_or_tenant_delete",
    "exports": "owner_delete_or_export_expiry",
    "backups": "backup_retention_then_archive_expiry",
    "cache": "operational_expiry_or_immediate_invalidation",
}


class RetentionDeleteError(RuntimeError):
    """Redaction-safe deletion or remnant reconciliation failure."""


@dataclass(frozen=True, slots=True)
class DeletionSubject:
    subject_type: str
    subject_id: str
    tenant_id: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteResult:
    deleted_count: int
    retained_count: int = 0
    retention_basis: str | None = None


class DeletionAdapter(Protocol):
    def delete(self, subject: DeletionSubject) -> DeleteResult: ...

    def remnant_count(self, subject: DeletionSubject) -> int: ...


class RetentionDeleteCoordinator:
    """Delete across all stores and retain only a keyed, non-PII proof record."""

    def __init__(
        self,
        *,
        session,
        adapters: dict[str, DeletionAdapter],
        required_stores: tuple[str, ...],
        digest_key: str,
        knowledge_lifecycle=None,
    ) -> None:
        if set(adapters) != set(required_stores):
            raise ValueError("deletion_required_store_mismatch")
        if len(str(digest_key or "")) < 16:
            raise ValueError("deletion_digest_key_invalid")
        self.session = session
        self.adapters = dict(adapters)
        self.required_stores = tuple(required_stores)
        self.digest_key = str(digest_key).encode("utf-8")
        if knowledge_lifecycle is None:
            from backend.governed_execution.knowledge_lifecycle import (
                KnowledgeLifecycleCoordinator,
            )

            knowledge_lifecycle = KnowledgeLifecycleCoordinator()
        self.knowledge_lifecycle = knowledge_lifecycle
        self.lifecycle_evidence: dict[str, object] = {}

    def run(self, subject: DeletionSubject) -> DataDeletionTombstone:
        normalized_type = str(subject.subject_type or "").strip().lower()
        normalized_id = str(subject.subject_id or "").strip()
        if normalized_type not in {"user", "tenant"} or not normalized_id:
            raise ValueError("deletion_subject_invalid")
        cache_plan = self.knowledge_lifecycle.execute_operation_sync(
            owner="retrieval_graph_memory",
            operation="maintenance",
            requested_ids=["KA-080"],
            ka_inputs={
                "KA-080": {
                    "key": f"{normalized_type}:{normalized_id}",
                    "operation": "delete",
                    "cache_state": {},
                }
            },
            request_id=f"deletion:{normalized_type}:{normalized_id}",
            run_id=f"deletion:{normalized_type}:{normalized_id}",
            max_effects=4,
            principal_id="retention_delete_coordinator",
            tier="maintenance",
            layer="data",
            service_capabilities={"knowledge_store_service"},
        )
        self.lifecycle_evidence["cache_invalidation"] = cache_plan.to_dict()
        digest = hmac.new(
            self.digest_key,
            f"{normalized_type}:{normalized_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        tombstone = DataDeletionTombstone(
            subject_type=normalized_type,
            subject_digest=digest,
            policy_version=RETENTION_POLICY_VERSION,
            status="processing",
            store_status={},
            attempts=1,
        )
        self.session.add(tombstone)
        self.session.commit()

        statuses: dict[str, dict[str, object]] = {}
        failed = False
        ordered_stores = [
            *sorted(store for store in self.adapters if store != "postgresql"),
            *(["postgresql"] if "postgresql" in self.adapters else []),
        ]
        for store in ordered_stores:
            adapter = self.adapters[store]
            try:
                result = adapter.delete(subject)
                remnants = int(adapter.remnant_count(subject))
                if remnants < 0:
                    raise RetentionDeleteError("deletion_remnant_count_invalid")
                if remnants:
                    if result.retained_count != remnants or not result.retention_basis:
                        raise RetentionDeleteError("unapproved_deletion_remnants")
                    status = "retained_by_policy"
                else:
                    status = "pass"
                statuses[store] = {
                    "status": status,
                    "deleted_count": max(0, int(result.deleted_count)),
                    "retained_count": remnants,
                    "retention_basis": result.retention_basis,
                }
            except Exception:
                failed = True
                statuses[store] = {
                    "status": "failed",
                    "deleted_count": 0,
                    "retained_count": None,
                    "retention_basis": None,
                    "safe_reason": f"{store}_deletion_failed",
                }
        recovery_plan = self.knowledge_lifecycle.execute_operation_sync(
            owner="truthmemory_truthlink_frost",
            operation="maintenance",
            requested_ids=["KA-064"],
            ka_inputs={
                "KA-064": {
                    "error_logs": [
                        {
                            "message": f"{store}_deletion_failed",
                            "store": store,
                        }
                        for store, status in statuses.items()
                        if status.get("status") == "failed"
                    ]
                }
            },
            request_id=f"deletion:{normalized_type}:{normalized_id}:recovery",
            run_id=f"deletion:{normalized_type}:{normalized_id}:recovery",
            max_effects=4,
            principal_id="retention_delete_coordinator",
            tier="maintenance",
            layer="data",
            service_capabilities={"knowledge_lifecycle_service"},
        )
        self.lifecycle_evidence["failure_recovery"] = recovery_plan.to_dict()
        tombstone.store_status = dict(statuses)
        self.session.add(tombstone)
        self.session.commit()

        if failed:
            tombstone.status = "partial_failure"
            tombstone.safe_reason = "cross_store_deletion_incomplete"
            self.session.commit()
            raise RetentionDeleteError("cross_store_deletion_incomplete")
        tombstone.status = "completed"
        tombstone.safe_reason = None
        tombstone.completed_at = datetime.now(UTC)
        self.session.commit()
        return tombstone
