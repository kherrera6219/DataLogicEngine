import uuid
import json
from types import SimpleNamespace

import app as app_module
from app import db
from backend.dsqp import DSQPChain
from backend.truth_engine.truth_memory.commit_service import TruthMemoryCommitService
from core.system.frost_service import FROSTService
from models import TraceRun, TruthAuditEvent


class FakeObjectStore:
    def __init__(self):
        self.buckets = []
        self.objects = {}

    def create_bucket(self, bucket):
        self.buckets.append(bucket)
        return True

    def put(self, bucket, key, data, content_type=None, metadata=None):
        self.objects[(bucket, key)] = {
            "data": data,
            "content_type": content_type,
            "metadata": metadata or {},
        }
        return key

    def list(self, bucket, prefix=""):
        return [
            SimpleNamespace(key=key, size=len(value["data"]))
            for (stored_bucket, key), value in self.objects.items()
            if stored_bucket == bucket and key.startswith(prefix)
        ]


def test_truth_audit_event_has_db_o_artifact_fields():
    columns = TruthAuditEvent.__table__.columns

    assert "object_store_bucket" in columns
    assert "object_store_key" in columns
    assert "merkle_root" in columns
    assert "blockchain_anchor_tx" in columns
    assert "blockchain_anchor_status" in columns


def test_commit_writes_audit_bundle_object_and_anchor_metadata(app, monkeypatch):
    import backend.storage as storage_module

    fake_store = FakeObjectStore()
    monkeypatch.setattr(storage_module, "get_object_store", lambda: fake_store)
    monkeypatch.setattr(
        TruthMemoryCommitService,
        "_anchor_merkle_root",
        staticmethod(lambda run, merkle_root: {
            "merkle_root": merkle_root,
            "transaction_hash": "0xabc123",
            "network": "simulated-production",
        }),
    )

    with app.app_context():
        run = TraceRun(
            run_id=uuid.uuid4(),
            status="pass",
            tier="3",
            input_message="input",
            final_answer="answer",
            confidence=0.91,
            truthgate_decision="allow",
        )
        db.session.add(run)
        db.session.commit()

        receipt = TruthMemoryCommitService().commit(run, db.session)

        event = TruthAuditEvent.query.filter_by(event_type="audit_bundle_commit").first()
        assert receipt
        assert event is not None
        assert event.object_store_bucket == "audit_logs"
        assert event.object_store_key == f"{run.run_id}.json"
        assert event.merkle_root
        assert event.blockchain_anchor_tx == "0xabc123"
        assert event.blockchain_anchor_status == "anchored"
        assert ("audit_logs", f"{run.run_id}.json") in fake_store.objects
        assert event.event_data["object_store"]["key"] == f"{run.run_id}.json"
        assert event.event_data["blockchain_anchor"]["transaction_hash"] == "0xabc123"


def test_frost_snapshot_writes_simulation_artifact(monkeypatch):
    import backend.storage as storage_module

    fake_store = FakeObjectStore()
    monkeypatch.setattr(storage_module, "get_object_store", lambda: fake_store)

    service = FROSTService()
    snapshot_id = service.snapshot({"step": "l4", "score": 0.87}, {"run_id": "run-1"})

    key = f"{snapshot_id}.json"
    assert service.verify_snapshot(snapshot_id)
    assert ("simulation_artifacts", key) in fake_store.objects
    assert service.snapshot_metadata[snapshot_id]["object_store"]["bucket"] == "simulation_artifacts"

    payload = json.loads(fake_store.objects[("simulation_artifacts", key)]["data"])
    assert payload["snapshot_id"] == snapshot_id
    assert payload["state"]["step"] == "l4"
    assert payload["integrity"]["content_sha256"]


def test_dsqp_chain_writes_deliverable_artifact(monkeypatch):
    import backend.storage as storage_module

    fake_store = FakeObjectStore()
    monkeypatch.setattr(storage_module, "get_object_store", lambda: fake_store)

    persona = DSQPChain().construct(
        "Assess acquisition compliance",
        axis_number=10,
        coordinate_path="17.high_stakes.7.truthcore",
    )

    key = f"dsqp/{persona.persona_id}.json"
    assert ("deliverables", key) in fake_store.objects
    assert persona.metadata["object_store"]["bucket"] == "deliverables"
    assert persona.metadata["object_store"]["key"] == key

    payload = json.loads(fake_store.objects[("deliverables", key)]["data"])
    assert payload["persona_id"] == persona.persona_id
    assert payload["axis_number"] == 10
    assert payload["components"]["job_role"]["title"]


def test_health_bucket_stats_reports_object_counts(monkeypatch):
    import backend.storage.object_store as object_store_module

    fake_store = FakeObjectStore()
    fake_store.put("audit_logs", "run-1.json", b"abc")
    fake_store.put("deliverables", "dsqp/persona.json", b"12345")
    monkeypatch.setattr(object_store_module, "get_object_store", lambda: fake_store)

    stats = app_module._object_store_bucket_stats()

    assert stats["status"] == "ok"
    assert stats["buckets"]["audit_logs"] == {"object_count": 1, "total_bytes": 3}
    assert stats["buckets"]["deliverables"] == {"object_count": 1, "total_bytes": 5}
