"""Versioned cross-store authority and stable-identifier contracts.

This module is intentionally declarative. It makes physical PostgreSQL entities
and logical multi-store data classes reviewable without connecting to a running
data plane. Phase 4 migration, outbox, backup, restore, and retention code must
consume this registry instead of inventing store ownership locally.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
from types import MappingProxyType
from typing import Iterable, Mapping


DATA_CONTRACT_SCHEMA_VERSION = "1.0.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class StoreAuthority(str, Enum):
    """Approved authority names; candidates are deliberately excluded."""

    POSTGRESQL = "postgresql"
    REDIS = "redis"
    NEO4J = "neo4j"
    CHROMA = "chroma"
    MINIO = "minio"
    LOCAL_JSON = "local_json"
    LOCAL_FILESYSTEM = "local_filesystem"
    DPAPI_VAULT = "dpapi_vault"


@dataclass(frozen=True, slots=True)
class LogicalDataContract:
    """Authority and materialization rule for one logical data class."""

    key: str
    authority: StoreAuthority
    stable_id: str
    schema_version: str
    source_revision: str
    materializations: tuple[StoreAuthority, ...] = ()
    transaction_boundary: str = "authority_store_transaction"
    compensating_action: str = "mark_partial_and_retry_from_authority"
    retention_class: str = "policy_required"
    implementation_status: str = "implemented"
    notes: str = ""


@dataclass(frozen=True, slots=True)
class CrossStoreRecord:
    """Required envelope for every outbox or reconciliation record."""

    entity_type: str
    entity_id: str
    schema_version: str
    source_revision: str
    correlation_id: str
    occurred_at: datetime
    payload_sha256: str

    def __post_init__(self) -> None:
        required = {
            "entity_type_required": self.entity_type,
            "entity_id_required": self.entity_id,
            "schema_version_required": self.schema_version,
            "source_revision_required": self.source_revision,
            "correlation_id_required": self.correlation_id,
        }
        for reason, value in required.items():
            if not str(value or "").strip():
                raise ValueError(reason)
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at_timezone_required")
        if not _SHA256_RE.fullmatch(str(self.payload_sha256 or "").lower()):
            raise ValueError("payload_sha256_invalid")

    @property
    def record_key(self) -> str:
        return f"{self.entity_type}:{self.entity_id}:{self.source_revision}"

    def to_dict(self) -> dict[str, str]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "schema_version": self.schema_version,
            "source_revision": self.source_revision,
            "correlation_id": self.correlation_id,
            "occurred_at": self.occurred_at.isoformat(),
            "payload_sha256": self.payload_sha256.lower(),
            "record_key": self.record_key,
        }


# A new SQLAlchemy table must be added here in the same change. Values are the
# stable primary-key fields that cross-store records must carry as strings.
POSTGRES_ENTITY_KEYS: Mapping[str, str] = MappingProxyType(
    {
        "ai_audit_events": "id",
        "api_keys": "id",
        "artifact_redactions": "redaction_id",
        "audit_logs": "id",
        "chat_messages": "id",
        "chat_sessions": "id",
        "claim_evidence_links": "id",
        "compliance_mappings": "mapping_id",
        "cross_store_materialization_states": "id",
        "cross_store_outbox_events": "id",
        "data_deletion_tombstones": "deletion_id",
        "evidence_conflicts": "conflict_id",
        "external_api_keys": "id",
        "feature_flag_audit_events": "id",
        "feature_flags": "id",
        "ka_artifact_links": "id",
        "llm_provider_usage": "id",
        "llm_providers": "id",
        "mcp_prompts": "id",
        "mcp_resources": "id",
        "mcp_servers": "id",
        "mcp_tools": "id",
        "memory_entries": "id",
        "model_routing_policies": "id",
        "password_history": "id",
        "persona_evidence_links": "id",
        "prompt_templates": "id",
        "simulation_sessions": "id",
        "stage_artifact_links": "id",
        "trace_artifacts": "artifact_id",
        "trace_axis_vectors": "vector_id",
        "trace_claims": "claim_id",
        "trace_evidence": "evidence_id",
        "trace_exports": "export_id",
        "trace_ka_invocations": "invocation_id",
        "trace_memory_events": "event_id",
        "trace_personas": "persona_id",
        "trace_policy_decisions": "decision_id",
        "trace_runs": "run_id",
        "trace_spans": "span_id",
        "trace_stage_logs": "log_id",
        "trace_stages": "stage_id",
        "truth_artifacts": "id",
        "truth_audit_events": "id",
        "truth_budgets": "id",
        "truth_link_messages": "id",
        "truth_metrics": "id",
        "truth_sessions": "id",
        "ukg_domains": "id",
        "ukg_edges": "id",
        "ukg_integrated_views": "id",
        "ukg_ka_executions": "id",
        "ukg_knowledge_algorithms": "id",
        "ukg_knowledge_edges": "id",
        "ukg_knowledge_nodes": "id",
        "ukg_locations": "id",
        "ukg_method_nodes": "id",
        "ukg_nodes": "id",
        "ukg_personas": "id",
        "ukg_perspectives": "id",
        "ukg_pillar_levels": "id",
        "ukg_sectors": "id",
        "ukg_sessions": "id",
        "ukg_time_contexts": "id",
        "user_ai_preferences": "id",
        "user_notification_preferences": "id",
        "users": "id",
    }
)


def _contract(
    key: str,
    authority: StoreAuthority,
    stable_id: str,
    *,
    materializations: tuple[StoreAuthority, ...] = (),
    status: str = "implemented",
    transaction: str = "authority_store_transaction",
    compensation: str = "mark_partial_and_retry_from_authority",
    retention: str = "policy_required",
    notes: str = "",
) -> LogicalDataContract:
    return LogicalDataContract(
        key=key,
        authority=authority,
        stable_id=stable_id,
        schema_version=f"{key}.v1",
        source_revision=f"{authority.value}:monotonic_revision",
        materializations=materializations,
        transaction_boundary=transaction,
        compensating_action=compensation,
        retention_class=retention,
        implementation_status=status,
        notes=notes,
    )


LOGICAL_DATA_CONTRACTS: tuple[LogicalDataContract, ...] = (
    _contract("owner_identity_and_sessions", StoreAuthority.POSTGRESQL, "users.id"),
    _contract(
        "external_api_clients_and_scopes",
        StoreAuthority.POSTGRESQL,
        "external_api_keys.id",
        materializations=(StoreAuthority.REDIS,),
    ),
    _contract(
        "provider_configuration",
        StoreAuthority.POSTGRESQL,
        "llm_providers.id",
        materializations=(StoreAuthority.DPAPI_VAULT,),
    ),
    _contract(
        "virtual_models",
        StoreAuthority.POSTGRESQL,
        "virtual_model.id",
        status="target_table_missing_phase_8_dependency",
    ),
    _contract(
        "routing_policies",
        StoreAuthority.POSTGRESQL,
        "model_routing_policies.id",
        materializations=(StoreAuthority.REDIS,),
    ),
    _contract(
        "idempotency_records",
        StoreAuthority.POSTGRESQL,
        "idempotency_record.id",
        materializations=(StoreAuthority.REDIS,),
        status="durable_target_table_missing",
        compensation="reject_duplicate_or_retry_pending_authority_record",
    ),
    _contract(
        "admission_counters",
        StoreAuthority.REDIS,
        "admission:{principal_id}:{window}:{policy_revision}",
        retention="operational_expiring",
        compensation="fail_closed_when_counter_state_is_unavailable",
    ),
    _contract(
        "asynchronous_jobs_and_results",
        StoreAuthority.POSTGRESQL,
        "job.id",
        materializations=(StoreAuthority.REDIS,),
        status="durable_job_and_result_tables_missing",
        compensation="requeue_only_from_committed_authority_state",
    ),
    _contract("provider_usage", StoreAuthority.POSTGRESQL, "llm_provider_usage.id"),
    _contract(
        "gateway_audit_events",
        StoreAuthority.POSTGRESQL,
        "ai_audit_events.id",
        materializations=(StoreAuthority.MINIO,),
        compensation="keep_request_incomplete_until_audit_bundle_is_verified",
        retention="audit_policy",
    ),
    _contract("chat_transcripts", StoreAuthority.POSTGRESQL, "chat_sessions.id/chat_messages.id"),
    _contract(
        "trace_records",
        StoreAuthority.POSTGRESQL,
        "trace_runs.run_id",
        materializations=(StoreAuthority.MINIO,),
        compensation="mark_trace_artifact_pending_and_reconcile",
        retention="trace_policy",
    ),
    _contract(
        "graph_nodes_and_relationships",
        StoreAuthority.POSTGRESQL,
        "ukg_knowledge_nodes.uid/ukg_knowledge_edges.source_node_id:type:target_node_id",
        materializations=(StoreAuthority.NEO4J,),
        transaction="postgres_outbox_then_idempotent_neo4j_merge",
        compensation="retain_outbox_pending_and_report_graph_degraded",
    ),
    _contract(
        "vector_embeddings",
        StoreAuthority.POSTGRESQL,
        "source_type:source_id:embedding_model:source_revision",
        materializations=(StoreAuthority.CHROMA,),
        transaction="postgres_outbox_then_idempotent_chroma_upsert",
        compensation="retain_source_revision_pending_and_rebuild_collection_entry",
    ),
    _contract(
        "truthlink_events",
        StoreAuthority.POSTGRESQL,
        "truth_link_messages.id",
        materializations=(StoreAuthority.REDIS,),
        transaction="postgres_outbox_then_redis_stream_publish",
        compensation="replay_unpublished_event_from_postgresql",
        retention="operational_event_policy",
    ),
    _contract(
        "unified_memory_graph",
        StoreAuthority.LOCAL_JSON,
        "vertex.vertex_id/edge.source_id:target_id:edge_type",
        materializations=(StoreAuthority.POSTGRESQL,),
        status="legacy_retained_authority_pending_phase_9_consolidation",
        transaction="atomic_file_replace",
        compensation="retain_previous_file_and_rebuild_from_last_valid_revision",
        retention="memory_policy",
    ),
    _contract(
        "audit_artifact_bundles",
        StoreAuthority.MINIO,
        "audit-logs/{run_id}.json",
        materializations=(StoreAuthority.POSTGRESQL,),
        transaction="postgres_outbox_then_required_object_put",
        compensation="keep_audit_commit_incomplete_and_retry_object_put",
        retention="audit_policy",
    ),
    _contract(
        "simulation_artifacts",
        StoreAuthority.MINIO,
        "simulation-artifacts/{snapshot_id}.json",
        materializations=(StoreAuthority.POSTGRESQL,),
        transaction="postgres_outbox_then_required_object_put",
        compensation="mark_simulation_artifact_pending_and_retry",
        retention="simulation_policy",
    ),
    _contract(
        "deliverables",
        StoreAuthority.MINIO,
        "deliverables/{workflow}/{deliverable_id}",
        materializations=(StoreAuthority.POSTGRESQL,),
        status="object_write_implemented_durable_index_incomplete",
        transaction="postgres_outbox_then_required_object_put",
        compensation="do_not_mark_deliverable_complete_until_object_hash_matches",
        retention="deliverable_policy",
    ),
    _contract(
        "trace_exports",
        StoreAuthority.MINIO,
        "trace-exports/{export_id}",
        materializations=(StoreAuthority.POSTGRESQL,),
        status="bucket_contract_implemented_workflow_migration_pending",
        transaction="postgres_outbox_then_required_object_put",
        compensation="keep_trace_export_pending_and_retry",
        retention="export_policy",
    ),
    _contract(
        "evaluation_data",
        StoreAuthority.MINIO,
        "evaluation-data/{dataset_revision}/{object_id}",
        materializations=(StoreAuthority.POSTGRESQL,),
        status="bucket_created_workflow_contract_pending",
        retention="evaluation_policy",
    ),
    _contract(
        "graph_snapshots",
        StoreAuthority.MINIO,
        "graphs/{graph_revision}/{object_id}",
        materializations=(StoreAuthority.NEO4J, StoreAuthority.POSTGRESQL),
        status="bucket_created_snapshot_workflow_pending",
        retention="graph_snapshot_policy",
    ),
    _contract(
        "mcp_metadata",
        StoreAuthority.POSTGRESQL,
        "mcp_servers/resources/tools/prompts.id",
    ),
    _contract(
        "service_credentials",
        StoreAuthority.DPAPI_VAULT,
        "installation_id:credential_schema_version",
        transaction="dpapi_encrypt_then_atomic_file_replace",
        compensation="retain_previous_vault_and_refuse_service_start",
        retention="installation_lifetime",
    ),
    _contract(
        "runtime_cache",
        StoreAuthority.REDIS,
        "cache_namespace:key:source_revision",
        retention="disposable_expiring",
        compensation="invalidate_and_recompute_from_authority",
    ),
    _contract(
        "retained_configuration",
        StoreAuthority.LOCAL_JSON,
        "configuration_file:schema_version",
        materializations=(StoreAuthority.DPAPI_VAULT,),
        transaction="validated_atomic_file_replace",
        compensation="retain_last_valid_configuration",
        retention="installation_lifetime",
    ),
    _contract(
        "coordinated_backup_manifest",
        StoreAuthority.LOCAL_FILESYSTEM,
        "backup_id:manifest_schema_version",
        materializations=(StoreAuthority.MINIO,),
        status="current_version_engineering_qualified_release_authorization_deferred",
        transaction="maintenance_mode_multi_store_checkpoint",
        compensation="discard_incomplete_backup_and_resume_only_after_visible_failure",
        retention="backup_policy",
    ),
    _contract(
        "deletion_tombstones",
        StoreAuthority.POSTGRESQL,
        "deletion_id:subject_digest:policy_version",
        transaction="cross_store_delete_then_remnant_reconciliation",
        compensation="retain_non_pii_tombstone_and_retry_failed_store",
        retention="deletion_proof_policy",
    ),
)


def validate_contract_registry(live_postgresql_tables: Iterable[str]) -> list[str]:
    """Return stable machine-readable validation errors for registry drift."""

    errors: list[str] = []
    live = {str(name) for name in live_postgresql_tables}
    registered = set(POSTGRES_ENTITY_KEYS)
    for table in sorted(live - registered):
        errors.append(f"unregistered_postgresql_entity:{table}")
    for table in sorted(registered - live):
        errors.append(f"stale_postgresql_entity_contract:{table}")

    keys = [contract.key for contract in LOGICAL_DATA_CONTRACTS]
    for key in sorted({key for key in keys if keys.count(key) > 1}):
        errors.append(f"duplicate_logical_data_contract:{key}")
    for contract in LOGICAL_DATA_CONTRACTS:
        if not contract.stable_id.strip():
            errors.append(f"stable_id_missing:{contract.key}")
        if not contract.schema_version.strip():
            errors.append(f"schema_version_missing:{contract.key}")
        if not contract.source_revision.strip():
            errors.append(f"source_revision_missing:{contract.key}")
        if contract.authority in contract.materializations:
            errors.append(f"authority_repeated_as_materialization:{contract.key}")
        if len(set(contract.materializations)) != len(contract.materializations):
            errors.append(f"duplicate_materialization:{contract.key}")
    return errors


def build_contract_manifest(live_postgresql_tables: Iterable[str]) -> dict[str, object]:
    """Build deterministic JSON-ready authority evidence."""

    live = sorted(str(name) for name in live_postgresql_tables)
    return {
        "schema_version": DATA_CONTRACT_SCHEMA_VERSION,
        "postgresql_entity_count": len(POSTGRES_ENTITY_KEYS),
        "postgresql_entities": [
            {"table": table, "stable_id_field": POSTGRES_ENTITY_KEYS[table]}
            for table in sorted(POSTGRES_ENTITY_KEYS)
        ],
        "logical_data_contracts": [
            {
                "key": contract.key,
                "authority": contract.authority.value,
                "stable_id": contract.stable_id,
                "schema_version": contract.schema_version,
                "source_revision": contract.source_revision,
                "materializations": [store.value for store in contract.materializations],
                "transaction_boundary": contract.transaction_boundary,
                "compensating_action": contract.compensating_action,
                "retention_class": contract.retention_class,
                "implementation_status": contract.implementation_status,
                "notes": contract.notes,
            }
            for contract in sorted(LOGICAL_DATA_CONTRACTS, key=lambda item: item.key)
        ],
        "validation_errors": validate_contract_registry(live),
        "release_constraints": {
            "object_store_architecture": StoreAuthority.MINIO.value,
            "seaweedfs_qualification_authorized": True,
            "seaweedfs_production_selected": False,
            "coordinated_backup_restore_engineering_qualified": True,
            "managed_backup_production_authorized": False,
            "supported_prior_release_upgrade_qualified": False,
            "at_rest_production_qualified": False,
        },
    }
