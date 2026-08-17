import uuid

from extensions import db
from models import (
    TraceAxisVector,
    TraceEvidence,
    TraceKAInvocation,
    TracePersona,
    TraceRun,
    TraceStage,
    User,
)


def test_trace_bundle_endpoint_returns_aggregate_contract(app, authenticated_client):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        run_id = uuid.uuid4()
        run = TraceRun(
            run_id=run_id,
            user_id=user.id,
            status="running",
            input_message="Trace viewer contract test",
            final_answer="Contract answer",
            confidence=0.91,
            tier="2",
            latency_ms=125,
            model_name="gemini-3.7-flash",
            data_snapshot={"provider_used": "google"},
        )
        db.session.add(run)
        db.session.flush()
        db.session.add(
            TraceStage(
                run_id=run_id,
                name="L1 Context",
                stage_type="layer",
                layer_index=1,
                status="completed",
                duration_ms=12,
                metrics={"tokens_in": 4, "tokens_out": 8, "retrieval_count": 1},
                outputs={"summary": "context parsed"},
            )
        )
        db.session.add(
            TraceEvidence(
                run_id=run_id,
                source_type="knowledge_graph",
                source_id="kg-1",
                source_title="Fixture Evidence",
                authority="high",
                retrieval_method="ka-018",
                relevance_score=0.88,
                used_by_claims=["claim-1"],
                used_by_stages=["L2"],
            )
        )
        db.session.add(
            TracePersona(
                run_id=run_id,
                persona_type="knowledge",
                persona_name="Knowledge Expert",
                status="pass",
                draft_text="Persona position",
                confidence=0.82,
                objections=[{"detail": "Needs citation"}],
                consensus_impact={"synthesis_weight": 0.4, "final_position": "Final position"},
            )
        )
        db.session.add(
            TraceKAInvocation(
                run_id=run_id,
                ka_id="KA-018",
                ka_name="Source Provenance",
                status="completed",
                duration_ms=5,
            )
        )
        db.session.add(
            TraceAxisVector(
                run_id=run_id,
                axes={"1": {"name": "Pillar", "selected": True}},
                coordinate_hash="abc",
            )
        )
        db.session.commit()

    response = authenticated_client.get(f"/api/v1/trace/runs/{run_id}/bundle")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["run_id"] == str(run_id)
    assert payload["metrics"]["stage_count"] == 1
    assert payload["metrics"]["total_duration_ms"] == 125
    assert payload["run"]["provider_used"] == "google"
    assert payload["run"]["model_name"] == "gemini-3.7-flash"
    assert payload["frost_layers"][0]["name"] == "L1 Context"
    assert payload["evidence_sources"][0]["evidence_tier"] == "GOLD"
    assert payload["evidence_sources"][0]["claims_supported"] == ["claim-1"]
    assert payload["personas"][0]["synthesis_weight"] == 0.4
    assert payload["personas"][0]["flagged_conflicts"] == ["Needs citation"]
    assert payload["ka_invocations"][0]["ka_id"] == "KA-018"
    assert payload["coordinate"]["coordinate_hash"] == "abc"



def test_trace_runs_list_clamps_pagination_bounds(app, authenticated_client):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        for index in range(3):
            db.session.add(
                TraceRun(
                    run_id=uuid.uuid4(),
                    user_id=user.id,
                    status="pass",
                    input_message=f"Trace list pagination contract {index}",
                )
            )
        db.session.commit()

    response = authenticated_client.get("/api/v1/trace/runs?page=0&per_page=999")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["page"] == 1
    assert payload["per_page"] == 100
    assert payload["total"] >= 3
    assert len(payload["runs"]) >= 3
