"""
KA-032: Simulation Orchestration Controller
Purpose: Sequence and manage KA execution flow, layer transitions, checkpoints, and exit criteria.
"""
import json
import logging
import os
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA032Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    pipeline: List[Any] = Field(default_factory=list, description="Sequence of KA IDs or step objects")
    simulation_state: Dict[str, Any] = Field(default_factory=dict, description="Current state of the simulation")
    exit_criteria: Dict[str, Any] = Field(default_factory=dict)


class KA032SimulationOrchestrationController(KnowledgeAlgorithm):
    """
    KA-032: Orchestration and sequence management engine for KA execution flow.
    """
    input_schema = KA032Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-032"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_32_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA032Input) -> Dict[str, Any]:
        steps = [self._normalize_step(step, index) for index, step in enumerate(input_data.pipeline)]
        state = dict(input_data.simulation_state)
        self.log_execution_step("Orchestrating Sequence", {"steps": len(steps), "mode": self.config.get("execution_mode", "sequential")})

        completed: set[str] = set(state.get("completed_steps", []))
        failed: List[Dict[str, Any]] = []
        executed_steps = []
        checkpoints = []
        stop_on_error = bool(self.config.get("stop_on_error", False))

        for step in steps:
            dependency_status = self._dependency_status(step, completed)
            status = "PENDING"
            if dependency_status["blocked"]:
                status = "SKIPPED_BLOCKED"
            elif step["ka_id"] in set(state.get("failed_kas", [])):
                status = "FAILED"
                failed.append({"ka_id": step["ka_id"], "reason": "listed_in_failed_kas"})
            else:
                status = "READY"
                completed.add(step["step_id"])

            record = {**step, "status": status, "dependencies": dependency_status}
            executed_steps.append(record)
            if self.config.get("checkpoint_enabled", True) and status in {"READY", "FAILED", "SKIPPED_BLOCKED"}:
                checkpoints.append({"checkpoint_id": f"cp_{step['step']}", "step_id": step["step_id"], "status": status})
            if status == "FAILED" and stop_on_error:
                break

        criteria_result = self._evaluate_exit_criteria(input_data.exit_criteria, executed_steps, failed)
        final_status = "FAILED" if failed and stop_on_error else "BLOCKED" if any(step["status"] == "SKIPPED_BLOCKED" for step in executed_steps) else "COMPLETED"
        if not criteria_result["met"]:
            final_status = "CRITERIA_NOT_MET"

        return {
            "success": final_status in {"COMPLETED", "BLOCKED"},
            "execution_schedule": executed_steps,
            "final_status": final_status,
            "checkpoints": checkpoints,
            "checkpoints_captured": len(checkpoints),
            "exit_criteria": criteria_result,
        }

    @staticmethod
    def _normalize_step(step: Any, index: int) -> Dict[str, Any]:
        if isinstance(step, dict):
            ka_id = str(step.get("ka_id") or step.get("id") or step.get("name") or f"STEP-{index + 1}")
            deps = step.get("depends_on", step.get("dependencies", []))
        else:
            ka_id = str(step)
            deps = []
        return {"step": index + 1, "step_id": f"step_{index + 1}", "ka_id": ka_id, "depends_on": list(deps or [])}

    @staticmethod
    def _dependency_status(step: Dict[str, Any], completed: set[str]) -> Dict[str, Any]:
        missing = [dep for dep in step["depends_on"] if dep not in completed]
        return {"blocked": bool(missing), "missing": missing}

    @staticmethod
    def _evaluate_exit_criteria(criteria: Dict[str, Any], steps: List[Dict[str, Any]], failed: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not criteria:
            return {"met": True, "reason": "no_exit_criteria"}
        min_completed = int(criteria.get("min_completed", 0) or 0)
        max_failures = int(criteria.get("max_failures", len(steps)) or len(steps))
        completed_count = sum(1 for step in steps if step["status"] == "READY")
        met = completed_count >= min_completed and len(failed) <= max_failures
        return {"met": met, "completed_count": completed_count, "failure_count": len(failed), "min_completed": min_completed, "max_failures": max_failures}


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA032SimulationOrchestrationController(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-032 Failed: {e}")
        return {"success": False, "error": str(e)}
