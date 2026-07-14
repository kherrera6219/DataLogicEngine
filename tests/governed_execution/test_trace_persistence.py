import uuid

import pytest

from backend.llm_gateway.gateway import LLMGateway


@pytest.mark.asyncio
async def test_trace_transaction_persists_exact_stages_and_governance_artifacts(app):
    from extensions import db
    from models import (
        TraceClaim,
        TraceEvidence,
        TraceKAInvocation,
        TracePersona,
        TracePolicyDecision,
        TraceRun,
        TraceStage,
    )

    run_id = uuid.uuid4()
    admission_id = uuid.uuid4()
    persistence_id = uuid.uuid4()
    payload = {
        "contract_version": "governed.v1",
        "ok": True,
        "status": "completed",
        "answer": "Use the approved control [S1].",
        "provider_used": "openai",
        "model_used": "test-model",
        "confidence": 1.0,
        "usage": {"prompt_tokens": 2, "completion_tokens": 3},
        "latency_ms": 9,
        "trace": [
            {
                "stage_id": str(admission_id),
                "stage_name": "admission",
                "stage_type": "policy",
                "status": "completed",
                "start_time": "2026-07-13T20:00:00+00:00",
                "end_time": "2026-07-13T20:00:00.001000+00:00",
                "duration_ms": 1,
                "input": {"request_id": "request-1"},
                "output": {"decision": "allow"},
                "metrics": {},
            },
            {
                "stage_id": str(persistence_id),
                "stage_name": "persistence",
                "stage_type": "persistence",
                "status": "completed",
                "start_time": "2026-07-13T20:00:00.001000+00:00",
                "end_time": "2026-07-13T20:00:00.002000+00:00",
                "duration_ms": 1,
                "input": {"trace_id": str(run_id)},
                "output": {"trace_id": str(run_id)},
                "metrics": {},
            },
        ],
        "evidence": [
            {
                "source_id": "source-1",
                "citation_label": "S1",
                "text": "Approved control text",
                "source_type": "document",
                "title": "Control Manual",
                "score": 0.9,
                "content_hash": "abc123",
                "locator": {"page": 4},
                "metadata": {"retrieval_method": "vector", "authority": "high"},
            }
        ],
        "claims": [
            {
                "claim_id": "claim-1",
                "text": "Use the approved control [S1].",
                "evidence_ids": ["source-1"],
                "status": "supported",
                "confidence": 1.0,
            }
        ],
        "metadata": {
            "provider_call_count": 1,
            "source_ids": ["source-1"],
            "dmrf": {
                "run_id": "dmrf-1",
                "tier": "moderate",
                "query_digest": "digest",
                "axis_vector": {"axes": {"15": {"value": "standard"}}, "confidence": 0.5},
                "gate_result": {"decision": "allow"},
            },
            "dsqp": {
                "profiles": {
                    "8": {
                        "persona_id": "persona-8",
                        "axis_number": 8,
                        "persona_type": "knowledge",
                        "name": "Knowledge Expert",
                        "description": "Knowledge contribution",
                        "coverage_score": 1.0,
                        "components": {"skills": {"items": ["analysis"]}},
                        "metadata": {"construction_mode": "deterministic"},
                        "validation": {"valid": True, "errors": []},
                    }
                }
            },
            "truthcore": {
                "mode": "standard",
                "steps_executed": [
                    {
                        "step": "complexity_routing",
                        "ka_id": "KA-113",
                        "status": "completed",
                        "input": {"query": "Assess control"},
                        "output": {"route": "standard"},
                        "duration_ms": 2,
                    }
                ],
            },
            "policy_decisions": [
                {
                    "policy_id": "ai_governance_admission",
                    "decision": "allow",
                    "rationale": "fixture",
                    "stage": "admission",
                }
            ],
        },
    }

    with app.app_context():
        gateway = LLMGateway(db_session=db.session)
        persisted = await gateway._create_trace_run(
            payload,
            "Assess control",
            str(run_id),
            "anonymous",
            None,
            "test-model",
        )

        assert persisted is True
        run = db.session.get(TraceRun, run_id)
        stages = TraceStage.query.filter_by(run_id=run_id).order_by(TraceStage.layer_index).all()
        assert run.status == "completed"
        assert run.confidence == 1.0
        assert run.data_snapshot["governed_status"] == "completed"
        assert [(stage.stage_id, stage.name, stage.status) for stage in stages] == [
            (admission_id, "admission", "completed"),
            (persistence_id, "persistence", "completed"),
        ]
        assert stages[0].inputs == {"request_id": "request-1"}
        assert stages[1].end_time is not None
        assert TraceEvidence.query.filter_by(run_id=run_id).one().source_id == "source-1"
        assert TraceClaim.query.filter_by(run_id=run_id).one().evidence_ids == ["source-1"]
        assert TracePersona.query.filter_by(run_id=run_id).one().status == "completed"
        ka = TraceKAInvocation.query.filter_by(run_id=run_id).one()
        assert ka.ka_id == "KA-113"
        assert ka.inputs == {"query": "Assess control"}
        assert ka.outputs == {"route": "standard"}
        assert ka.duration_ms == 2
        decision = TracePolicyDecision.query.filter_by(run_id=run_id).one()
        assert decision.decision == "allow"
        assert decision.stage_id == admission_id

        payload["trace"][1]["output"] = {"trace_id": str(run_id), "idempotent": True}
        assert await gateway._create_trace_run(
            payload,
            "Assess control",
            str(run_id),
            "anonymous",
            None,
            "test-model",
        ) is True
        assert TraceStage.query.filter_by(run_id=run_id).count() == 2
        assert db.session.get(TraceStage, persistence_id).outputs["idempotent"] is True


@pytest.mark.asyncio
async def test_trace_preserves_long_failure_status_and_unmeasured_confidence(app):
    from extensions import db
    from models import TraceRun

    run_id = uuid.uuid4()
    payload = {
        "contract_version": "governed.v1",
        "ok": False,
        "status": "capability_unavailable",
        "answer": "",
        "failure": {
            "kind": "capability_unavailable",
            "code": "SIMULATION_PHASE10_BOUNDARY",
            "message": "Simulation is not connected",
            "stage": "simulation",
        },
        "trace": [],
        "evidence": [],
        "claims": [],
        "usage": {},
        "metadata": {"provider_call_count": 0},
    }

    with app.app_context():
        gateway = LLMGateway(db_session=db.session)
        assert await gateway._create_trace_run(
            payload,
            "Run a simulation",
            str(run_id),
            "anonymous",
            None,
            "unknown",
        ) is True

        run = db.session.get(TraceRun, run_id)
        assert run.status == "capability_unavailable"
        assert run.confidence is None
        assert run.data_snapshot["failure"]["code"] == "SIMULATION_PHASE10_BOUNDARY"
