"""Durable PostgreSQL outbox and materialization-ledger contracts."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from flask import Flask

from extensions import db
from models import CrossStoreMaterializationState, CrossStoreOutboxEvent
from backend.dsqp import DSQPOrchestrator
from backend.storage.artifact_materialization import persist_object_artifact
from backend.storage.outbox import CrossStoreOutbox
from backend.storage.materialization_dispatcher import CrossStoreMaterializationDispatcher


def _app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    return app


def test_enqueue_is_transactional_idempotent_and_visible():
    app = _app()
    with app.app_context():
        db.create_all()
        outbox = CrossStoreOutbox(db.session)

        first = outbox.enqueue(
            entity_type="trace_run",
            entity_id="run-123",
            destination="minio",
            operation="put_audit_bundle",
            schema_version="trace-run.v1",
            source_revision="postgresql:trace_runs:42",
            payload={"run_id": "run-123", "bucket": "audit-logs"},
            correlation_id="corr-123",
        )
        second = outbox.enqueue(
            entity_type="trace_run",
            entity_id="run-123",
            destination="minio",
            operation="put_audit_bundle",
            schema_version="trace-run.v1",
            source_revision="postgresql:trace_runs:42",
            payload={"bucket": "audit-logs", "run_id": "run-123"},
            correlation_id="corr-123",
        )
        db.session.commit()

        assert first.id == second.id
        assert CrossStoreOutboxEvent.query.count() == 1
        state = CrossStoreMaterializationState.query.one()
        assert state.state == "pending"
        assert state.source_revision == "postgresql:trace_runs:42"
        assert state.payload_sha256 == first.payload_sha256


def test_success_and_failure_transitions_are_retryable_and_safe():
    app = _app()
    with app.app_context():
        db.create_all()
        outbox = CrossStoreOutbox(db.session)
        event = outbox.enqueue(
            entity_type="knowledge_node",
            entity_id="node-1",
            destination="neo4j",
            operation="upsert",
            schema_version="knowledge-node.v1",
            source_revision="postgresql:ukg_knowledge_nodes:7",
            payload={"uid": "node-1"},
            correlation_id="corr-node",
        )
        db.session.commit()

        claimed = outbox.claim_batch(destination="neo4j", limit=10)
        assert [item.id for item in claimed] == [event.id]
        assert claimed[0].attempts == 1

        outbox.mark_failed(claimed[0], safe_reason="database password was exposed")
        db.session.commit()
        assert event.status == "failed"
        assert event.safe_reason == "delivery_failed"
        assert "password" not in event.safe_reason

        event.available_at = None
        claimed = outbox.claim_batch(destination="neo4j", limit=10)
        outbox.mark_succeeded(claimed[0], observed_revision="neo4j:tx:99")
        db.session.commit()

        state = CrossStoreMaterializationState.query.one()
        assert event.status == "succeeded"
        assert state.state == "succeeded"
        assert state.observed_revision == "neo4j:tx:99"


def test_new_source_revision_reopens_materialization_state():
    app = _app()
    with app.app_context():
        db.create_all()
        outbox = CrossStoreOutbox(db.session)
        first = outbox.enqueue(
            entity_type="document",
            entity_id="doc-1",
            destination="chroma",
            operation="upsert_embedding",
            schema_version="document.v1",
            source_revision="postgresql:documents:1",
            payload={"text_hash": "a" * 64},
            correlation_id="corr-1",
        )
        outbox.mark_succeeded(first, observed_revision="chroma:doc-1:1")
        db.session.commit()

        second = outbox.enqueue(
            entity_type="document",
            entity_id="doc-1",
            destination="chroma",
            operation="upsert_embedding",
            schema_version="document.v1",
            source_revision="postgresql:documents:2",
            payload={"text_hash": "b" * 64},
            correlation_id="corr-2",
        )
        db.session.commit()

        state = CrossStoreMaterializationState.query.one()
        assert second.id != first.id
        assert state.state == "pending"
        assert state.source_revision == "postgresql:documents:2"
        assert state.observed_revision is None


def test_stale_processing_claim_is_recovered_after_worker_interruption():
    app = _app()
    with app.app_context():
        db.create_all()
        event = CrossStoreOutbox(db.session).enqueue(
            entity_type="knowledge_node",
            entity_id="node-stale",
            destination="neo4j",
            operation="merge_knowledge_node",
            schema_version="knowledge-node.v1",
            source_revision="source-1",
            payload={"node_uid": "node-stale"},
            correlation_id="corr-stale",
        )
        db.session.commit()
        CrossStoreOutbox(db.session).claim_batch(limit=1)
        event.locked_at = datetime.now(UTC) - timedelta(minutes=10)
        db.session.commit()

        reclaimed = CrossStoreOutbox(db.session).claim_batch(
            limit=1,
            processing_timeout_seconds=300,
        )

        assert [item.id for item in reclaimed] == [event.id]
        assert reclaimed[0].attempts == 2


def test_dispatcher_commits_success_and_safe_failure_per_event():
    app = _app()
    with app.app_context():
        db.create_all()
        outbox = CrossStoreOutbox(db.session)
        success = outbox.enqueue(
            entity_type="knowledge_node",
            entity_id="node-ok",
            destination="chroma",
            operation="upsert_knowledge_node",
            schema_version="knowledge-node.v1",
            source_revision="revision-ok",
            payload={"node_uid": "node-ok"},
            correlation_id="corr-ok",
        )
        failure = outbox.enqueue(
            entity_type="knowledge_node",
            entity_id="node-fail",
            destination="neo4j",
            operation="merge_knowledge_node",
            schema_version="knowledge-node.v1",
            source_revision="revision-fail",
            payload={"node_uid": "node-fail"},
            correlation_id="corr-fail",
        )
        db.session.commit()

        def fail(_event):
            raise RuntimeError("secret provider detail")

        result = CrossStoreMaterializationDispatcher(
            db.session,
            handlers={
                "chroma": lambda event: event.source_revision,
                "neo4j": fail,
            },
        ).run_once()

        assert result == {"claimed": 2, "succeeded": 1, "failed": 1}
        assert db.session.get(CrossStoreOutboxEvent, success.id).status == "succeeded"
        failed = db.session.get(CrossStoreOutboxEvent, failure.id)
        assert failed.status == "failed"
        assert failed.safe_reason == "neo4j_delivery_failed"


def test_required_frost_snapshot_is_queued_without_direct_cross_store_write(monkeypatch):
    app = _app()
    app.config["DLE_DATA_PLANE_DRIVER"] = "podman"
    with app.app_context():
        db.create_all()
        import backend.storage as storage_package

        monkeypatch.setattr(
            storage_package,
            "get_object_store",
            lambda: (_ for _ in ()).throw(AssertionError("direct object write")),
        )
        reference = persist_object_artifact(
            entity_type="frost_snapshot",
            entity_id="snapshot-1",
            bucket="simulation-artifacts",
            key="snapshot-1.json",
            body={"snapshot_id": "snapshot-1", "state": {"step": 4}},
            schema_version="frost-snapshot.v1",
            content_type="application/json",
            metadata={"run_id": "run-1"},
        )

        event = CrossStoreOutboxEvent.query.one()
        assert reference["status"] == "pending"
        assert event.destination == "minio"
        assert event.operation == "put_object"
        assert event.payload["bucket"] == "simulation-artifacts"
        assert event.payload["metadata"]["run_id"] == "run-1"


def test_frost_snapshot_materializes_without_simulation_authority_row(monkeypatch):
    app = _app()
    app.config["DLE_DATA_PLANE_DRIVER"] = "podman"

    class _ObjectStore:
        def __init__(self):
            self.objects = {}

        def create_bucket(self, _bucket):
            return True

        def put(self, bucket, key, body, **_kwargs):
            self.objects[(bucket, key)] = body
            return key

        def exists(self, bucket, key):
            return (bucket, key) in self.objects

        def get(self, bucket, key):
            return self.objects[(bucket, key)]

    store = _ObjectStore()
    with app.app_context():
        db.create_all()
        import backend.storage as storage_package

        monkeypatch.setattr(storage_package, "get_object_store", lambda: store)
        persist_object_artifact(
            entity_type="frost_snapshot",
            entity_id="snapshot-1",
            bucket="simulation-artifacts",
            key="snapshot-1.json",
            body={"snapshot_id": "snapshot-1", "state": {"step": 4}},
            schema_version="frost-snapshot.v1",
            content_type="application/json",
        )

        result = CrossStoreMaterializationDispatcher(db.session).run_once()
        event = CrossStoreOutboxEvent.query.one()

        assert result == {"claimed": 1, "succeeded": 1, "failed": 0}
        assert event.status == "succeeded"
        assert ("simulation-artifacts", "snapshot-1.json") in store.objects


def test_parallel_dsqp_construction_queues_four_deliverables_without_session_race():
    app = _app()
    app.config["DLE_DATA_PLANE_DRIVER"] = "podman"
    with app.app_context():
        db.create_all()

        result = asyncio.run(
            DSQPOrchestrator(timeout_seconds=5).construct_all(
                "Review a regulated AI workflow",
                {"active_axes": [8, 9, 10, 11]},
                active_axes=[8, 9, 10, 11],
                context={"risk_domain": "finance"},
            )
        )

        assert result["failures"] == {}
        assert set(result["profiles"]) == {"8", "9", "10", "11"}
        events = CrossStoreOutboxEvent.query.order_by(CrossStoreOutboxEvent.entity_id).all()
        assert len(events) == 4
        assert {event.entity_type for event in events} == {"dsqp_deliverable"}
        assert {event.status for event in events} == {"pending"}


def test_simulation_artifact_hash_mismatch_cannot_complete_session(monkeypatch):
    app = _app()
    app.config["DLE_DATA_PLANE_DRIVER"] = "podman"

    class _ObjectStore:
        def __init__(self):
            self.objects = {}

        def create_bucket(self, _bucket):
            return True

        def put(self, bucket, key, body, **_kwargs):
            self.objects[(bucket, key)] = body
            return key

        def exists(self, bucket, key):
            return (bucket, key) in self.objects

        def get(self, bucket, key):
            return self.objects[(bucket, key)]

    with app.app_context():
        db.create_all()
        import backend.storage as storage_package
        from models import SimulationArtifact, SimulationSession, User

        monkeypatch.setattr(storage_package, "get_object_store", _ObjectStore)
        user = User(username="simulation-hash", _email="simulation-hash@local", active=True)
        db.session.add(user)
        db.session.flush()
        simulation = SimulationSession(
            session_id="00000000-0000-0000-0000-000000000010",
            user_id=user.id,
            parameters={"query": "hash mismatch"},
            status="materialization_pending",
            artifact_state="materialization_pending",
        )
        db.session.add(simulation)
        reference = persist_object_artifact(
            entity_type="simulation_artifact",
            entity_id=f"{simulation.session_id}:result",
            bucket="simulation-artifacts",
            key=f"simulations/{simulation.session_id}/result.json",
            body={"schema_version": "simulation-result.v1", "status": "completed"},
            schema_version="simulation-result.v1",
            content_type="application/json",
            commit=False,
        )
        db.session.add(
            SimulationArtifact(
                session_id=simulation.session_id,
                artifact_type="result",
                schema_version="simulation-result.v1",
                revision="0" * 64,
                object_key=reference["key"],
                sha256="0" * 64,
                size_bytes=reference["size_bytes"],
                state="pending",
                metadata_json={"bucket": reference["bucket"]},
            )
        )
        db.session.commit()

        result = CrossStoreMaterializationDispatcher(db.session).run_once()

        assert result == {"claimed": 1, "succeeded": 0, "failed": 1}
        db.session.refresh(simulation)
        assert simulation.status == "materialization_pending"
        assert SimulationArtifact.query.one().state == "pending"
