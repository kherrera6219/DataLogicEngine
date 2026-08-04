"""Authoritative, content-free knowledge temporal-health review ledger."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

from backend.governed_execution.extended_subsystems import AuthoritativeEffectReceipt
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator
from backend.knowledge_algorithms.selection import KATraceState

BATCH_12_IDS = (
    "KA-023",
    "KA-052",
    "KA-064",
    "KA-1082",
    "KA-1083",
    "KA-1093",
    "KA-1105",
)


class KnowledgeTemporalHealthError(RuntimeError):
    """Raised when temporal-health review cannot be recorded safely."""


class KnowledgeTemporalHealthCoordinator(KnowledgeLifecycleCoordinator):
    """CP19-H owner dispatch with authoritative receipt helpers."""

    @staticmethod
    def sha256_payload(payload: Any) -> str:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def bind_effect_receipt(
        self,
        *,
        service: str,
        operation: str,
        resource_id: str,
        request_payload: Any,
        result_payload: Any,
        idempotency_key: str,
        ka_execution: Any,
        proposal_ids: list[str],
    ) -> AuthoritativeEffectReceipt:
        return AuthoritativeEffectReceipt(
            service=service,
            operation=operation,
            resource_id=resource_id,
            request_sha256=self.sha256_payload(request_payload),
            result_sha256=self.sha256_payload(result_payload),
            idempotency_key=idempotency_key,
            ka_plan_id=str(ka_execution.plan.plan_id),
            ka_proposal_ids=sorted(set(proposal_ids)),
        )

    @staticmethod
    def execution_outputs(execution: Any) -> dict[str, dict[str, Any]]:
        return {
            canonical_id: dict(result.get("output") or {})
            for canonical_id, result in execution.results.items()
        }

    @staticmethod
    def lifecycle_evidence(execution: Any) -> dict[str, Any]:
        return {
            "schema_version": "dle.ka-lifecycle-evidence.v1",
            "owner": execution.owner,
            "operation": execution.operation,
            "plan_id": execution.plan.plan_id,
            "manifest_version": execution.plan.manifest_version,
            "status": execution.report.status.value,
            "selected_ids": list(execution.plan.selected_ids),
            "executed_ids": list(execution.executed_ids),
            "execution_order": list(execution.plan.execution_order),
            "required_failure": execution.report.required_failure,
        }


class KnowledgeTemporalHealthService:
    """Record one idempotent review; never apply a knowledge lifecycle change."""

    def __init__(
        self,
        *,
        review_root: Path | None = None,
        coordinator: KnowledgeTemporalHealthCoordinator | None = None,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        self.review_root = (
            Path(review_root).resolve()
            if review_root is not None
            else (repository_root / "instance" / "knowledge-temporal-health").resolve()
        )
        self.coordinator = coordinator or KnowledgeTemporalHealthCoordinator()

    def record_review(
        self,
        *,
        ka_inputs: dict[str, dict[str, Any]],
        idempotency_key: str,
        request_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        """Execute the exact Batch 12 owner chain and persist only safe evidence."""
        self._validate_identity(
            idempotency_key=idempotency_key,
            request_id=request_id,
            principal_id=principal_id,
        )
        if set(ka_inputs) != set(BATCH_12_IDS):
            raise KnowledgeTemporalHealthError(
                "Temporal-health review requires the exact Batch 12 KA inputs"
            )
        execution = self.coordinator.execute_operation_sync(
            owner="truthmemory_truthlink_frost",
            operation="maintenance",
            requested_ids=list(BATCH_12_IDS),
            ka_inputs=ka_inputs,
            request_id=request_id,
            run_id=f"knowledge-temporal-health:{request_id}",
            max_effects=len(BATCH_12_IDS),
            session_id=request_id,
            principal_id=principal_id,
            tier="maintenance",
            layer="knowledge_temporal_health",
            service_capabilities={"knowledge_lifecycle_service"},
            required=True,
        )
        outputs = self._validate_execution(execution)
        request_payload = {
            "schema_version": "dle.knowledge-temporal-health-request.v1",
            "ka_input_sha256": self.coordinator.sha256_payload(ka_inputs),
            "principal_sha256": self._sha256_text(principal_id),
        }
        request_sha256 = self.coordinator.sha256_payload(request_payload)
        review_id = (
            "knowledge-temporal-health-" + self._sha256_text(idempotency_key)[:24]
        )
        target = self.review_root / f"{review_id}.json"
        existing = self._read_existing(
            target,
            request_sha256=request_sha256,
        )
        if existing is not None:
            return existing

        summaries = {
            canonical_id: {
                "status": str(outputs[canonical_id]["status"]),
                "result_sha256": self.coordinator.sha256_payload(outputs[canonical_id]),
                "proposal_count": self._proposal_count(
                    canonical_id,
                    outputs[canonical_id],
                ),
            }
            for canonical_id in BATCH_12_IDS
        }
        lifecycle = self.coordinator.lifecycle_evidence(execution)
        lifecycle["trace_states"] = {
            canonical_id: [event.state.value for event in trace.events]
            for canonical_id, trace in sorted(execution.report.traces.items())
        }
        record = {
            "schema_version": "dle.knowledge-temporal-health-review.v1",
            "review_id": review_id,
            "status": "MAINTENANCE_REVIEW_RECORDED",
            "request_sha256": request_sha256,
            "algorithm_summaries": summaries,
            "lifecycle": lifecycle,
            "knowledge_updates_applied": False,
            "confidence_updates_applied": False,
            "trust_updates_applied": False,
            "versions_created": 0,
            "retirements_applied": 0,
            "jobs_scheduled": 0,
            "alerts_dispatched": 0,
            "blacklisting_applied": False,
            "revalidation_requests_dispatched": 0,
            "provider_calls_applied": 0,
            "external_egress_applied": False,
        }
        proposal_ids = sorted(
            {
                str(output.get("plan_sha256"))
                for output in outputs.values()
                if output.get("plan_sha256")
            }
        )
        receipt = self.coordinator.bind_effect_receipt(
            service=self.__class__.__name__,
            operation="record_knowledge_temporal_health_review",
            resource_id=review_id,
            request_payload=request_payload,
            result_payload=record,
            idempotency_key=idempotency_key,
            ka_execution=execution,
            proposal_ids=proposal_ids,
        ).to_dict()
        record["authoritative_effect_receipt"] = receipt
        return self._write_once(target, record)

    def _validate_execution(self, execution: Any) -> dict[str, dict[str, Any]]:
        if set(execution.executed_ids) != set(BATCH_12_IDS):
            raise KnowledgeTemporalHealthError(
                "Temporal-health owner did not execute the exact qualified chain"
            )
        outputs = self.coordinator.execution_outputs(execution)
        expected_status = {
            "KA-023": "belief_decay_proposed",
            "KA-052": "temporal_maintenance_proposed",
            "KA-064": "failure_patterns_measured",
            "KA-1082": "confidence_drift_measured",
            "KA-1083": "revalidation_schedule_planned",
            "KA-1093": "trust_decay_calculated",
            "KA-1105": "conceptual_obsolescence_assessed",
        }
        if any(
            outputs.get(canonical_id, {}).get("status") != status
            for canonical_id, status in expected_status.items()
        ):
            raise KnowledgeTemporalHealthError(
                "Temporal-health output status failed owner validation"
            )
        forbidden_claims = (
            outputs["KA-023"].get("confidence_updates_applied") is not False,
            outputs["KA-052"].get("knowledge_updated") is not False,
            outputs["KA-052"].get("versions_created") != 0,
            outputs["KA-052"].get("retirements_applied") != 0,
            outputs["KA-064"].get("alerts_dispatched") != 0,
            outputs["KA-064"].get("blacklisting_applied") is not False,
            outputs["KA-064"].get("log_content_scanned") is not False,
            outputs["KA-1082"].get("measurement_status") != "observational",
            outputs["KA-1083"].get("jobs_scheduled") != 0,
            outputs["KA-1083"].get("dependency_consumed") != "KA-1082",
            outputs["KA-1093"].get("trust_updates_applied") is not False,
            outputs["KA-1105"].get("requests_dispatched") != 0,
            outputs["KA-1105"].get("knowledge_updated") is not False,
            outputs["KA-1105"].get("dependencies_consumed") != ["KA-1082", "KA-1083"],
        )
        if any(forbidden_claims):
            raise KnowledgeTemporalHealthError(
                "Temporal-health KA made an unsupported effect or dependency claim"
            )
        for canonical_id in BATCH_12_IDS:
            states = execution.report.traces[canonical_id].events
            if not any(event.state is KATraceState.EXECUTED for event in states):
                raise KnowledgeTemporalHealthError(
                    f"{canonical_id} has no committed execution trace"
                )
        return outputs

    @staticmethod
    def _proposal_count(canonical_id: str, output: dict[str, Any]) -> int:
        field = {
            "KA-023": "proposals",
            "KA-052": "proposals",
            "KA-064": "patterns",
            "KA-1082": "measurements",
            "KA-1083": "schedule",
            "KA-1093": "proposals",
            "KA-1105": "assessments",
        }[canonical_id]
        rows = output.get(field)
        return len(rows) if isinstance(rows, list) else 0

    @staticmethod
    def _validate_identity(
        *,
        idempotency_key: str,
        request_id: str,
        principal_id: str,
    ) -> None:
        if not 8 <= len(str(idempotency_key or "")) <= 200:
            raise KnowledgeTemporalHealthError(
                "Idempotency key must contain 8 through 200 characters"
            )
        if not 1 <= len(str(request_id or "")) <= 200:
            raise KnowledgeTemporalHealthError(
                "Request ID must contain 1 through 200 characters"
            )
        if not 1 <= len(str(principal_id or "")) <= 200:
            raise KnowledgeTemporalHealthError(
                "Principal ID must contain 1 through 200 characters"
            )

    def _read_existing(
        self,
        target: Path,
        *,
        request_sha256: str,
    ) -> dict[str, Any] | None:
        if not target.exists():
            return None
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise KnowledgeTemporalHealthError(
                "Existing temporal-health review is unreadable"
            ) from exc
        if payload.get("request_sha256") != request_sha256:
            raise KnowledgeTemporalHealthError(
                "Idempotency key was already used for a different review"
            )
        self._validate_existing_receipt(target, payload)
        return payload

    def _validate_existing_receipt(
        self,
        target: Path,
        payload: dict[str, Any],
    ) -> None:
        receipt = payload.get("authoritative_effect_receipt")
        review_id = str(payload.get("review_id") or "")
        base_payload = dict(payload)
        base_payload.pop("authoritative_effect_receipt", None)
        valid = bool(
            payload.get("schema_version") == "dle.knowledge-temporal-health-review.v1"
            and payload.get("status") == "MAINTENANCE_REVIEW_RECORDED"
            and review_id == target.stem
            and isinstance(receipt, dict)
            and receipt.get("schema_version") == "dle.authoritative-effect-receipt.v1"
            and receipt.get("status") == "applied"
            and receipt.get("service") == self.__class__.__name__
            and receipt.get("operation") == "record_knowledge_temporal_health_review"
            and receipt.get("resource_id") == review_id
            and receipt.get("request_sha256") == payload.get("request_sha256")
            and review_id
            == "knowledge-temporal-health-"
            + self._sha256_text(str(receipt.get("idempotency_key") or ""))[:24]
            and hmac.compare_digest(
                str(receipt.get("result_sha256") or ""),
                self.coordinator.sha256_payload(base_payload),
            )
        )
        if not valid:
            raise KnowledgeTemporalHealthError(
                "Existing temporal-health review failed integrity validation"
            )

    def _write_once(
        self,
        target: Path,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self.review_root.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            return payload
        except FileExistsError:
            existing = self._read_existing(
                target,
                request_sha256=str(payload["request_sha256"]),
            )
            if existing is None:
                raise KnowledgeTemporalHealthError(
                    "Temporal-health review write lost its idempotency race"
                )
            return existing

    @staticmethod
    def _sha256_text(value: str) -> str:
        return hashlib.sha256(str(value).encode("utf-8")).hexdigest()
