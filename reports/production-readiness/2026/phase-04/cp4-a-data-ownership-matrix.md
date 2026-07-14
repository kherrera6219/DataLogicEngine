# CP4-A Cross-Store Data Ownership Matrix

## Status

- Contract schema: `1.0.0`
- Captured: `2026-07-14T01:22:48.120703+00:00`
- PostgreSQL entities covered: **67**
- Registry errors: **0**
- Production object-store authority: **minio**
- SeaweedFS production selected: **No**
- Managed coordinated backup authorized: **No**

This matrix assigns exactly one authority to every current logical data
class and records all materialized copies. A materialization never becomes
authoritative merely because its service is reachable. Remaining durable
target gaps are assigned to their owning later production-plan phases.

## Logical data classes

| Data class | Authority | Stable ID | Materializations | Transaction boundary | Compensation | Status |
|---|---|---|---|---|---|---|
| admission_counters | redis | admission:{principal_id}:{window}:{policy_revision} | none | authority_store_transaction | fail_closed_when_counter_state_is_unavailable | implemented |
| asynchronous_jobs_and_results | postgresql | job.id | redis | authority_store_transaction | requeue_only_from_committed_authority_state | durable_job_and_result_tables_missing |
| audit_artifact_bundles | minio | audit-logs/{run_id}.json | postgresql | postgres_outbox_then_required_object_put | keep_audit_commit_incomplete_and_retry_object_put | implemented |
| chat_transcripts | postgresql | chat_sessions.id/chat_messages.id | none | authority_store_transaction | mark_partial_and_retry_from_authority | implemented |
| coordinated_backup_manifest | local_filesystem | backup_id:manifest_schema_version | minio | maintenance_mode_multi_store_checkpoint | discard_incomplete_backup_and_resume_only_after_visible_failure | current_version_engineering_qualified_release_authorization_deferred |
| deletion_tombstones | postgresql | deletion_id:subject_digest:policy_version | none | cross_store_delete_then_remnant_reconciliation | retain_non_pii_tombstone_and_retry_failed_store | implemented |
| deliverables | minio | deliverables/{workflow}/{deliverable_id} | postgresql | postgres_outbox_then_required_object_put | do_not_mark_deliverable_complete_until_object_hash_matches | object_write_implemented_durable_index_incomplete |
| evaluation_data | minio | evaluation-data/{dataset_revision}/{object_id} | postgresql | authority_store_transaction | mark_partial_and_retry_from_authority | bucket_created_workflow_contract_pending |
| external_api_clients_and_scopes | postgresql | external_api_keys.id | redis | authority_store_transaction | mark_partial_and_retry_from_authority | implemented |
| gateway_audit_events | postgresql | ai_audit_events.id | minio | authority_store_transaction | keep_request_incomplete_until_audit_bundle_is_verified | implemented |
| graph_nodes_and_relationships | postgresql | ukg_knowledge_nodes.uid/ukg_knowledge_edges.source_node_id:type:target_node_id | neo4j | postgres_outbox_then_idempotent_neo4j_merge | retain_outbox_pending_and_report_graph_degraded | implemented |
| graph_snapshots | minio | graphs/{graph_revision}/{object_id} | neo4j, postgresql | authority_store_transaction | mark_partial_and_retry_from_authority | bucket_created_snapshot_workflow_pending |
| idempotency_records | postgresql | idempotency_record.id | redis | authority_store_transaction | reject_duplicate_or_retry_pending_authority_record | durable_target_table_missing |
| mcp_metadata | postgresql | mcp_servers/resources/tools/prompts.id | none | authority_store_transaction | mark_partial_and_retry_from_authority | implemented |
| owner_identity_and_sessions | postgresql | users.id | none | authority_store_transaction | mark_partial_and_retry_from_authority | implemented |
| provider_configuration | postgresql | llm_providers.id | dpapi_vault | authority_store_transaction | mark_partial_and_retry_from_authority | implemented |
| provider_usage | postgresql | llm_provider_usage.id | none | authority_store_transaction | mark_partial_and_retry_from_authority | implemented |
| retained_configuration | local_json | configuration_file:schema_version | dpapi_vault | validated_atomic_file_replace | retain_last_valid_configuration | implemented |
| routing_policies | postgresql | model_routing_policies.id | redis | authority_store_transaction | mark_partial_and_retry_from_authority | implemented |
| runtime_cache | redis | cache_namespace:key:source_revision | none | authority_store_transaction | invalidate_and_recompute_from_authority | implemented |
| service_credentials | dpapi_vault | installation_id:credential_schema_version | none | dpapi_encrypt_then_atomic_file_replace | retain_previous_vault_and_refuse_service_start | implemented |
| simulation_artifacts | minio | simulation-artifacts/{snapshot_id}.json | postgresql | postgres_outbox_then_required_object_put | mark_simulation_artifact_pending_and_retry | implemented |
| trace_exports | minio | trace-exports/{export_id} | postgresql | postgres_outbox_then_required_object_put | keep_trace_export_pending_and_retry | bucket_contract_implemented_workflow_migration_pending |
| trace_records | postgresql | trace_runs.run_id | minio | authority_store_transaction | mark_trace_artifact_pending_and_reconcile | implemented |
| truthlink_events | postgresql | truth_link_messages.id | redis | postgres_outbox_then_redis_stream_publish | replay_unpublished_event_from_postgresql | implemented |
| unified_memory_graph | local_json | vertex.vertex_id/edge.source_id:target_id:edge_type | postgresql | atomic_file_replace | retain_previous_file_and_rebuild_from_last_valid_revision | legacy_retained_authority_pending_phase_9_consolidation |
| vector_embeddings | postgresql | source_type:source_id:embedding_model:source_revision | chroma | postgres_outbox_then_idempotent_chroma_upsert | retain_source_revision_pending_and_rebuild_collection_entry | implemented |
| virtual_models | postgresql | virtual_model.id | none | authority_store_transaction | mark_partial_and_retry_from_authority | target_table_missing_phase_8_dependency |

## PostgreSQL physical entities

Every SQLAlchemy table is PostgreSQL-owned as a physical record. The
logical matrix above separately identifies authoritative records and
their graph, vector, cache, object, or file materializations.

| Table | Stable primary identity |
|---|---|
| `ai_audit_events` | `id` |
| `api_keys` | `id` |
| `artifact_redactions` | `redaction_id` |
| `audit_logs` | `id` |
| `chat_messages` | `id` |
| `chat_sessions` | `id` |
| `claim_evidence_links` | `id` |
| `compliance_mappings` | `mapping_id` |
| `cross_store_materialization_states` | `id` |
| `cross_store_outbox_events` | `id` |
| `data_deletion_tombstones` | `deletion_id` |
| `evidence_conflicts` | `conflict_id` |
| `external_api_keys` | `id` |
| `feature_flag_audit_events` | `id` |
| `feature_flags` | `id` |
| `ka_artifact_links` | `id` |
| `llm_provider_usage` | `id` |
| `llm_providers` | `id` |
| `mcp_prompts` | `id` |
| `mcp_resources` | `id` |
| `mcp_servers` | `id` |
| `mcp_tools` | `id` |
| `memory_entries` | `id` |
| `model_routing_policies` | `id` |
| `password_history` | `id` |
| `persona_evidence_links` | `id` |
| `prompt_templates` | `id` |
| `simulation_sessions` | `id` |
| `stage_artifact_links` | `id` |
| `trace_artifacts` | `artifact_id` |
| `trace_axis_vectors` | `vector_id` |
| `trace_claims` | `claim_id` |
| `trace_evidence` | `evidence_id` |
| `trace_exports` | `export_id` |
| `trace_ka_invocations` | `invocation_id` |
| `trace_memory_events` | `event_id` |
| `trace_personas` | `persona_id` |
| `trace_policy_decisions` | `decision_id` |
| `trace_runs` | `run_id` |
| `trace_spans` | `span_id` |
| `trace_stage_logs` | `log_id` |
| `trace_stages` | `stage_id` |
| `truth_artifacts` | `id` |
| `truth_audit_events` | `id` |
| `truth_budgets` | `id` |
| `truth_link_messages` | `id` |
| `truth_metrics` | `id` |
| `truth_sessions` | `id` |
| `ukg_domains` | `id` |
| `ukg_edges` | `id` |
| `ukg_integrated_views` | `id` |
| `ukg_ka_executions` | `id` |
| `ukg_knowledge_algorithms` | `id` |
| `ukg_knowledge_edges` | `id` |
| `ukg_knowledge_nodes` | `id` |
| `ukg_locations` | `id` |
| `ukg_method_nodes` | `id` |
| `ukg_nodes` | `id` |
| `ukg_personas` | `id` |
| `ukg_perspectives` | `id` |
| `ukg_pillar_levels` | `id` |
| `ukg_sectors` | `id` |
| `ukg_sessions` | `id` |
| `ukg_time_contexts` | `id` |
| `user_ai_preferences` | `id` |
| `user_notification_preferences` | `id` |
| `users` | `id` |

## Open implementation gaps exposed by the contract

- `asynchronous_jobs_and_results`: `durable_job_and_result_tables_missing`.
- `coordinated_backup_manifest`: `current_version_engineering_qualified_release_authorization_deferred`.
- `deliverables`: `object_write_implemented_durable_index_incomplete`.
- `evaluation_data`: `bucket_created_workflow_contract_pending`.
- `graph_snapshots`: `bucket_created_snapshot_workflow_pending`.
- `idempotency_records`: `durable_target_table_missing`.
- `trace_exports`: `bucket_contract_implemented_workflow_migration_pending`.
- `unified_memory_graph`: `legacy_retained_authority_pending_phase_9_consolidation`.
- `virtual_models`: `target_table_missing_phase_8_dependency`.

## Required cross-store envelope

Every outbox/reconciliation record must carry `entity_type`, stable
`entity_id`, `schema_version`, `source_revision`, `correlation_id`, a
timezone-aware `occurred_at`, and `payload_sha256`. Partial success stays
visible and retryable until every required materialization confirms the
same source revision and payload hash.
