"""
KA-Master: Master Controller
Purpose: The top-level orchestrator that manages the entire lifecycle of all 116 Knowledge Algorithms, 
providing a unified interface for complex query resolution and system self-management.
"""
import logging
import os
import importlib
import time
import uuid
import yaml
from datetime import datetime, UTC
from typing import Dict, Any
from pydantic import BaseModel
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from celery import Celery

from core.knowledge_algorithm.exceptions import KAError, KAConfigError

logger = logging.getLogger(__name__)

# Initialize celery
celery_app = Celery('ka_tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

class KAMasterController(KnowledgeAlgorithm):
    """
    KA-Master: The supreme orchestrator and system state machine.
    """
    def __init__(self, context: Dict[str, Any] = None):
        super().__init__(context or {}, None, None, None)
        self.ka_id = "KA-Master"
        self.llm_gateway = (context or {}).get("llm_gateway") if isinstance(context, dict) else None
        self._registry_path = os.path.join(os.path.dirname(__file__), "ka_registry.yaml")
        self.algorithms = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load available algorithms from ka_registry.yaml."""
        try:
            if os.path.exists(self._registry_path):
                with open(self._registry_path, "r") as f:
                    data = yaml.safe_load(f)
                    reg = data.get("ka_registry", {})
                    return {k: {"id": k, "metadata": {"KA_ID": k, "Status": "Active", "Implementation": v}} for k, v in reg.items()}
            return {}
        except Exception as e:
            raise KAConfigError(f"Failed to load KA registry: {str(e)}")

    def get_available_algorithms(self) -> Dict[str, Any]:
        return self.algorithms

    def _normalize_ka_id(self, ka_id: str) -> str:
        if not isinstance(ka_id, str):
            ka_id = str(ka_id)
        clean_id = ka_id.upper().strip()
        if clean_id.startswith("KA-"):
            if len(clean_id) == 6:
                return clean_id
            num_part = clean_id.replace("KA-", "").lstrip("0") or "0"
        else:
            num_part = clean_id.lstrip("0") or "0"
        try:
            return f"KA-{int(num_part):03d}"
        except ValueError:
            return clean_id

    def execute_algorithm(self, ka_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically imports and executes a specific Knowledge Algorithm with error propagation."""
        norm_id = self._normalize_ka_id(ka_id)
        is_async = input_data.get("async", False)
        
        self.log_execution_step("Dispatching Algorithm", {"ka_id": norm_id, "mode": "async" if is_async else "sync"})
        
        if norm_id not in self.algorithms:
            raise KAError(f"Algorithm {norm_id} not registered.", error_code="E404")
            
        if is_async:
            task = run_ka_task.delay(norm_id, input_data)
            return {"success": True, "ka_id": norm_id, "mode": "async", "task_id": task.id, "status": "PENDING"}

        impl_path = self.algorithms[norm_id]["metadata"]["Implementation"]
        started_at = datetime.now(UTC)
        start_time = time.perf_counter()
        try:
            module_path, function_name = impl_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            run_func = getattr(module, function_name)
            result = run_func(input_data)
            self._record_ka_execution(
                norm_id,
                input_data,
                output_data=result,
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )
            return result
        except Exception as e:
            self._record_ka_execution(
                norm_id,
                input_data,
                error=e,
                elapsed_ms=(time.perf_counter() - start_time) * 1000,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )
            self.logger.error(f"Execution of {norm_id} failed: {e}")
            raise KAError(f"Recursive Execution Failure on {norm_id}", error_code="E502", details={"inner_error": str(e)})

    def _record_ka_execution(
        self,
        ka_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any] | None = None,
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
                execution_time_ms=max(0, int(round(elapsed_ms))),
                tenant_id=(input_data or {}).get("tenant_id"),
                started_at=started_at or datetime.now(UTC),
                completed_at=completed_at or datetime.now(UTC),
            )
            session.add(execution)
            session.commit()
        except Exception as exc:
            try:
                session.rollback()
            except Exception:
                pass
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
        except Exception:
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
        except Exception:
            return None

    def _run_logic(self, input_data: BaseModel) -> Dict[str, Any]:
        """High-level query orchestration."""
        data = input_data.data if hasattr(input_data, "data") else {}
        query = data.get("query", "status_check")
        flow = self._select_flow(query, data)
        step_results = []
        for ka_id, payload in flow:
            try:
                result = self.execute_algorithm(ka_id, payload)
                step_results.append(
                    {
                        "ka_id": ka_id,
                        "success": bool(result.get("success", True)),
                        "result": self._json_safe(result),
                    }
                )
            except Exception as exc:
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

    def _select_flow(self, query: str, data: Dict[str, Any]) -> list[tuple[str, Dict[str, Any]]]:
        """Choose a bounded local KA chain for the current request."""
        query_text = str(query or "")
        lower = query_text.lower()
        flow: list[tuple[str, Dict[str, Any]]] = [
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
    def _summarize_flow(query: str, successful: list[Dict[str, Any]], failed: list[Dict[str, Any]]) -> str:
        if not successful:
            return f"Could not resolve query '{query}' because all selected KAs failed."
        if failed:
            return f"Resolved query '{query}' with {len(successful)} KA step(s); {len(failed)} step(s) degraded."
        return f"Resolved query '{query}' via {len(successful)} selected KA step(s)."

    def _fallback_logic(self, input_data: BaseModel, error: Exception) -> Dict[str, Any]:
        """Master-level fallback for orchestration failures."""
        return {
            "success": False,
            "system_state": "DEGRADED",
            "error": str(error),
            "fallback_engaged": True,
            "message": "Orchestration failed. Entering safe mode."
        }

@celery_app.task(name="ka_engine.run_ka_task")
def run_ka_task(ka_id: str, input_data: Dict[str, Any]):
    """Background task for long-running KAs."""
    from backend.knowledge_algorithms.ka_master_controller import get_controller
    master = get_controller()
    return master.execute_algorithm(ka_id, {**input_data, "async": False})

_controller_instance = None

def get_controller() -> KAMasterController:
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = KAMasterController({})
    return _controller_instance

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    # Redundant wrapper kept for compatibility, base class .run() handles internal logic
    algo = get_controller()
    return algo.run(context)
