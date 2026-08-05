from datetime import datetime, UTC

from backend.knowledge_algorithms.ka_36_complexity_estimator import (
    KA036ComplexityEstimator,
    KA036Input,
)
from backend.knowledge_algorithms.ka_master_controller import KAMasterController
from backend.truth_engine.truth_core.historical_embeddings import (
    cosine_similarity,
    parse_embedding,
    serialize_embedding,
    text_to_embedding,
)
from backend.truth_engine.truth_core.l9_schemas import L9Input
from backend.truth_engine.truth_core.meta_reasoning_controller import (
    MetaReasoningController,
)
from backend.truth_engine.truth_gate.l8_schemas import L8Input
from backend.truth_engine.truth_gate.trust_validation_gateway import (
    TrustValidationGateway,
)
from models import TruthSession


def test_l8_dynamic_threshold_uses_domain_history(monkeypatch):
    gateway = TrustValidationGateway()

    def fake_confidences(domain):
        return {
            "healthcare": [0.94, 0.95, 0.96],
            "standard": [0.84, 0.85, 0.86],
        }[domain]

    monkeypatch.setattr(gateway, "_trace_confidences_for_domain", fake_confidences)

    healthcare_threshold = gateway._get_threshold(
        L8Input(simulation_id="sim-1", risk_domain="healthcare")
    )
    standard_threshold = gateway._get_threshold(
        L8Input(simulation_id="sim-2", risk_domain="standard")
    )

    assert healthcare_threshold == 0.98
    assert standard_threshold == 0.88
    assert healthcare_threshold != standard_threshold


def test_truth_session_has_input_embedding_column():
    assert "input_embedding" in TruthSession.__table__.columns


def test_local_embedding_round_trip_similarity():
    query = "calibrate historical healthcare confidence"
    serialized = serialize_embedding(query)

    assert parse_embedding(serialized) == text_to_embedding(query)
    assert (
        cosine_similarity(text_to_embedding(query), parse_embedding(serialized)) == 1.0
    )


def test_l9_drift_report_includes_db_similar_sessions(monkeypatch):
    controller = MetaReasoningController()
    db_matches = [
        {
            "session_id": "historical-1",
            "similarity": 0.91,
            "confidence_score": 0.62,
            "tier": "high_stakes",
            "created_at": datetime.now(UTC).isoformat(),
        }
    ]
    monkeypatch.setattr(controller, "_search_audit_evidence", lambda *_: [])
    monkeypatch.setattr(
        controller, "_search_db_similar_sessions", lambda *_: db_matches
    )

    report = controller._detect_belief_drift(
        L9Input(
            simulation_id="sim-1",
            l8_gate_result={"quantum_summary": "healthcare answer"},
            problem_spec={"original_query": "healthcare answer"},
        ),
        [],
    )

    assert report.db_similar_sessions == db_matches
    assert report.drift_detected is True
    assert report.drift_type == "historical_baseline"


def test_ka_execution_timing_persistence(monkeypatch):
    added = []

    class FakeSession:
        def add(self, value):
            added.append(value)

        def commit(self):
            pass

        def rollback(self):
            raise AssertionError("rollback should not be called")

    controller = KAMasterController({})
    monkeypatch.setattr(controller, "_get_db_session", lambda: FakeSession())

    controller._record_ka_execution(
        "KA-036",
        {"problem": "x", "tenant_id": "tenant-a"},
        output_data={"success": True},
        elapsed_ms=12.4,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )

    assert len(added) == 1
    assert added[0].ka_id == "KA-036"
    assert added[0].status == "completed"
    assert added[0].execution_time_ms == 12
    assert added[0].tenant_id == "tenant-a"


def test_ka_036_uses_supplied_latency_without_hidden_history_read():
    result = KA036ComplexityEstimator({})._run_logic(
        KA036Input(
            problem="short",
            target_ka_id="KA-014",
            observed_latencies_ms=[100, 200, 300, 5000],
        )
    )

    assert result["signals"]["latency_sample_size"] == 4
    assert result["signals"]["p95_latency_ms"] == 5000
    assert result["complexity_score"] == 5
    assert result["database_read_performed"] is False
