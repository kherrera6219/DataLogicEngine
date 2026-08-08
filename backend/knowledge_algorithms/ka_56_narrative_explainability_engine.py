"""
KA-056: Narrative Explainability Engine
Purpose: Generate audience-safe, natural language explanations and rationale maps from complex execution traces and decision logs.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA056Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_dag: Dict[str, Any] = Field(default_factory=dict, description="The execution trace DAG to explain")
    decision_log: List[Dict[str, Any]] = Field(default_factory=list, description="The log of decisions made during execution")
    audience: str = Field(default="operator", min_length=1, max_length=100)

class KA056NarrativeExplainabilityEngine(KnowledgeAlgorithm):
    """
    KA-056: Explainability and rationale generation engine for human-readable insights.
    """
    input_schema = KA056Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-056"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_56_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA056Input) -> Dict[str, Any]:
        trace_dag = input_data.trace_dag
        decision_log = input_data.decision_log
        self.log_execution_step("Generating Decision Rationale", {"decision_count": len(decision_log)})
        
        explanations = []
        for index, decision in enumerate(
            sorted(decision_log, key=lambda row: str(row.get("step_id") or ""))
        ):
            step_id = str(decision.get("step_id") or f"step-{index + 1}")
            reason_code = str(decision.get("reason_code") or "reason_not_recorded")
            confidence = decision.get("confidence")
            rationale = f"{step_id} recorded reason code {reason_code}."
            if confidence is not None:
                rationale += f" Recorded confidence: {float(confidence):.3f}."
            explanations.append(
                {
                    "step": step_id,
                    "action": decision.get("action"),
                    "rationale": rationale,
                    "reason_code": reason_code,
                    "confidence": confidence,
                    "evidence_refs": sorted(set(decision.get("evidence_refs") or [])),
                    "pivot_point": bool(decision.get("is_pivot", False)),
                }
            )

        path = trace_dag.get("summary_path")
        summary = (
            f"Explained {len(explanations)} recorded decision nodes"
            + (f" across path {path}." if path else ".")
        )
        return {
            "success": True,
            "narrative_summary": summary,
            "step_by_step_rationale": explanations,
            "audience": input_data.audience,
            "audience_vibe": self.config.get("audience_vibe", "professional"),
            "explanation_generated_from_recorded_trace_only": True,
            "provider_called": False,
            "deterministic": True,
            "limitations": (
                "The narrative restates recorded decisions and evidence links; "
                "it does not verify correctness, fill missing reasons, or reveal "
                "hidden reasoning."
            ),
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA056NarrativeExplainabilityEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-056 Failed: {e}")
        return {"success": False, "error": str(e)}
