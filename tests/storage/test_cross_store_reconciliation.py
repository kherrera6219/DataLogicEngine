"""Phase 4 cross-store authority and identifier contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

import models
from backend.storage.data_contracts import (
    DATA_CONTRACT_SCHEMA_VERSION,
    LOGICAL_DATA_CONTRACTS,
    POSTGRES_ENTITY_KEYS,
    CrossStoreRecord,
    StoreAuthority,
    build_contract_manifest,
    validate_contract_registry,
)


def test_every_sqlalchemy_entity_has_one_postgresql_identity_contract():
    live_tables = set(models.db.metadata.tables)

    assert len(live_tables) == 83
    assert set(POSTGRES_ENTITY_KEYS) == live_tables
    assert validate_contract_registry(live_tables) == []


def test_plan_required_logical_data_classes_have_explicit_authority():
    required = {
        "external_api_clients_and_scopes",
        "virtual_models",
        "routing_policies",
        "idempotency_records",
        "admission_counters",
        "asynchronous_jobs_and_results",
        "ingestion_jobs_and_corpus_revisions",
        "provider_usage",
        "gateway_audit_events",
        "graph_nodes_and_relationships",
        "vector_embeddings",
        "truthlink_events",
        "unified_memory_graph",
        "audit_artifact_bundles",
        "simulation_artifacts",
        "deliverables",
        "trace_exports",
    }
    contracts = {contract.key: contract for contract in LOGICAL_DATA_CONTRACTS}

    assert required <= set(contracts)
    assert all(contract.authority for contract in contracts.values())
    assert all(
        contract.authority not in contract.materializations
        for contract in contracts.values()
    )


def test_object_authority_remains_minio_until_replacement_control_passes():
    object_contracts = [
        contract
        for contract in LOGICAL_DATA_CONTRACTS
        if contract.authority is StoreAuthority.MINIO
    ]

    assert object_contracts
    assert "seaweedfs" not in {authority.value for authority in StoreAuthority}


def test_cross_store_record_requires_stable_versioned_source_identity():
    record = CrossStoreRecord(
        entity_type="trace_run",
        entity_id="run-123",
        schema_version="trace-run.v1",
        source_revision="postgresql:trace_runs:42",
        correlation_id="corr-123",
        occurred_at=datetime(2026, 7, 13, tzinfo=UTC),
        payload_sha256="a" * 64,
    )

    assert record.record_key == "trace_run:run-123:postgresql:trace_runs:42"
    assert record.to_dict()["occurred_at"] == "2026-07-13T00:00:00+00:00"

    with pytest.raises(ValueError, match="source_revision_required"):
        CrossStoreRecord(
            entity_type="trace_run",
            entity_id="run-123",
            schema_version="trace-run.v1",
            source_revision="",
            correlation_id="corr-123",
            occurred_at=datetime.now(UTC),
            payload_sha256="a" * 64,
        )


def test_contract_manifest_is_deterministic_and_machine_readable():
    first = build_contract_manifest(models.db.metadata.tables)
    second = build_contract_manifest(models.db.metadata.tables)

    assert first == second
    assert first["schema_version"] == DATA_CONTRACT_SCHEMA_VERSION
    assert first["postgresql_entity_count"] == 83
    assert first["validation_errors"] == []
    assert first["release_constraints"]["object_store_architecture"] == "minio"
    assert first["release_constraints"]["seaweedfs_production_selected"] is False
