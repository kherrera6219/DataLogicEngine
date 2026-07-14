import asyncio
import json
import sys
import uuid

from backend.mcp_server.router import MCPRouter
from backend.mcp_server.subscriptions import MCPSubscriptionManager
from backend.truth_engine.truth_gate.opa_policy import OPAPolicyEvaluator
from backend.truth_engine.truth_memory.mlflow_tracker import TruthMemoryMLflowTracker
from backend.truth_engine.truth_memory.provenance import ProvenanceRecord
from backend.truth_engine.truth_memory.commit_service import TruthMemoryCommitService
from models import TraceRun, TruthAuditEvent
from app import db


def test_truthmemory_mlflow_tracker_writes_local_jsonl(tmp_path):
    tracker = TruthMemoryMLflowTracker(tracking_uri=str(tmp_path / "mlruns"))

    result = tracker.record_session(
        {
            "session_id": "session-1",
            "tier": "moderate",
            "confidence_score": 0.91,
            "processing_time_ms": 123,
        }
    )

    assert result["tracked"] is True
    assert result["backend"] in {"jsonl", "mlflow"}
    if result["backend"] == "jsonl":
        path = tmp_path / "mlruns" / "truthmemory_sessions.jsonl"
        assert path.exists()
        payload = json.loads(path.read_text(encoding="utf-8").strip())
        assert payload["session_id"] == "session-1"


def test_opa_policy_fallback_denies_critical_low_confidence():
    result = OPAPolicyEvaluator(binary_path="missing-opa.exe").evaluate(
        {
            "risk_domain": "healthcare",
            "overall_confidence": 0.9,
            "axis_17_requires_human": False,
        }
    )

    assert result["backend"] == "python"
    assert result["allow"] is False
    assert "critical_domain_confidence_below_0_995" in result["violations"]


def test_provenance_record_exports_w3c_prov_json():
    class Run:
        run_id = "run-1"
        tier = "3"
        status = "pass"

    prov = ProvenanceRecord.from_trace_run(
        Run(),
        evidence_pack_hash="abc123",
        object_ref={"bucket": "audit-logs", "key": "run-1.json"},
    ).to_w3c_prov()

    assert "entity" in prov
    assert "activity" in prov
    assert "wasGeneratedBy" in prov
    assert prov["entity"]["trace_run:run-1"]["dle:evidence_pack_hash"] == "abc123"


def test_truthmemory_commit_stores_w3c_prov(app, monkeypatch):
    monkeypatch.setattr(TruthMemoryCommitService, "_write_audit_bundle_object", staticmethod(lambda run, bundle: {}))
    monkeypatch.setattr(TruthMemoryCommitService, "_anchor_merkle_root", staticmethod(lambda run, merkle_root: {}))

    with app.app_context():
        run = TraceRun(
            run_id=uuid.uuid4(),
            status="pass",
            tier="2",
            input_message="input",
            final_answer="answer",
            confidence=0.9,
            truthgate_decision="allow",
        )
        db.session.add(run)
        db.session.commit()

        TruthMemoryCommitService().commit(run, db.session)

        event = TruthAuditEvent.query.filter_by(event_type="audit_bundle_commit").first()
        assert event is not None
        assert event.event_data["w3c_prov"]["entity"]


def test_mcp_router_sampling_and_resource_subscription():
    router = MCPRouter()

    sampling_response = asyncio.run(
        router.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sampling/createMessage",
                "params": {
                    "messages": [
                        {"role": "user", "content": {"type": "text", "text": "Summarize the trace."}}
                    ]
                },
            }
        )
    )
    assert sampling_response["result"]["content"]["type"] == "text"

    subscribe_response = asyncio.run(
        router.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/subscribe",
                "params": {"uri": "dle://memory", "clientId": "client-1"},
            }
        )
    )
    assert subscribe_response["result"]["uri"] == "dle://memory"


def test_mcp_subscription_manager_sends_sse_event():
    manager = MCPSubscriptionManager()
    subscription = manager.subscribe("dle://resource", client_id="client-1")

    assert manager.notify("dle://resource", {"changed": True}) == 1
    assert manager.unsubscribe(subscription["subscription_id"]) is True


def test_sdk_v070_dsqp_and_coordinate_resolver_work_offline():
    sdk_path = "C:/software/DataLogicEngine/sdk/UKG_Python_SDK"
    if sdk_path not in sys.path:
        sys.path.insert(0, sdk_path)

    import ukg_sdk
    from ukg_sdk import CoordinateResolver17, DSQPClient

    assert ukg_sdk.__version__ == "0.7.0"
    coordinate = CoordinateResolver17().resolve("compliance audit risk").to_dict()
    persona = DSQPClient().construct("compliance audit risk", coordinate, axis_number=10)

    assert coordinate["axis_17"] == "high_stakes"
    assert persona["success"] is True
    assert persona["axis_number"] == 10
    assert persona["dsqp_chain"]
