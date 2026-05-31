"""
KA-006: Deep Planning
Purpose: Decompose complex problems into detailed, hierarchical execution plans.
"""
import logging
import json
import os
import uuid
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA006Input(BaseModel):
    problem: str = Field(..., description="The complex problem to decompose into a plan")
    requested_depth: int = Field(1, ge=1, le=5, description="The hierarchical depth of the plan")
    active_rules: List[str] = Field(default_factory=list, description="Optional active rules to incorporate")
    user_role: str = Field("standard", description="User role context for access gating")


class KA006DeepPlanning(KnowledgeAlgorithm):
    """
    KA-006: Hierarchical planner that creates a structured execution graph.
    """
    input_schema = KA006Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-006"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_06_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA006Input) -> Dict[str, Any]:
        problem = input_data.problem
        depth = input_data.requested_depth
        active_rules = input_data.active_rules
        
        self.log_execution_step("Generating Deep Plan", {"problem": problem, "depth": depth})
        
        plan = self._generate_plan(problem, depth, active_rules)
        
        return {
            "success": True,
            "plan_id": f"plan-{uuid.uuid4().hex[:8]}",
            "plan_steps": plan,
            "complexity_estimate": self._estimate_complexity(plan)
        }

    def _generate_plan(self, problem: str, depth: int, active_rules: List[str] = None) -> List[Dict[str, Any]]:
        q = problem.lower()
        
        steps = []
        # Step 1: Base gathering is always required
        steps.append({"id": "s1", "action": "Information Gathering", "target": "internal_kb"})
        
        # Categorize query to inject specialized steps dynamically
        # 1. Compliance/Audit Intent
        if any(term in q for term in ["compliance", "audit", "gdpr", "hipaa", "sox", "regulatory"]):
            steps.append({"id": "s2_reg", "action": "Regulatory Check", "target": "compliance_engine", "depends_on": ["s1"]})
            steps.append({"id": "s2_pii", "action": "PII Detection", "target": "pii_redactor", "depends_on": ["s1"]})
            
        # 2. Database/Retrieval Intent
        if any(term in q for term in ["search", "fetch", "retrieve", "corpus", "ingest", "dbs"]):
            steps.append({"id": "s3_db", "action": "Vector Database Scan", "target": "chromadb_adapter", "depends_on": ["s1"]})
            steps.append({"id": "s3_filter", "action": "Entity Proximity Filtering", "target": "proximity_calculator", "depends_on": ["s3_db"]})
            
        # 3. Security/Adversarial Intent
        if any(term in q for term in ["security", "adversarial", "jailbreak", "override", "bypass"]):
            steps.append({"id": "s4_shield", "action": "Adversarial Guardrail Scan", "target": "ai_guardrail", "depends_on": ["s1"]})
            steps.append({"id": "s4_inject", "action": "Injection Defense Check", "target": "injection_defense", "depends_on": ["s4_shield"]})
            
        # 4. Temporal/Trend Intent
        if any(term in q for term in ["trend", "history", "projection", "forecast", "time"]):
            steps.append({"id": "s5_time", "action": "Temporal Regression Calibration", "target": "temporal_calculator", "depends_on": ["s1"]})

        # Add a default reasoning simulation step if none of the above are matched (keeps plans interesting)
        if len(steps) == 1:
            steps.append({"id": "s_sim", "action": "Scenario Simulation", "target": "L5_simulator", "depends_on": ["s1"]})
            
        # Append final synthesis step, which dynamically depends on the last step(s) added
        last_step_ids = [step["id"] for step in steps if step["id"] != "s1"]
        if not last_step_ids:
            last_step_ids = ["s1"]
            
        steps.append({"id": "s_synthesis", "action": "Final Synthesis", "target": "report_generator", "depends_on": last_step_ids})
        
        # Expand sub-steps based on depth parameter
        if depth > 1:
            for step in steps:
                step["sub_steps"] = [
                    {"id": f"{step['id']}_sub1", "action": f"Prepare {step['action']}", "status": "PENDING"},
                    {"id": f"{step['id']}_sub2", "action": f"Execute {step['action']}", "status": "PENDING"}
                ]

        # Configure step durations and state from configuration
        default_duration = self.config.get("default_step_duration_ms", 100)
        for step in steps:
            step["estimated_duration_ms"] = default_duration
            step["status"] = "PENDING"
            
        return steps

    def _estimate_complexity(self, plan: List[Dict[str, Any]]) -> float:
        base = len(plan) * 0.1
        deps = sum(len(s.get("depends_on", [])) for s in plan) * 0.05
        sub_steps_count = sum(len(s.get("sub_steps", [])) for s in plan) * 0.02
        return min(1.0, round(base + deps + sub_steps_count, 4))


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA006DeepPlanning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-006 Failed: {e}")
        return {"success": False, "error": str(e)}
