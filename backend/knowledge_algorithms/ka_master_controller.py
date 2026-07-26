"""
KA-Master: Master Controller
Purpose: The top-level orchestrator that manages the entire lifecycle of all 116 Knowledge Algorithms, 
providing a unified interface for complex query resolution and system self-management.
"""
import logging
import os
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from celery import Celery
from pydantic import BaseModel

from backend.knowledge_algorithms.contracts import (
    KAExecutionContext,
    KAExecutionMode,
    KAExecutionRequest,
    KAExecutionResult,
)
from backend.knowledge_algorithms.controller import get_ka_controller
from backend.knowledge_algorithms.manifest import KADefinition, normalize_ka_id
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionReport,
    KAPlanExecutor,
    KASelectionPlan,
    KASelectionRequest,
    ManifestKASelector,
)
from core.knowledge_algorithm.exceptions import KAConfigError, KAError
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

# Initialize celery
celery_app = Celery('ka_tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

class KAMasterController(KnowledgeAlgorithm):
    """
    KA-Master: The supreme orchestrator and system state machine.
    """
    def __init__(self, context: dict[str, Any] | None = None):
        super().__init__(context or {}, None, None, None)
        self.ka_id = "KA-Master"
        self.llm_gateway = (context or {}).get("llm_gateway") if isinstance(context, dict) else None
        self._canonical_controller = get_ka_controller()
        self._selector = ManifestKASelector(
            self._canonical_controller.manifest
        )
        self.algorithms = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        """Expose a compatibility view generated from the canonical manifest."""
        try:
            return {
                definition.canonical_id: {
                    "id": definition.canonical_id,
                    "metadata": self._compatibility_metadata(definition),
                }
                for definition in self._canonical_controller.list_definitions()
            }
        except Exception as e:  # noqa: BLE001 - configuration boundary
            raise KAConfigError(f"Failed to load KA manifest: {e!s}")

    @staticmethod
    def _compatibility_metadata(definition: KADefinition) -> dict[str, Any]:
        entrypoint = definition.implementation.entrypoint
        implementation = (
            f"{entrypoint.module}.{entrypoint.callable}"
            if entrypoint and entrypoint.adapter == "module_run"
            else definition.implementation.source
        )
        trigger_set = set(definition.contract.triggers)
        return {
            "KA_ID": definition.canonical_id,
            "KA_Name": definition.name,
            "Purpose": definition.purpose,
            "Category": (
                definition.contract.categories[0]
                if definition.contract.categories
                else None
            ),
            "Primary_Layers": ",".join(definition.contract.layers),
            "Allowed_Layers": ",".join(definition.contract.layers),
            "Inputs": "; ".join(definition.contract.inputs),
            "Outputs": "; ".join(definition.contract.outputs),
            "Reads_Memory": "Yes" if definition.contract.reads_memory else "No",
            "Writes_Memory": "Yes" if definition.contract.writes_memory else "No",
            "Can_Invoke_Chaos": (
                "Yes" if "may_invoke_chaos" in trigger_set else "No"
            ),
            "Can_Invoke_External_Research": (
                "Yes"
                if "may_invoke_external_research" in trigger_set
                else "No"
            ),
            "Can_Trigger_Recursion": (
                "Yes" if "may_trigger_recursion" in trigger_set else "No"
            ),
            "Can_Veto": "Yes" if "may_veto" in trigger_set else "No",
            "Risk_Class": (
                definition.contract.risk_classes[0]
                if definition.contract.risk_classes
                else None
            ),
            "Dependencies": ",".join(definition.contract.dependencies),
            "Produces_Artifacts": (
                "Yes" if definition.contract.produces_artifacts else "No"
            ),
            "Audit_Events": "Yes" if definition.contract.audit_events else "No",
            "Version": definition.version,
            "Owner": definition.integration.primary_owner,
            "Primary_Owner": definition.integration.primary_owner,
            "Consumer_Paths": definition.integration.consumer_paths,
            "Integration_Stage": definition.integration.stage,
            "Required_Or_Optional": definition.integration.required_or_optional,
            "Selector_Policy": definition.integration.selector_policy,
            "Effect_Port": definition.integration.effect_port,
            "Design_Owners": definition.contract.subsystems,
            "Status": (
                "Active"
                if definition.implementation.entrypoint
                else "Implementation Required"
            ),
            "Implementation": implementation,
            "classification": definition.admission.classification,
            "production_enabled": definition.admission.production_enabled,
            "deterministic": definition.admission.deterministic,
            "guarantee": definition.contract.guarantee,
            "limitations": definition.contract.limitations,
            "performance_budget_ms": definition.contract.performance_budget_ms,
            "manifest_version": definition.contract.version,
            "effect_class": definition.contract.effect_class,
        }

    def get_available_algorithms(self) -> dict[str, Any]:
        return self.algorithms

    def plan_algorithms(
        self,
        request: KASelectionRequest | dict[str, Any],
    ) -> KASelectionPlan:
        """Build one manifest-driven plan without executing a KA."""
        return self._selector.plan(request)

    async def execute_algorithm_plan(
        self,
        plan: KASelectionPlan,
        request: KASelectionRequest | dict[str, Any],
    ) -> KAPlanExecutionReport:
        """Execute an admitted plan through the canonical controller."""
        return await KAPlanExecutor(self._canonical_controller).execute(
            plan,
            request,
        )

    def _normalize_ka_id(self, ka_id: str) -> str:
        try:
            return self._canonical_controller.manifest.resolve_id(str(ka_id))
        except KeyError:
            return normalize_ka_id(str(ka_id))

    def execute_algorithm(self, ka_id: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Return the versioned compatibility envelope for external legacy callers."""
        norm_id = self._normalize_ka_id(ka_id)
        is_async = input_data.get("async", False)
        
        self.log_execution_step("Dispatching Algorithm", {"ka_id": norm_id, "mode": "async" if is_async else "sync"})
        
        if norm_id not in self.algorithms:
            raise KAError(f"Algorithm {norm_id} not registered.", error_code="E404")
        metadata = self.algorithms[norm_id]["metadata"]
        if input_data.get("_production_workflow") and not metadata.get("production_enabled"):
            raise KAError(
                f"Algorithm {norm_id} is not enabled for production workflows.",
                error_code="E403",
                details={"classification": metadata.get("classification")},
            )
            
        if is_async:
            task = run_ka_task.delay(norm_id, input_data)
            return {"success": True, "ka_id": norm_id, "mode": "async", "task_id": task.id, "status": "PENDING"}

        result = self.execute_typed(
            norm_id,
            input_data,
            production_workflow=bool(input_data.get("_production_workflow")),
        )
        payload = result.model_dump(mode="json", exclude_none=True)
        return {
            "success": result.success,
            "ka_id": result.canonical_id,
            "output": result.output,
            "execution_time_ms": result.duration_ms,
            "trace_id": result.trace_id,
            "canonical_result": payload,
            **(
                {
                    "error": result.error.message,
                    "error_code": result.error.code.value,
                }
                if result.error
                else {}
            ),
        }

    def execute_typed(
        self,
        ka_id: str,
        input_data: dict[str, Any] | None = None,
        *,
        production_workflow: bool = False,
        context: KAExecutionContext | None = None,
    ) -> KAExecutionResult:
        """Execute one KA for internal callers using only the canonical typed result."""
        norm_id = self._normalize_ka_id(ka_id)
        if norm_id not in self.algorithms:
            raise KAError(
                f"Algorithm {norm_id} not registered.",
                error_code="E404",
            )

        payload = dict(input_data or {})
        payload.pop("async", None)
        production_workflow = bool(
            production_workflow or payload.pop("_production_workflow", False)
        )
        request = KAExecutionRequest(
            ka_id=norm_id,
            input=payload,
            context=context or KAExecutionContext(),
            mode=(
                KAExecutionMode.PRODUCTION
                if production_workflow
                else KAExecutionMode.EVALUATION
            ),
        )
        started_at = datetime.now(UTC)
        start_time = time.perf_counter()
        result = self._canonical_controller.execute(request)
        self._record_ka_execution(
            norm_id,
            payload,
            output_data=result.model_dump(mode="json", exclude_none=True),
            error=None if result.success else RuntimeError(
                result.error.message
                if result.error
                else "Knowledge Algorithm execution failed."
            ),
            elapsed_ms=(time.perf_counter() - start_time) * 1000,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )
        return result

    def _record_ka_execution(
        self,
        ka_id: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any] | None = None,
        error: Exception | None = None,
        elapsed_ms: float = 0.0,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Persist KA timing telemetry when the local database is available."""
        session = self._get_db_session()
        if session is None:
            return

        try:
            from models import KAExecution

            self._ensure_ka_catalog_entry(session, ka_id)
            execution = KAExecution(
                uid=str(uuid.uuid4()),
                ka_id=ka_id,
                status="failed" if error else "completed",
                input_data=self._json_safe(input_data),
                output_data=self._json_safe(output_data) if output_data is not None else None,
                error_message=str(error) if error else None,
                execution_time_ms=max(0, round(elapsed_ms)),
                tenant_id=(input_data or {}).get("tenant_id"),
                started_at=started_at or datetime.now(UTC),
                completed_at=completed_at or datetime.now(UTC),
            )
            session.add(execution)
            session.commit()
        except Exception as exc:  # noqa: BLE001 - optional persistence boundary
            try:
                session.rollback()
            except Exception as rollback_exc:  # noqa: BLE001
                logger.debug(
                    "KAExecution rollback skipped for %s: %s",
                    ka_id,
                    rollback_exc,
                )
            logger.debug(f"KAExecution timing persistence skipped for {ka_id}: {exc}")

    def _ensure_ka_catalog_entry(self, session, ka_id: str) -> None:
        """Ensure KAExecution foreign keys can resolve in local-first databases."""
        try:
            from models import KnowledgeAlgorithm

            exists = session.query(KnowledgeAlgorithm).filter_by(ka_id=ka_id).first()
            if exists:
                return
            session.add(KnowledgeAlgorithm(
                uid=f"ka-{ka_id.lower()}",
                ka_id=ka_id,
                name=ka_id,
                description="Auto-registered by KA execution telemetry.",
            ))
        except Exception:  # noqa: BLE001 - optional catalog persistence
            return

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): KAMasterController._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [KAMasterController._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [KAMasterController._json_safe(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    @staticmethod
    def _get_db_session():
        try:
            from extensions import db

            return db.session
        except Exception:  # noqa: BLE001 - optional Flask database binding
            return None

    def _run_logic(self, input_data: BaseModel) -> dict[str, Any]:
        """High-level query orchestration."""
        data = input_data.data if hasattr(input_data, "data") else {}
        query = data.get("query", "status_check")
        flow = self._select_flow(query, data)
        step_results = []
        for ka_id, payload in flow:
            try:
                result = self.execute_typed(ka_id, payload)
                step_results.append(
                    {
                        "ka_id": ka_id,
                        "success": result.success,
                        "result": result.model_dump(
                            mode="json",
                            exclude_none=True,
                        ),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - per-step failure isolation
                step_results.append(
                    {
                        "ka_id": ka_id,
                        "success": False,
                        "error": str(exc),
                    }
                )
        successful = [step for step in step_results if step["success"]]
        failed = [step for step in step_results if not step["success"]]
        system_state = "NOMINAL" if not failed else "DEGRADED"
        
        return {
            "success": bool(successful),
            "orchestrated_flow": [ka_id for ka_id, _payload in flow],
            "step_results": step_results,
            "system_state": system_state,
            "active_kas": len(self.algorithms),
            "final_conclusion": self._summarize_flow(query, successful, failed),
        }

    def _select_flow(self, query: str, data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        """Choose a bounded local KA chain for the current request."""
        query_text = str(query or "")
        lower = query_text.lower()
        flow: list[tuple[str, dict[str, Any]]] = [
            ("KA-004", {"query": query_text}),
            ("KA-005", {"query": query_text}),
        ]
        if any(term in lower for term in ("health", "status", "liveness", "readiness")):
            flow.append(("KA-109", {"check_mode": data.get("check_mode", "standard")}))
        elif any(term in lower for term in ("select pipeline", "algorithm selection", "choose ka", "ka pipeline")):
            flow.append(
                (
                    "KA-031",
                    {
                        "query": query_text,
                        "query_class": data.get("query_class", "GENERAL"),
                        "complexity_tier": data.get("complexity_tier", "standard"),
                        "policy_flags": data.get("policy_flags", []),
                        "budget": data.get("budget", {}),
                    },
                )
            )
        elif any(term in lower for term in ("orchestrate", "execution schedule", "simulate pipeline", "checkpoint")):
            flow.append(
                (
                    "KA-032",
                    {
                        "pipeline": data.get("pipeline", []),
                        "simulation_state": data.get("simulation_state", {}),
                        "exit_criteria": data.get("exit_criteria", {}),
                    },
                )
            )
        elif any(term in lower for term in ("adversarial", "attack assumption", "stress test", "robustness")):
            flow.append(
                (
                    "KA-034",
                    {
                        "scenario": data.get("scenario", query_text),
                        "assumptions": data.get("assumptions", []),
                        "evidence": data.get("evidence", []),
                    },
                )
            )
        elif any(term in lower for term in ("impute", "gap", "missing value", "bayesian gap")):
            flow.append(
                (
                    "KA-035",
                    {
                        "gaps": data.get("gaps", []),
                        "priors": data.get("priors", {}),
                        "observations": data.get("observations", {}),
                        "evidence_weights": data.get("evidence_weights", {}),
                    },
                )
            )
        elif any(term in lower for term in ("hypothesis", "hypotheses", "possible cause")):
            flow.append(
                (
                    "KA-040",
                    {
                        "observation": data.get("observation", query_text),
                        "context": data.get("context", {}),
                        "variables": data.get("variables", []),
                    },
                )
            )
        elif any(term in lower for term in ("causal graph", "causal inference engine", "causal relationship")):
            flow.append(
                (
                    "KA-066",
                    {
                        "events": data.get("events", []),
                        "dependencies": data.get("dependencies", []),
                        "confounders": data.get("confounders", []),
                    },
                )
            )
        elif any(term in lower for term in ("relation", "relationship", "predicate")):
            flow.append(("KA-049", {"text": data.get("text", query_text), "entities": data.get("entities", [])}))
        elif any(term in lower for term in ("cache", "evict", "ttl")):
            flow.append(
                (
                    "KA-080",
                    {
                        "key": data.get("key", "*"),
                        "operation": data.get("operation", "stats"),
                        "cache_state": data.get("cache_state", {}),
                    },
                )
            )
        elif any(term in lower for term in ("train model", "model training", "training job")):
            flow.append(
                (
                    "KA-081",
                    {
                        "dataset_id": data.get("dataset_id", "ds_default"),
                        "model_name": data.get("model_name", "local_model"),
                        "training_samples": data.get("training_samples"),
                        "hyperparameters": data.get("hyperparameters", {}),
                    },
                )
            )
        elif any(term in lower for term in ("evaluate model", "model evaluation", "performance metrics")):
            flow.append(
                (
                    "KA-082",
                    {
                        "model_id": data.get("model_id", "latest"),
                        "test_set": data.get("test_set", "eval_v1"),
                        "predictions": data.get("predictions", []),
                        "labels": data.get("labels", []),
                    },
                )
            )
        elif any(term in lower for term in ("deploy model", "model deployment", "canary")):
            flow.append(
                (
                    "KA-083",
                    {
                        "version": data.get("version", "v1.0.0"),
                        "env": data.get("env", "staging"),
                        "health_signals": data.get("health_signals", {}),
                        "current_version": data.get("current_version"),
                    },
                )
            )
        elif any(term in lower for term in ("hyperparameter", "tune model", "parameter search")):
            flow.append(
                (
                    "KA-086",
                    {
                        "model_type": data.get("model_type", "transformer"),
                        "max_trials": data.get("max_trials"),
                        "parameter_space": data.get("parameter_space", {}),
                    },
                )
            )
        elif any(term in lower for term in ("ab test", "a/b test", "experiment variant", "traffic split")):
            flow.append(
                (
                    "KA-088",
                    {
                        "request_id": data.get("request_id", query_text),
                        "subject_id": data.get("subject_id"),
                        "experiment_metrics": data.get("experiment_metrics", {}),
                    },
                )
            )
        elif any(term in lower for term in ("entity", "extract", "name", "email", "regulation")):
            flow.append(("KA-048", {"text": query_text}))
        elif any(term in lower for term in ("anomaly", "outlier", "spike")):
            flow.append(("KA-039", {"data": data.get("data", []), "method": data.get("method", "zscore")}))
        elif any(term in lower for term in ("why", "explain", "best explanation", "abductive")):
            flow.append(
                (
                    "KA-041",
                    {
                        "query": query_text,
                        "observation": data.get("observation", query_text),
                        "rules": data.get("rules", []),
                        "evidence": data.get("evidence", []),
                    },
                )
            )
        elif any(term in lower for term in ("counterfactual", "what if", "what-if")):
            flow.extend(
                [
                    (
                        "KA-042",
                        {
                            "scenario": data.get("scenario", query_text),
                            "change": data.get("change", {}),
                            "baseline": data.get("baseline", {}),
                            "relationships": data.get("relationships", {}),
                        },
                    ),
                    (
                        "KA-070",
                        {
                            "hypotheticals": data.get("hypotheticals", []),
                            "graph": data.get("graph", {}),
                        },
                    ),
                ]
            )
        elif any(term in lower for term in ("analogy", "analogical", "map concept")):
            flow.append(
                (
                    "KA-044",
                    {
                        "source": data.get("source", query_text),
                        "target_domain": data.get("target_domain", ""),
                        "target_candidates": data.get("target_candidates", []),
                    },
                )
            )
        elif any(term in lower for term in ("pattern", "recurring", "sequence")):
            flow.append(("KA-045", {"stream": data.get("stream", data.get("data", []))}))
        elif any(term in lower for term in ("trend", "trajectory", "forecast direction")):
            flow.append(("KA-046", {"time_series": data.get("time_series", data.get("data", []))}))
        elif any(term in lower for term in ("sentiment", "tone", "emotion")):
            flow.append(("KA-047", {"text": data.get("text", query_text)}))
        elif any(term in lower for term in ("model", "statistical", "bayesian", "structural")):
            flow.append(
                (
                    "KA-011",
                    {
                        "data": data.get("data", []),
                        "model_type": data.get("model_type", "statistical"),
                    },
                )
            )
        else:
            flow.extend(
                [
                    ("KA-113", {"query": query_text}),
                    ("KA-001", {"query": query_text}),
                    ("KA-019", {"findings": data.get("findings", []) or [{"content": query_text}]}),
                ]
            )
        return [(ka_id, payload) for ka_id, payload in flow if ka_id in self.algorithms]

    @staticmethod
    def _summarize_flow(query: str, successful: list[dict[str, Any]], failed: list[dict[str, Any]]) -> str:
        if not successful:
            return f"Could not resolve query '{query}' because all selected KAs failed."
        if failed:
            return f"Resolved query '{query}' with {len(successful)} KA step(s); {len(failed)} step(s) degraded."
        return f"Resolved query '{query}' via {len(successful)} selected KA step(s)."

    def _fallback_logic(self, input_data: BaseModel, error: Exception) -> dict[str, Any]:
        """Master-level fallback for orchestration failures."""
        return {
            "success": False,
            "system_state": "DEGRADED",
            "error": str(error),
            "fallback_engaged": True,
            "message": "Orchestration failed. Entering safe mode."
        }

@celery_app.task(name="ka_engine.run_ka_task")
def run_ka_task(ka_id: str, input_data: dict[str, Any]):
    """Background task for long-running KAs."""
    from backend.knowledge_algorithms.ka_master_controller import get_controller
    master = get_controller()
    result = master.execute_typed(
        ka_id,
        {**input_data, "async": False},
        production_workflow=bool(input_data.get("_production_workflow")),
    )
    return result.model_dump(mode="json", exclude_none=True)

_controller_instance = None

def get_controller() -> KAMasterController:
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = KAMasterController({})
    return _controller_instance

def run(context: dict[str, Any]) -> dict[str, Any]:
    # Redundant wrapper kept for compatibility, base class .run() handles internal logic
    algo = get_controller()
    return algo.run(context)
