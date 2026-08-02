"""Durable, bounded execution and restart reconciliation for simulations."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from backend.simulation.contracts import SimulationScenario
from backend.simulation.job_coordination import (
    RedisSimulationJobCoordinator,
    SimulationJobCoordinatorUnavailable,
)
from backend.simulation.multi_agent_engine import MultiAgentSimulationEngine
from backend.simulation.provider_adapter import BoundedSimulationProviderAdapter
from backend.simulation.providers import (
    FixedSeedSimulationTurnProvider,
    GatewaySimulationTurnProvider,
)
from backend.simulation.validation import validate_simulation_result

logger = logging.getLogger(__name__)


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class SimulationJobRunner:
    """Own the bounded worker pool and durable simulation lifecycle."""

    def __init__(self, app, *, max_workers: int = 2) -> None:
        self.app = app
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, min(8, int(max_workers))),
            thread_name_prefix="dle-simulation-job",
        )
        self._futures: dict[str, Future] = {}
        self._lock = Lock()
        self._stopping = False
        self._lease_seconds = max(
            60,
            min(3600, int(app.config.get("DLE_SIMULATION_JOB_LEASE_SECONDS", 600))),
        )
        self._coordinator = None
        if app.config.get("DLE_USE_REDIS") or app.config.get("DLE_PRODUCTION_MODE"):
            redis_url = app.config.get("DLE_REDIS_URL") or os.environ.get(
                "REDIS_URL", "redis://127.0.0.1:6379/0"
            )
            self._coordinator = RedisSimulationJobCoordinator.from_url(redis_url)

    def start(self) -> None:
        """Resume only work whose last provider call has a verified checkpoint."""
        from extensions import db
        from models import SimulationProviderCall, SimulationSession

        queued: list[str] = []
        with self.app.app_context():
            interrupted = SimulationSession.query.filter_by(status="running").all()
            for simulation in interrupted:
                uncheckpointed = SimulationProviderCall.query.filter(
                    SimulationProviderCall.session_id == simulation.session_id,
                    SimulationProviderCall.call_index > int(simulation.checkpoint_sequence or 0),
                ).first()
                if uncheckpointed is not None:
                    simulation.status = "failed"
                    simulation.last_error_code = "SIMULATION_INTERRUPTED_RETRY_UNSAFE"
                    simulation.last_error_message = (
                        "Execution stopped after provider admission but before a durable checkpoint."
                    )
                    simulation.completed_at = datetime.now(UTC)
                else:
                    simulation.status = "queued"
                    queued.append(simulation.session_id)
            queued.extend(
                simulation.session_id
                for simulation in SimulationSession.query.filter_by(status="queued").all()
                if simulation.session_id not in queued
            )
            db.session.commit()
        for simulation_id in queued:
            self.submit(simulation_id)

    def submit(self, simulation_id: str) -> None:
        normalized = str(uuid.UUID(str(simulation_id)))
        with self._lock:
            if self._stopping:
                raise RuntimeError("Simulation runner is stopping")
            existing = self._futures.get(normalized)
            if existing is not None and not existing.done():
                return
            if self._coordinator is not None:
                self._coordinator.enqueue(normalized)
            future = self._executor.submit(self._run, normalized)
            self._futures[normalized] = future
            future.add_done_callback(lambda _future: self._forget(normalized))

    def _forget(self, simulation_id: str) -> None:
        with self._lock:
            self._futures.pop(simulation_id, None)

    def _run(self, simulation_id: str) -> None:
        worker_id = str(uuid.uuid4())
        if self._coordinator is not None and not self._coordinator.acquire(
            simulation_id,
            worker_id=worker_id,
            lease_seconds=self._lease_seconds,
        ):
            return
        try:
            with self.app.app_context():
                self._execute(simulation_id)
        except Exception:
            logger.exception("Durable simulation execution failed")
            self._mark_failed(simulation_id, "SIMULATION_INTERNAL_ERROR")
        finally:
            if self._coordinator is not None:
                try:
                    self._coordinator.release(simulation_id, worker_id=worker_id)
                except SimulationJobCoordinatorUnavailable:
                    logger.error("Simulation coordination lease release failed")

    def run_now(self, simulation_id: str) -> None:
        """Execute synchronously for deterministic qualification and tests."""
        with self.app.app_context():
            self._execute(str(simulation_id))

    def _execute(self, simulation_id: str) -> None:
        from extensions import db
        from models import (
            SimulationCheckpoint,
            SimulationEventRecord,
            SimulationProviderCall,
            SimulationSession,
            SimulationStep,
        )

        simulation = SimulationSession.query.filter_by(session_id=simulation_id).one_or_none()
        if simulation is None or simulation.status != "queued":
            return
        scenario = SimulationScenario.model_validate(simulation.parameters or {})
        admission = self._admit_scenario(simulation, scenario)
        if not admission["ok"]:
            simulation.status = "failed"
            simulation.last_error_code = "SIMULATION_GOVERNANCE_BLOCK"
            simulation.last_error_message = str(admission["error"] or "Simulation blocked")[:500]
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "failed")
            return
        from backend.governed_execution.extended_subsystems import (
            ExtendedSubsystemCoordinator,
        )
        from backend.governed_execution.knowledge_lifecycle import (
            KnowledgeLifecycleError,
        )

        subsystem = ExtendedSubsystemCoordinator()
        try:
            ka_planning = subsystem.plan_simulation(
                simulation_id=simulation_id,
                principal_id=str(simulation.user_id),
                scenario=scenario,
            )
            plan_allowed, plan_blockers = subsystem.simulation_plan_allowed(
                ka_planning,
                scenario=scenario,
            )
        except KnowledgeLifecycleError:
            logger.exception("Simulation KA planning failed")
            ka_planning = None
            plan_allowed = False
            plan_blockers = ["ka_planning_failed"]
        if not plan_allowed:
            simulation.status = "failed"
            simulation.last_error_code = "SIMULATION_KA_ADMISSION_BLOCK"
            simulation.last_error_message = (
                "Simulation blocked by canonical KA planning."
            )
            simulation.budget = {
                **dict(simulation.budget or {}),
                "ka_planning": (
                    ka_planning.to_dict()
                    if ka_planning is not None
                    else None
                ),
                "ka_plan_blockers": plan_blockers,
            }
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "failed")
            return
        try:
            ka_counterfactual = subsystem.plan_simulation_counterfactual(
                simulation_id=simulation_id,
                principal_id=str(simulation.user_id),
                scenario=scenario,
            )
            counterfactual_context = subsystem.simulation_counterfactual_context(
                ka_counterfactual
            )
        except KnowledgeLifecycleError:
            logger.exception("Simulation counterfactual planning failed")
            simulation.status = "failed"
            simulation.last_error_code = "SIMULATION_KA_COUNTERFACTUAL_BLOCK"
            simulation.last_error_message = (
                "Simulation blocked by canonical counterfactual planning."
            )
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "failed")
            return
        resource_limits = subsystem.simulation_resource_limits(
            ka_planning,
            scenario=scenario,
        )
        simulation.status = "running"
        simulation.trace_id = simulation.trace_id or simulation.session_id
        simulation.started_at = simulation.started_at or datetime.now(UTC)
        simulation.completed_at = None
        simulation.last_error_code = None
        simulation.last_error_message = None
        planning_effect_receipt = subsystem.bind_effect_receipt(
            service="SimulationJobRunner",
            operation="admit_simulation_plan",
            resource_id=simulation_id,
            request_payload=scenario.plan.to_dict(),
            result_payload={
                "status": "running",
                "resource_limits": resource_limits,
            },
            idempotency_key=(
                f"simulation:{simulation_id}:"
                f"{simulation.scenario_revision}:admission"
            ),
            ka_execution=ka_planning,
            proposal_ids=[f"{simulation_id}:plan"],
        )
        simulation.budget = {
            **dict(simulation.budget or {}),
            "ka_planning": ka_planning.to_dict(),
            "ka_counterfactual": ka_counterfactual.to_dict(),
            "ka_resource_limits": resource_limits,
            "effect_receipts": [
                planning_effect_receipt.to_dict(),
            ],
        }
        admission_event_sequence = (
            db.session.query(db.func.max(SimulationEventRecord.sequence))
            .filter_by(session_id=simulation_id)
            .scalar()
            or 0
        ) + 1
        db.session.add(
            SimulationEventRecord(
                session_id=simulation_id,
                sequence=admission_event_sequence,
                event_type="policy.admitted",
                status="running",
                progress_current=int(simulation.current_step or 0),
                progress_total=scenario.plan.max_provider_calls,
                details={"governance_flags": admission["flags"]},
            )
        )
        db.session.commit()
        self._publish(simulation, "running")

        checkpoint = (
            SimulationCheckpoint.query.filter_by(session_id=simulation_id)
            .order_by(SimulationCheckpoint.sequence.desc())
            .first()
        )
        resume_state = dict(checkpoint.state or {}) if checkpoint is not None else None
        previous_calls = int(simulation.checkpoint_sequence or 0)
        aggregate = (
            db.session.query(
                db.func.coalesce(db.func.sum(SimulationProviderCall.tokens_in), 0),
                db.func.coalesce(db.func.sum(SimulationProviderCall.tokens_out), 0),
                db.func.coalesce(
                    db.func.sum(SimulationProviderCall.estimated_cost_usd),
                    0,
                ),
            )
            .filter_by(session_id=simulation_id, status="completed")
            .one()
        )
        retrieved_evidence = self._retrieve_evidence(
            simulation,
            scenario,
            query=str(admission["query"]),
        )
        provider = self._provider_for(
            scenario,
            allowed_provider_types=admission["allowed_provider_types"],
            allowed_models=admission["allowed_models"],
        )
        provider_budget = self._preflight_provider_budget(provider, scenario)
        if not provider_budget["ok"]:
            self._close_provider(provider)
            simulation.status = "failed"
            simulation.last_error_code = str(provider_budget["code"])
            simulation.last_error_message = str(provider_budget["message"])[:500]
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "failed")
            return
        simulation.budget = {
            **dict(simulation.budget or {}),
            "estimated_cost_usd": provider_budget["estimated_cost_usd"],
            "pricing_status": provider_budget["pricing_status"],
            "provider": getattr(provider, "provider_type", None),
            "model": getattr(provider, "model", None),
        }
        db.session.commit()

        def control_requested(action: str) -> bool:
            db.session.expire(simulation)
            requested = (
                simulation.cancellation_requested_at is not None
                if action == "cancel"
                else simulation.pause_requested_at is not None
            )
            if requested:
                return True
            if self._coordinator is None:
                return False
            return self._coordinator.requested_control(simulation_id) == action

        def on_call_event(payload: dict[str, Any]) -> None:
            call_index = int(payload["call_index"])
            call = SimulationProviderCall.query.filter_by(
                session_id=simulation_id,
                call_index=call_index,
                attempt_number=simulation.revision,
            ).one_or_none()
            if payload["event"] == "started":
                if call is not None:
                    raise RuntimeError("SIMULATION_PROVIDER_CALL_REPLAY_BLOCKED")
                step = SimulationStep.query.filter_by(
                    session_id=simulation_id,
                    sequence=call_index,
                    attempt_number=simulation.revision,
                ).one_or_none()
                if step is None:
                    step = SimulationStep(
                        session_id=simulation_id,
                        step_key=self._step_key(scenario, call_index),
                        sequence=call_index,
                        attempt_number=simulation.revision,
                        status="running",
                        input_hash=str(simulation.scenario_revision),
                        started_at=datetime.now(UTC),
                    )
                    db.session.add(step)
                    db.session.flush()
                call = SimulationProviderCall(
                    session_id=simulation_id,
                    step_id=step.id,
                    call_index=call_index,
                    attempt_number=simulation.revision,
                    purpose=step.step_key,
                    persona_id=str(payload.get("persona") or "")[:64] or None,
                    provider_type=str(payload.get("provider_type") or "unknown")[:32],
                    model=str(payload.get("model") or "unknown")[:128],
                    status="running",
                    disclosed_categories=[
                        "user_prompt",
                        *(["scenario_context"] if scenario.context else []),
                        *(["participant_configuration"] if scenario.participants else []),
                        *(["retrieved_text"] if retrieved_evidence else []),
                        *(["prior_provider_output"] if call_index > 1 else []),
                    ],
                )
                db.session.add(call)
            elif call is not None:
                call.status = "completed" if payload["event"] == "completed" else "failed"
                call.provider_type = str(payload.get("provider_type") or call.provider_type)[:32]
                call.model = str(payload.get("model") or call.model)[:128]
                call.tokens_in = int(payload.get("tokens_in") or 0)
                call.tokens_out = int(payload.get("tokens_out") or 0)
                call.estimated_cost_usd = payload.get("estimated_cost_usd")
                call.pricing_status = str(payload.get("pricing_status") or "unknown")[:32]
                call.latency_ms = int(payload.get("latency_ms") or 0)
                call.error_code = str(payload.get("error_code") or "")[:100] or None
                call.completed_at = datetime.now(UTC)
            db.session.commit()

        def persist_checkpoint(step_key: str, state: dict[str, Any]) -> None:
            sequence = self._step_sequence(scenario, step_key)
            state_hash = _sha256_json(state)
            step = SimulationStep.query.filter_by(
                session_id=simulation_id,
                sequence=sequence,
                attempt_number=simulation.revision,
            ).one()
            step.status = "completed"
            step.output_hash = state_hash
            step.output_summary = step_key
            step.validation = {"status": "checkpointed"}
            step.completed_at = datetime.now(UTC)
            checkpoint_record = SimulationCheckpoint.query.filter_by(
                session_id=simulation_id,
                sequence=sequence,
            ).one_or_none()
            if checkpoint_record is None:
                checkpoint_record = SimulationCheckpoint(
                    session_id=simulation_id,
                    sequence=sequence,
                    step_key=step_key,
                    state_hash=state_hash,
                    state=state,
                )
                db.session.add(checkpoint_record)
            simulation.current_step = sequence
            simulation.checkpoint_sequence = sequence
            event_sequence = (
                db.session.query(db.func.max(SimulationEventRecord.sequence))
                .filter_by(session_id=simulation_id)
                .scalar()
                or 0
            ) + 1
            db.session.add(
                SimulationEventRecord(
                    session_id=simulation_id,
                    sequence=event_sequence,
                    event_type="step.completed",
                    status="running",
                    step_key=step_key,
                    progress_current=sequence,
                    progress_total=scenario.plan.max_provider_calls,
                    details={"checkpoint_hash": state_hash},
                )
            )
            db.session.commit()
            self._publish(simulation, "running", step_key=step_key)

        adapter = BoundedSimulationProviderAdapter(
            provider=provider,
            simulation_id=simulation_id,
            max_provider_calls=scenario.plan.max_provider_calls,
            max_total_tokens=resource_limits["max_total_tokens"],
            max_cost_usd=scenario.max_cost_usd,
            initial_provider_calls=previous_calls,
            initial_tokens_in=int(aggregate[0] or 0),
            initial_tokens_out=int(aggregate[1] or 0),
            initial_estimated_cost_usd=float(aggregate[2] or 0),
            initial_pricing_status=(
                "unknown"
                if SimulationProviderCall.query.filter_by(
                    session_id=simulation_id,
                    status="completed",
                    pricing_status="unknown",
                ).first()
                else "available"
            ),
            deadline_monotonic=time.monotonic() + scenario.timeout_seconds,
            is_cancel_requested=lambda: control_requested("cancel"),
            is_pause_requested=lambda: control_requested("pause"),
            on_call_event=on_call_event,
        )
        engine = MultiAgentSimulationEngine(llm_gateway=adapter)
        execution_context = dict(scenario.context)
        execution_context["_simulation_participants"] = [
            participant.model_dump(mode="json")
            for participant in scenario.participants
        ]
        execution_context["_simulation_evidence"] = [
            {
                "source_uid": item["source_uid"],
                "citation_label": item["citation_label"],
                "text": item["text"],
                "content_hash": item["content_hash"],
            }
            for item in retrieved_evidence
        ]
        execution_context["_ka_counterfactual"] = {
            key: value
            for key, value in counterfactual_context.items()
            if key != "ka_lifecycle"
        }
        engine.create_simulation(
            str(admission["query"]),
            execution_context,
            simulation_id=simulation_id,
        )
        counterfactual_effect_receipt = subsystem.bind_effect_receipt(
            service="SimulationJobRunner",
            operation="apply_counterfactual_context",
            resource_id=simulation_id,
            request_payload={
                "scenario_revision": simulation.scenario_revision,
            },
            result_payload=counterfactual_context,
            idempotency_key=(
                f"simulation:{simulation_id}:"
                f"{simulation.scenario_revision}:counterfactual"
            ),
            ka_execution=ka_counterfactual,
            proposal_ids=[f"{simulation_id}:counterfactual"],
        )
        simulation.budget = {
            **dict(simulation.budget or {}),
            "effect_receipts": [
                planning_effect_receipt.to_dict(),
                counterfactual_effect_receipt.to_dict(),
            ],
        }
        db.session.commit()
        result = asyncio.run(
            engine.run_simulation(
                simulation_id,
                depth=scenario.depth.value,
                timeout=scenario.timeout_seconds,
                resume_state=resume_state,
                checkpoint_callback=persist_checkpoint,
                plan=scenario.plan,
            )
        )
        self._close_provider(provider)

        error = str((result.get("metadata") or {}).get("error") or "")
        if error == "SIMULATION_PAUSED":
            simulation.status = "paused"
            simulation.pause_requested_at = None
            db.session.commit()
            self._publish(simulation, "paused")
            return
        if error == "SIMULATION_CANCELLED":
            simulation.status = "cancelled"
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "cancelled")
            return
        if result.get("status") != "completed":
            simulation.status = "failed"
            simulation.last_error_code = error[:100] or "SIMULATION_EXECUTION_FAILED"
            simulation.last_error_message = "Simulation execution failed at a bounded step."
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "failed")
            return

        output_validation = self._validate_result_output(
            simulation,
            result,
            retrieved_evidence,
        )
        if not output_validation["ok"]:
            simulation.status = "failed"
            simulation.last_error_code = "SIMULATION_OUTPUT_VALIDATION_FAILED"
            simulation.last_error_message = "Simulation output failed policy or evidence validation."
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "failed")
            return
        result["final_conclusion"] = output_validation["answer"]
        evidence = self._persist_evidence(
            simulation,
            scenario,
            retrieved_evidence,
            conclusion=str(result.get("final_conclusion") or ""),
        )
        validation = validate_simulation_result(
            scenario=scenario,
            result=result,
            evidence=evidence,
        )
        result["validation"] = validation
        result["confidence_score"] = validation["confidence_score"]
        ka_outcome = subsystem.plan_simulation_outcome(
            simulation_id=simulation_id,
            principal_id=str(simulation.user_id),
            status="completed",
            summary=str(result.get("final_conclusion") or ""),
            significance=float(result.get("confidence_score") or 0),
        )
        artifact_refs = self._persist_artifacts(simulation, result)
        artifact_receipt = subsystem.bind_effect_receipt(
            service="SimulationJobRunner",
            operation="persist_simulation_artifacts",
            resource_id=simulation_id,
            request_payload={
                "scenario_revision": simulation.scenario_revision,
                "expected_artifacts": [
                    item.type for item in scenario.expected_artifacts
                ],
            },
            result_payload=artifact_refs,
            idempotency_key=(
                f"simulation:{simulation_id}:"
                f"{simulation.scenario_revision}:artifacts"
            ),
            ka_execution=ka_outcome,
            proposal_ids=[f"{simulation_id}:result"],
        )
        simulation.provider_call_count = int(result["budget"]["provider_calls_used"])
        simulation.results = {
            "status": "completed",
            "final_conclusion": result["final_conclusion"],
            "confidence_score": result["confidence_score"],
            "validation": validation,
            "budget": result["budget"],
            "artifacts": artifact_refs,
            "ka_outcome": ka_outcome.to_dict(),
            "effect_receipts": [
                planning_effect_receipt.to_dict(),
                counterfactual_effect_receipt.to_dict(),
                artifact_receipt.to_dict(),
            ],
        }
        simulation.artifact_state = (
            "ready"
            if all(item["state"] == "ready" for item in artifact_refs)
            else "materialization_pending"
        )
        simulation.status = (
            "completed" if simulation.artifact_state == "ready" else "materialization_pending"
        )
        simulation.completed_at = datetime.now(UTC)
        db.session.commit()
        if scenario.execution_mode == "live" and validation["status"] == "measured":
            self._queue_optional_indexes(simulation)
        self._publish(simulation, simulation.status)

    def _admit_scenario(
        self,
        simulation,
        scenario: SimulationScenario,
    ) -> dict[str, Any]:
        from backend.governed_execution.contracts import GovernedMode, GovernedRequest
        from backend.llm_gateway.governance import AIGovernanceEngine
        from extensions import db

        request = GovernedRequest(
            messages=[{"role": "user", "content": scenario.query}],
            mode=GovernedMode.SIMULATION,
            source="simulation_worker",
            principal_kind="desktop",
            principal_id=str(simulation.user_id),
            user_id=int(simulation.user_id),
            session_id=simulation.session_id,
            provider=scenario.provider,
            model=scenario.model,
            constraints={
                "max_provider_calls": scenario.plan.max_provider_calls,
                "max_total_tokens": scenario.max_total_tokens,
            },
            metadata={"token_budget": scenario.max_total_tokens},
            max_tokens=scenario.plan.max_tokens_per_call,
        )
        governance_input = scenario.query
        if scenario.context:
            governance_input = (
                f"{scenario.query}\n\nScenario context:\n"
                + json.dumps(scenario.context, sort_keys=True, default=str)
            )
        decision = AIGovernanceEngine(db.session).prepare_request(
            request,
            governance_input,
        )
        return {
            "ok": decision.ok,
            "query": scenario.query,
            "error": decision.error,
            "flags": list(decision.governance_flags),
            "allowed_provider_types": set(decision.allowed_provider_types),
            "allowed_models": set(decision.allowed_models),
        }

    def _provider_for(
        self,
        scenario: SimulationScenario,
        *,
        allowed_provider_types: set[str],
        allowed_models: set[str],
    ):
        factory = self.app.extensions.get("dle_simulation_provider_factory")
        if callable(factory):
            return factory(scenario)
        if scenario.execution_mode == "fixed_seed_local":
            return FixedSeedSimulationTurnProvider(seed=scenario.seed)
        from extensions import db

        return GatewaySimulationTurnProvider(
            db_session=db.session,
            preferred_provider=scenario.provider,
            model=scenario.model,
            allowed_provider_types=allowed_provider_types,
            allowed_models=allowed_models,
        )

    @staticmethod
    def _preflight_provider_budget(provider, scenario: SimulationScenario) -> dict[str, Any]:
        if scenario.execution_mode == "fixed_seed_local":
            estimate = 0.0
            pricing_status = "available"
        else:
            try:
                asyncio.run(provider.preflight())
            except Exception:
                return {
                    "ok": False,
                    "code": "SIMULATION_PROVIDER_UNAVAILABLE",
                    "message": "No approved simulation provider is available.",
                    "estimated_cost_usd": None,
                    "pricing_status": "unknown",
                }
            estimate = provider.estimate_max_cost_usd(scenario.max_total_tokens)
            pricing_status = str(provider.pricing_status)
        if scenario.max_cost_usd is not None and estimate is None:
            return {
                "ok": False,
                "code": "SIMULATION_COST_BUDGET_UNVERIFIABLE",
                "message": "The configured cost ceiling cannot be verified without approved pricing.",
                "estimated_cost_usd": None,
                "pricing_status": pricing_status,
            }
        if (
            scenario.max_cost_usd is not None
            and estimate is not None
            and estimate > scenario.max_cost_usd
        ):
            return {
                "ok": False,
                "code": "SIMULATION_COST_BUDGET_EXCEEDED",
                "message": "The preflight maximum cost exceeds the configured ceiling.",
                "estimated_cost_usd": estimate,
                "pricing_status": pricing_status,
            }
        return {
            "ok": True,
            "code": None,
            "message": None,
            "estimated_cost_usd": estimate,
            "pricing_status": pricing_status,
        }

    @staticmethod
    def _step_key(scenario: SimulationScenario, sequence: int) -> str:
        if sequence == 1:
            return "contextualize"
        if sequence == scenario.plan.max_provider_calls:
            return "synthesis"
        return f"debate_{sequence - 1}"

    @staticmethod
    def _step_sequence(scenario: SimulationScenario, step_key: str) -> int:
        if step_key == "contextualize":
            return 1
        if step_key == "synthesis":
            return scenario.plan.max_provider_calls
        return int(step_key.rsplit("_", 1)[1]) + 1

    def _retrieve_evidence(
        self,
        simulation,
        scenario: SimulationScenario,
        *,
        query: str,
    ) -> list[dict[str, Any]]:
        if not scenario.input_corpus or scenario.execution_mode != "live":
            return []
        from backend.governed_execution.contracts import GovernedMode, GovernedRequest
        from backend.governed_execution.retrieval import retrieve_evidence

        governed = GovernedRequest(
            messages=[{"role": "user", "content": query}],
            mode=GovernedMode.SIMULATION,
            source="simulation_worker",
            principal_kind="desktop",
            principal_id=str(simulation.user_id),
            user_id=int(simulation.user_id),
            session_id=simulation.session_id,
            constraints={
                "max_evidence_items": min(20, max(1, len(scenario.input_corpus) * 2)),
                "max_evidence_chars": min(
                    12_000,
                    max(1_000, scenario.max_total_tokens * 2),
                ),
            },
            metadata={"_trace_id": simulation.session_id},
        )
        evidence, warnings = retrieve_evidence(governed, query)
        requested = set(scenario.input_corpus)
        selected: list[dict[str, Any]] = []
        for item in evidence:
            document_uid = str(item.metadata.get("document_uid") or "")
            if document_uid not in requested and item.source_id not in requested:
                continue
            selected.append(
                {
                    "source_uid": document_uid or item.source_id,
                    "source_revision": str(
                        item.metadata.get("source_revision") or "unknown"
                    ),
                    "content_hash": str(item.content_hash or ""),
                    "citation_label": item.citation_label,
                    "text": item.text,
                    "warnings": list(warnings),
                }
            )
        return selected

    def _validate_result_output(
        self,
        simulation,
        result: dict[str, Any],
        retrieved: list[dict[str, Any]],
    ) -> dict[str, Any]:
        from backend.governed_execution.contracts import (
            EvidenceRecord,
            GovernedMode,
            SourceRecord,
        )
        from backend.governed_execution.validation import validate_output
        from backend.llm_gateway.governance import AIGovernanceEngine
        from extensions import db

        evidence: list[EvidenceRecord] = []
        for item in retrieved:
            record = EvidenceRecord(
                source_id=str(item["source_uid"]),
                citation_label=str(item["citation_label"]),
                text=str(item["text"]),
                source_type="ingested_document",
                content_hash=str(item["content_hash"]),
                metadata={"source_revision": item["source_revision"]},
                source=SourceRecord(
                    source_id=str(item["source_uid"]),
                    source_type="ingested_document",
                    content_hash=str(item["content_hash"]),
                ),
            )
            record.bind_to_trace(simulation.trace_id or simulation.session_id)
            evidence.append(record)
        validation = validate_output(
            str(result.get("final_conclusion") or ""),
            evidence,
            mode=GovernedMode.SIMULATION,
            governance_engine=AIGovernanceEngine(db.session),
        )
        supported_ids = {
            evidence_id
            for claim in validation.get("claims") or []
            if claim.status == "supported"
            for evidence_id in claim.evidence_ids
        }
        for item, record in zip(retrieved, evidence, strict=True):
            item["supported"] = record.evidence_id in supported_ids
        return {
            "ok": bool(validation["ok"]),
            "answer": str(validation["answer"]),
            "classification": validation["classification"],
            "warnings": list(validation["warnings"]),
        }

    def _persist_evidence(
        self,
        simulation,
        scenario: SimulationScenario,
        retrieved: list[dict[str, Any]],
        *,
        conclusion: str,
    ) -> list[dict[str, Any]]:
        from extensions import db
        from models import SimulationEvidenceRecord

        records: list[dict[str, Any]] = []
        by_uid = {str(item["source_uid"]): item for item in retrieved}
        for source_uid in scenario.input_corpus:
            source = by_uid.get(source_uid)
            citation_label = str((source or {}).get("citation_label") or "")
            state = (
                "verified"
                if source is not None
                and bool(source.get("supported"))
                and f"[{citation_label}]" in conclusion
                else ("uncited" if source is not None else "missing")
            )
            revision = str((source or {}).get("source_revision") or "missing")
            content_hash = str((source or {}).get("content_hash") or ("0" * 64))
            db.session.add(
                SimulationEvidenceRecord(
                    session_id=simulation.session_id,
                    evidence_type="retrieved_document",
                    source_uid=source_uid,
                    source_revision=revision[:64],
                    content_hash=content_hash[:64],
                    summary=citation_label or None,
                    validation_state=state,
                )
            )
            records.append(
                {
                    "source_uid": source_uid,
                    "source_revision": revision,
                    "content_hash": content_hash,
                    "validation_state": state,
                    "citation_label": citation_label or None,
                }
            )
        db.session.flush()
        return records

    def _persist_artifacts(self, simulation, result: dict[str, Any]) -> list[dict[str, Any]]:
        from backend.storage.artifact_materialization import persist_object_artifact
        from extensions import db
        from models import SimulationArtifact

        artifacts = {
            "transcript": {
                "schema_version": "simulation-transcript.v1",
                "events": result.get("events") or [],
                "simulation_id": simulation.session_id,
            },
            "result": {
                "schema_version": "simulation-result.v1",
                **{
                    key: value
                    for key, value in result.items()
                    if key != "events"
                },
            },
        }
        references: list[dict[str, Any]] = []
        for artifact_type, body in artifacts.items():
            encoded = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
            revision = hashlib.sha256(encoded).hexdigest()
            key = f"simulations/{simulation.session_id}/{revision}/{artifact_type}.json"
            reference = persist_object_artifact(
                entity_type="simulation_artifact",
                entity_id=f"{simulation.session_id}:{artifact_type}",
                bucket="simulation-artifacts",
                key=key,
                body=body,
                schema_version=str(body.get("schema_version") or "simulation-result.v1"),
                content_type="application/json",
                metadata={
                    "simulation_id": simulation.session_id,
                    "artifact_type": artifact_type,
                },
                commit=False,
            )
            db.session.add(
                SimulationArtifact(
                    session_id=simulation.session_id,
                    artifact_type=artifact_type,
                    schema_version=str(body.get("schema_version") or "simulation-result.v1"),
                    revision=revision,
                    object_key=key,
                    sha256=revision,
                    size_bytes=len(encoded),
                    state=reference["status"],
                    metadata_json={"bucket": reference["bucket"]},
                    verified_at=(datetime.now(UTC) if reference["status"] == "ready" else None),
                )
            )
            references.append(
                {
                    "type": artifact_type,
                    "bucket": reference["bucket"],
                    "key": key,
                    "sha256": revision,
                    "state": reference["status"],
                }
            )
        db.session.flush()
        return references

    def _queue_optional_indexes(self, simulation) -> None:
        from backend.storage.outbox import CrossStoreOutbox
        from extensions import db

        conclusion = str((simulation.results or {}).get("final_conclusion") or "")
        revision = f"sha256:{hashlib.sha256(conclusion.encode('utf-8')).hexdigest()}"
        outbox = CrossStoreOutbox(db.session)
        common = {
            "node_uid": f"simulation:{simulation.session_id}",
            "node_type": "simulation_result",
            "content": conclusion,
            "metadata": {
                "simulation_id": simulation.session_id,
                "scenario_revision": simulation.scenario_revision,
            },
        }
        outbox.enqueue(
            entity_type="simulation_result",
            entity_id=simulation.session_id,
            destination="chroma",
            operation="upsert_knowledge_node",
            schema_version="simulation-result-index.v1",
            source_revision=revision,
            payload=common,
            correlation_id=simulation.session_id,
        )
        outbox.enqueue(
            entity_type="simulation_result",
            entity_id=simulation.session_id,
            destination="neo4j",
            operation="merge_knowledge_node",
            schema_version="simulation-result-index.v1",
            source_revision=revision,
            payload={
                "node_uid": common["node_uid"],
                "properties": {
                    "label": "SimulationResult",
                    "simulation_id": simulation.session_id,
                    "scenario_revision": simulation.scenario_revision,
                },
            },
            correlation_id=simulation.session_id,
        )
        db.session.commit()

    def request_pause(self, simulation) -> None:
        simulation.pause_requested_at = datetime.now(UTC)
        if self._coordinator is not None:
            self._coordinator.request_control(simulation.session_id, "pause")

    def request_cancel(self, simulation) -> None:
        simulation.cancellation_requested_at = datetime.now(UTC)
        if self._coordinator is not None:
            self._coordinator.request_control(simulation.session_id, "cancel")

    def resume(self, simulation) -> None:
        from extensions import db

        simulation.pause_requested_at = None
        simulation.cancellation_requested_at = None
        simulation.status = "queued"
        if self._coordinator is not None:
            self._coordinator.clear_controls(simulation.session_id)
        db.session.commit()
        self.submit(simulation.session_id)

    def retry(self, simulation) -> None:
        from extensions import db
        from models import SimulationProviderCall

        uncheckpointed = SimulationProviderCall.query.filter(
            SimulationProviderCall.session_id == simulation.session_id,
            SimulationProviderCall.call_index > int(simulation.checkpoint_sequence or 0),
        ).first()
        if uncheckpointed is not None:
            raise ValueError("SIMULATION_RETRY_UNSAFE_AFTER_PROVIDER_ADMISSION")
        simulation.revision = int(simulation.revision or 1) + 1
        simulation.last_error_code = None
        simulation.last_error_message = None
        simulation.completed_at = None
        simulation.status = "queued"
        if self._coordinator is not None:
            self._coordinator.clear_controls(simulation.session_id)
        db.session.commit()
        self.submit(simulation.session_id)

    def reconcile_artifacts(self, simulation) -> None:
        """Promote a run only after required object writes are observed."""
        if simulation.artifact_state != "materialization_pending":
            return
        from extensions import db
        from models import (
            CrossStoreMaterializationState,
            SimulationArtifact,
        )

        artifacts = SimulationArtifact.query.filter_by(
            session_id=simulation.session_id
        ).all()
        for artifact in artifacts:
            if artifact.state == "ready":
                continue
            state = CrossStoreMaterializationState.query.filter_by(
                entity_type="simulation_artifact",
                entity_id=f"{simulation.session_id}:{artifact.artifact_type}",
                destination="minio",
            ).one_or_none()
            if state is not None and state.state == "succeeded":
                artifact.state = "ready"
                artifact.verified_at = state.completed_at or datetime.now(UTC)
        if artifacts and all(artifact.state == "ready" for artifact in artifacts):
            simulation.artifact_state = "ready"
            simulation.status = "completed"
            results = dict(simulation.results or {})
            results["status"] = "completed"
            for reference in results.get("artifacts") or []:
                reference["state"] = "ready"
            simulation.results = results
        db.session.commit()

    def live_state(self, simulation_id: str) -> dict[str, str] | None:
        return self._coordinator.get_state(simulation_id) if self._coordinator else None

    @staticmethod
    def _close_provider(provider) -> None:
        close = getattr(provider, "close", None)
        if callable(close):
            try:
                asyncio.run(close())
            except Exception:
                logger.warning("Simulation provider cleanup failed", exc_info=True)

    def _publish(self, simulation, state: str, *, step_key: str | None = None) -> None:
        current = int(simulation.current_step or 0)
        total = int((simulation.plan or {}).get("max_provider_calls") or 0)
        if self._coordinator is not None:
            self._coordinator.record_state(simulation.session_id, state, current, total)
        from backend.websocket import emit_simulation_complete, emit_simulation_progress

        payload = {
            "status": state,
            "current_step": current,
            "total_steps": total,
            "step_key": step_key,
        }
        if state in {"completed", "materialization_pending", "failed", "cancelled"}:
            emit_simulation_complete(simulation.session_id, simulation.results or payload)
        else:
            emit_simulation_progress(simulation.session_id, payload)

    def _mark_failed(self, simulation_id: str, code: str) -> None:
        from extensions import db
        from models import SimulationSession

        with self.app.app_context():
            simulation = SimulationSession.query.filter_by(session_id=simulation_id).one_or_none()
            if simulation is None or simulation.status in {"completed", "cancelled"}:
                return
            simulation.status = "failed"
            simulation.last_error_code = code
            simulation.last_error_message = "Simulation execution failed."
            simulation.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish(simulation, "failed")

    def stop(self) -> None:
        with self._lock:
            self._stopping = True
            futures = list(self._futures.values())
        for future in futures:
            future.cancel()
        self._executor.shutdown(wait=True, cancel_futures=True)


def get_simulation_job_runner(app) -> SimulationJobRunner:
    runner = app.extensions.get("dle_simulation_job_runner")
    if runner is None:
        runner = SimulationJobRunner(
            app,
            max_workers=int(app.config.get("DLE_SIMULATION_JOB_WORKERS", 2)),
        )
        app.extensions["dle_simulation_job_runner"] = runner
        runner.start()
    return runner
