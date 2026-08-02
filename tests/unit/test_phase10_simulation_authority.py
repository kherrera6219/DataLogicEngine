from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import uuid

import pytest

from backend.simulation.contracts import (
    SIMULATION_CONTRACT_VERSION,
    SimulationDepth,
    SimulationExpectedArtifact,
    SimulationParticipant,
    SimulationPlan,
    SimulationScenario,
)
from backend.simulation.multi_agent_engine import MultiAgentSimulationEngine
from backend.simulation.provider_adapter import BoundedSimulationProviderAdapter
from backend.simulation.providers import FixedSeedSimulationTurnProvider


class _TurnProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def generate_turn(self, **payload):
        self.calls.append(payload)
        return {
            "content": "Evidence-backed simulation observation.",
            "provider": "deterministic",
            "model": "fixture-v1",
            "tokens_in": 10,
            "tokens_out": 5,
            "estimated_cost_usd": 0.0,
        }


def test_depth_plan_declares_exact_maximum_provider_calls():
    assert SimulationPlan.for_depth(SimulationDepth.QUICK).max_provider_calls == 4
    assert SimulationPlan.for_depth(SimulationDepth.STANDARD).max_provider_calls == 5
    assert SimulationPlan.for_depth(SimulationDepth.DEEP).max_provider_calls == 7


def test_versioned_scenario_declares_participants_budget_and_artifacts():
    scenario = SimulationScenario(
        query="Evaluate a supply-chain disruption",
        depth=SimulationDepth.STANDARD,
        seed=42,
        participants=[
            SimulationParticipant(id="analyst", role="analysis"),
            SimulationParticipant(id="critic", role="challenge"),
        ],
        expected_artifacts=[
            SimulationExpectedArtifact(type="transcript", required=True),
            SimulationExpectedArtifact(type="result", required=True),
        ],
    )

    assert scenario.contract_version == SIMULATION_CONTRACT_VERSION
    assert scenario.plan.max_provider_calls == 5
    assert scenario.plan.max_output_tokens == 2_500
    assert scenario.plan.participants == ("analyst", "critic")
    assert [artifact.type for artifact in scenario.expected_artifacts] == [
        "transcript",
        "result",
    ]


def test_scenario_rejects_unbounded_query_and_duplicate_participants():
    with pytest.raises(ValueError):
        SimulationScenario(query="x" * 5_001)
    with pytest.raises(ValueError, match="participant_ids_must_be_unique"):
        SimulationScenario(
            query="valid",
            participants=[
                SimulationParticipant(id="same", role="analysis"),
                SimulationParticipant(id="same", role="challenge"),
            ],
        )
    with pytest.raises(ValueError, match="expected_artifacts_must_be_transcript_and_result"):
        SimulationScenario(
            query="valid",
            expected_artifacts=[SimulationExpectedArtifact(type="result")],
        )
    with pytest.raises(ValueError, match="simulation_context_exceeds_10000_bytes"):
        SimulationScenario(query="valid", context={"oversized": "x" * 10_000})


def test_custom_participants_and_context_reach_bounded_turn_prompts():
    provider = _TurnProvider()
    scenario = SimulationScenario(
        query="Evaluate the decision",
        context={"region": "Pacific Northwest"},
        depth=SimulationDepth.QUICK,
        participants=[
            SimulationParticipant(
                id="analyst",
                role="risk analysis",
                perspective="Prefer reversible mitigations",
            ),
            SimulationParticipant(id="critic", role="challenge assumptions"),
        ],
    )
    adapter = BoundedSimulationProviderAdapter(
        provider=provider,
        simulation_id="custom-scenario",
        max_provider_calls=scenario.plan.max_provider_calls,
        max_total_tokens=scenario.max_total_tokens,
    )
    engine = MultiAgentSimulationEngine(llm_gateway=adapter)
    context = dict(scenario.context)
    context["_simulation_participants"] = [
        participant.model_dump(mode="json")
        for participant in scenario.participants
    ]
    simulation_id = engine.create_simulation(
        scenario.query,
        context,
        simulation_id="custom-scenario",
    )

    result = asyncio.run(
        engine.run_simulation(
            simulation_id,
            depth=scenario.depth.value,
            plan=scenario.plan,
        )
    )

    assert result["status"] == "completed"
    assert result["metadata"]["plan"]["participants"] == ["analyst", "critic"]
    assert "Pacific Northwest" in str(provider.calls[0]["prompt"])
    assert provider.calls[1]["persona"] == "analyst"
    assert "risk analysis" in str(provider.calls[1]["prompt"])
    assert "Prefer reversible mitigations" in str(provider.calls[1]["prompt"])


def test_confidence_requires_retrieved_evidence_and_rendered_citations():
    from backend.simulation.validation import validate_simulation_result

    scenario = SimulationScenario(
        query="Evaluate this evidence",
        input_corpus=["document-1"],
    )
    result = {
        "final_conclusion": "Supported conclusion [S1]",
        "budget": {"provider_calls_used": 5},
        "events": [
            {"action": "ARGUE", "agent": participant}
            for participant in scenario.plan.participants
        ],
    }

    missing = validate_simulation_result(
        scenario=scenario,
        result=result,
        evidence=[{"source_uid": "document-1", "validation_state": "uncited"}],
    )
    measured = validate_simulation_result(
        scenario=scenario,
        result=result,
        evidence=[{"source_uid": "document-1", "validation_state": "verified"}],
    )

    assert missing["confidence_score"] is None
    assert missing["status"] == "insufficient_evidence"
    assert measured["confidence_score"] == 1.0
    assert measured["status"] == "measured"


def test_provider_adapter_enforces_hard_call_ceiling():
    provider = _TurnProvider()
    adapter = BoundedSimulationProviderAdapter(
        provider=provider,
        simulation_id="sim-budget",
        max_provider_calls=1,
        max_total_tokens=100,
    )

    async def exercise():
        await adapter.generate_simulation_turn(
            prompt="first", persona="analyst", max_tokens=20
        )
        with pytest.raises(RuntimeError, match="SIMULATION_PROVIDER_CALL_BUDGET_EXHAUSTED"):
            await adapter.generate_simulation_turn(
                prompt="second", persona="critic", max_tokens=20
            )

    asyncio.run(exercise())
    assert len(provider.calls) == 1


def test_provider_adapter_publishes_secret_free_attempt_events():
    provider = _TurnProvider()
    events = []
    adapter = BoundedSimulationProviderAdapter(
        provider=provider,
        simulation_id="sim-ledger",
        max_provider_calls=1,
        max_total_tokens=100,
        on_call_event=events.append,
    )

    asyncio.run(
        adapter.generate_simulation_turn(
            prompt="ledger", persona="analyst", max_tokens=20
        )
    )

    assert [event["event"] for event in events] == ["started", "completed"]
    assert events[-1]["provider_type"] == "deterministic"
    assert "prompt" not in events[-1]
    assert "content" not in events[-1]


def test_fixed_seed_provider_is_stable_across_session_ids():
    provider = FixedSeedSimulationTurnProvider(seed=42)

    first = asyncio.run(
        provider.generate_turn(
            prompt="same prompt",
            persona="analyst",
            max_tokens=20,
            simulation_id="session-a",
        )
    )
    second = asyncio.run(
        provider.generate_turn(
            prompt="same prompt",
            persona="analyst",
            max_tokens=20,
            simulation_id="session-b",
        )
    )

    assert first == second


def test_cost_ceiling_fails_closed_when_pricing_is_unavailable():
    from backend.simulation.jobs import SimulationJobRunner

    class _UnknownPricingProvider:
        pricing_status = "unknown"

        async def preflight(self):
            return None

        def estimate_max_cost_usd(self, _max_total_tokens):
            return None

    scenario = SimulationScenario(
        query="Cost bounded live run",
        max_cost_usd=1.0,
    )

    result = SimulationJobRunner._preflight_provider_budget(
        _UnknownPricingProvider(),
        scenario,
    )

    assert result["ok"] is False
    assert result["code"] == "SIMULATION_COST_BUDGET_UNVERIFIABLE"


def test_multi_agent_result_does_not_fabricate_confidence():
    provider = _TurnProvider()
    plan = SimulationPlan.for_depth(SimulationDepth.QUICK)
    adapter = BoundedSimulationProviderAdapter(
        provider=provider,
        simulation_id="sim-confidence",
        max_provider_calls=plan.max_provider_calls,
        max_total_tokens=2_000,
    )
    engine = MultiAgentSimulationEngine(llm_gateway=adapter)
    simulation_id = engine.create_simulation("Evaluate the scenario", {})

    result = asyncio.run(
        engine.run_simulation(simulation_id, depth=SimulationDepth.QUICK.value)
    )

    assert result["status"] == "completed"
    assert result["confidence_score"] is None
    assert result["validation"] == {
        "status": "not_measured",
        "validators": [],
    }
    assert result["budget"]["provider_calls_used"] == plan.max_provider_calls


def test_production_simulation_entry_points_do_not_import_legacy_engines():
    root = Path(__file__).resolve().parents[2]
    production_entry_points = (
        root / "backend" / "routes" / "simulation_routes.py",
        root / "backend" / "truth_engine" / "api.py",
        root / "core" / "simulation" / "app_orchestrator.py",
        root / "core" / "system" / "system_initializer.py",
        root / "core" / "orchestration" / "master_workflow.py",
    )
    forbidden = (
        "core.simulation.simulation_engine",
        "core.simulation.legacy_simulation_engine",
    )

    for path in production_entry_points:
        source = path.read_text(encoding="utf-8")
        assert all(name not in source for name in forbidden), path


def test_durable_simulation_authority_models_are_declared():
    from models import (
        SimulationArtifact,
        SimulationCheckpoint,
        SimulationEventRecord,
        SimulationEvidenceRecord,
        SimulationProviderCall,
        SimulationStep,
    )

    assert SimulationStep.__tablename__ == "simulation_steps"
    assert SimulationEventRecord.__tablename__ == "simulation_events"
    assert SimulationProviderCall.__tablename__ == "simulation_provider_calls"
    assert SimulationEvidenceRecord.__tablename__ == "simulation_evidence"
    assert SimulationCheckpoint.__tablename__ == "simulation_checkpoints"
    assert SimulationArtifact.__tablename__ == "simulation_artifacts"


def test_fixed_seed_job_persists_steps_calls_checkpoints_and_artifacts(app):
    from extensions import db
    from models import (
        SimulationArtifact,
        SimulationCheckpoint,
        SimulationEventRecord,
        SimulationProviderCall,
        SimulationSession,
        SimulationStep,
        User,
    )
    from backend.simulation.jobs import SimulationJobRunner

    with app.app_context():
        user = User(username="phase10", _email="phase10@local.ukg", active=True)
        db.session.add(user)
        db.session.flush()
        scenario = SimulationScenario(
            query="Qualify the durable simulation workflow",
            depth=SimulationDepth.QUICK,
            execution_mode="fixed_seed_local",
            seed=42,
        )
        scenario_payload = scenario.model_dump(mode="json")
        scenario_revision = hashlib.sha256(
            json.dumps(
                scenario_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        simulation = SimulationSession(
            session_id=str(uuid.uuid4()),
            user_id=user.id,
            parameters=scenario_payload,
            status="queued",
            current_step=0,
            total_steps=scenario.plan.max_provider_calls,
            results={},
            scenario_revision=scenario_revision,
            seed=scenario.seed,
            plan=scenario.plan.to_dict(),
            budget={"max_provider_calls": scenario.plan.max_provider_calls},
        )
        db.session.add(simulation)
        db.session.commit()
        simulation_id = simulation.session_id

    runner = SimulationJobRunner(app, max_workers=1)
    try:
        runner.run_now(simulation_id)
        with app.app_context():
            simulation = SimulationSession.query.filter_by(
                session_id=simulation_id
            ).one()
            assert simulation.status == "completed"
            assert simulation.provider_call_count == 4
            assert simulation.budget["ka_resource_limits"]["max_total_tokens"] < 10_000
            assert simulation.budget["ka_counterfactual"]["executed_ids"] == [
                "KA-042",
                "KA-070",
            ]
            assert simulation.results["confidence_score"] is None
            assert simulation.results["validation"]["status"] == "qualification_only"
            assert [
                receipt["operation"]
                for receipt in simulation.results["effect_receipts"]
            ] == [
                "admit_simulation_plan",
                "apply_counterfactual_context",
                "persist_simulation_artifacts",
            ]
            assert SimulationStep.query.filter_by(session_id=simulation_id).count() == 4
            assert (
                SimulationProviderCall.query.filter_by(
                    session_id=simulation_id,
                    status="completed",
                ).count()
                == 4
            )
            assert (
                SimulationCheckpoint.query.filter_by(session_id=simulation_id).count()
                == 4
            )
            assert SimulationArtifact.query.filter_by(session_id=simulation_id).count() == 2
            progress = SimulationEventRecord.query.filter_by(
                session_id=simulation_id,
                event_type="step.completed",
            ).order_by(SimulationEventRecord.sequence).all()
            assert [event.progress_current for event in progress] == [1, 2, 3, 4]
            assert all(event.progress_total == 4 for event in progress)
            artifacts = SimulationArtifact.query.filter_by(session_id=simulation_id).all()
            assert all(artifact.state == "ready" for artifact in artifacts)
            result_artifact = next(
                artifact
                for artifact in artifacts
                if artifact.artifact_type == "result"
            )
            from backend.storage import get_object_store

            stored_result = json.loads(
                get_object_store().get(
                    result_artifact.metadata_json["bucket"],
                    result_artifact.object_key,
                )
            )
            assert stored_result["schema_version"] == "simulation-result.v1"
    finally:
        runner.stop()


def test_pause_and_resume_continue_from_last_verified_checkpoint(app):
    from datetime import UTC, datetime

    from backend.simulation.jobs import SimulationJobRunner
    from extensions import db
    from models import (
        SimulationCheckpoint,
        SimulationProviderCall,
        SimulationSession,
        User,
    )

    class _PauseAfterFirstCall(_TurnProvider):
        async def generate_turn(self, **payload):
            result = await super().generate_turn(**payload)
            if len(self.calls) == 1:
                simulation = SimulationSession.query.filter_by(
                    session_id=payload["simulation_id"]
                ).one()
                simulation.pause_requested_at = datetime.now(UTC)
                db.session.commit()
            return result

    with app.app_context():
        user = User(username="phase10-pause", _email="pause@local.ukg", active=True)
        db.session.add(user)
        db.session.flush()
        scenario = SimulationScenario(
            query="Pause and resume the bounded workflow",
            depth=SimulationDepth.QUICK,
            execution_mode="fixed_seed_local",
        )
        simulation = SimulationSession(
            session_id=str(uuid.uuid4()),
            user_id=user.id,
            parameters=scenario.model_dump(mode="json"),
            status="queued",
            current_step=0,
            total_steps=4,
            results={},
            scenario_revision="a" * 64,
            plan=scenario.plan.to_dict(),
            budget={"max_provider_calls": 4},
        )
        db.session.add(simulation)
        db.session.commit()
        simulation_id = simulation.session_id

    provider = _PauseAfterFirstCall()
    app.extensions["dle_simulation_provider_factory"] = lambda _scenario: provider
    runner = SimulationJobRunner(app, max_workers=1)
    try:
        runner.run_now(simulation_id)
        with app.app_context():
            simulation = SimulationSession.query.filter_by(session_id=simulation_id).one()
            assert simulation.status == "paused"
            assert simulation.checkpoint_sequence == 1
            assert SimulationProviderCall.query.filter_by(session_id=simulation_id).count() == 1
            simulation.status = "queued"
            simulation.pause_requested_at = None
            db.session.commit()

        runner.run_now(simulation_id)
        with app.app_context():
            simulation = SimulationSession.query.filter_by(session_id=simulation_id).one()
            assert simulation.status == "completed"
            assert simulation.checkpoint_sequence == 4
            assert SimulationProviderCall.query.filter_by(session_id=simulation_id).count() == 4
            assert SimulationCheckpoint.query.filter_by(session_id=simulation_id).count() == 4
    finally:
        app.extensions.pop("dle_simulation_provider_factory", None)
        runner.stop()


def test_restart_marks_uncheckpointed_provider_admission_retry_unsafe(app):
    from backend.simulation.jobs import SimulationJobRunner
    from extensions import db
    from models import SimulationProviderCall, SimulationSession, User

    with app.app_context():
        user = User(username="phase10-restart", _email="restart@local.ukg", active=True)
        db.session.add(user)
        db.session.flush()
        scenario = SimulationScenario(
            query="Restart reconciliation",
            execution_mode="fixed_seed_local",
        )
        simulation = SimulationSession(
            session_id=str(uuid.uuid4()),
            user_id=user.id,
            parameters=scenario.model_dump(mode="json"),
            status="running",
            current_step=0,
            checkpoint_sequence=0,
            total_steps=5,
            results={},
            scenario_revision="b" * 64,
            plan=scenario.plan.to_dict(),
            budget={"max_provider_calls": 5},
        )
        db.session.add(simulation)
        db.session.flush()
        db.session.add(
            SimulationProviderCall(
                session_id=simulation.session_id,
                call_index=1,
                attempt_number=1,
                purpose="contextualize",
                provider_type="deterministic",
                model="fixed-seed-v1",
                status="running",
            )
        )
        db.session.commit()
        simulation_id = simulation.session_id

    runner = SimulationJobRunner(app, max_workers=1)
    try:
        runner.start()
        with app.app_context():
            simulation = SimulationSession.query.filter_by(session_id=simulation_id).one()
            assert simulation.status == "failed"
            assert simulation.last_error_code == "SIMULATION_INTERRUPTED_RETRY_UNSAFE"
    finally:
        runner.stop()
