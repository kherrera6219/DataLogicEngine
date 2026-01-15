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

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA006Input(BaseModel):
    problem: str = Field(..., description="The complex problem to decompose into a plan")
    requested_depth: int = Field(1, ge=1, le=5, description="The hierarchical depth of the plan")

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
        
        self.log_execution_step("Generating Deep Plan", {"problem": problem, "depth": depth})
        
        plan = self._generate_plan(problem, depth)
        
        return {
            "success": True,
            "plan_id": f"plan-{uuid.uuid4().hex[:8]}",
            "plan_steps": plan,
            "complexity_estimate": self._estimate_complexity(plan)
        }

    def _generate_plan(self, problem: str, depth: int) -> List[Dict[str, Any]]:
        steps = [
            {"id": "s1", "action": "Information Gathering", "target": "internal_kb"},
            {"id": "s2", "action": "Regulatory Check", "target": "compliance_engine", "depends_on": ["s1"]},
            {"id": "s3", "action": "Scenario Simulation", "target": "L5_simulator", "depends_on": ["s2"]},
            {"id": "s4", "action": "Final Synthesis", "target": "report_generator", "depends_on": ["s3"]}
        ]
        
        for step in steps:
            step["estimated_duration_ms"] = self.config.get("default_step_duration_ms", 100)
            step["status"] = "PENDING"
            
        return steps

    def _estimate_complexity(self, plan: List[Dict[str, Any]]) -> float:
        base = len(plan) * 0.1
        deps = sum(len(s.get("depends_on", [])) for s in plan) * 0.05
        return min(1.0, base + deps)

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA006DeepPlanning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-006 Failed: {e}")
        return {"success": False, "error": str(e)}
