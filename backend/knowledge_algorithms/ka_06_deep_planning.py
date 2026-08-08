"""
KA-006: Deep Planning
Purpose: Decompose complex problems into detailed, hierarchical execution plans.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier

logger = logging.getLogger(__name__)


class KA006Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem: str = Field(..., description="The complex problem to decompose into a plan")
    requested_depth: int = Field(1, ge=1, le=5, description="The hierarchical depth of the plan")
    active_rules: List[str] = Field(default_factory=list, description="Optional active rules to incorporate")
    user_role: str = Field("standard", description="User role context for access gating")
    dependency_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


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
        
        dependencies = input_data.dependency_results
        gap_result = dependencies.get("KA-003", {})
        classification = dependencies.get("KA-005", {})
        query_type = str(
            classification.get("query_type")
            or classification.get("classification")
            or classification.get("category")
            or "unclassified"
        )
        plan = self._generate_plan(
            problem,
            depth,
            active_rules,
            gaps=list(gap_result.get("identified_gaps") or gap_result.get("gaps") or []),
            query_type=query_type,
        )
        plan_identity = {
            "problem": problem,
            "depth": depth,
            "rules": sorted(set(active_rules)),
            "steps": plan,
        }
        
        return {
            "success": True,
            "plan_id": stable_identifier("plan", plan_identity),
            "plan_steps": plan,
            "complexity_estimate": self._estimate_complexity(plan),
            "query_type": query_type,
            "dependencies_consumed": sorted(dependencies),
            "candidate_only": True,
            "execution_started": False,
            "limitations": (
                "This is a bounded deterministic candidate plan. The governed "
                "execution service must authorize, schedule, and receipt every effect."
            ),
        }

    def _generate_plan(
        self,
        problem: str,
        depth: int,
        active_rules: List[str] | None = None,
        *,
        gaps: List[Any] | None = None,
        query_type: str = "unclassified",
    ) -> List[Dict[str, Any]]:
        query = problem.lower()
        rules = sorted({str(rule).strip() for rule in active_rules or [] if str(rule).strip()})
        normalized_gaps = sorted(
            {
                str(gap.get("gap") or gap.get("description") or gap)
                if isinstance(gap, dict)
                else str(gap)
                for gap in gaps or []
                if str(gap).strip()
            }
        )
        steps: List[Dict[str, Any]] = [
            {
                "id": "s1",
                "action": "Frame objective and acceptance criteria",
                "inputs": [problem],
                "depends_on": [],
            },
            {
                "id": "s2",
                "action": "Resolve declared evidence gaps",
                "inputs": normalized_gaps,
                "depends_on": ["s1"],
            },
            {
                "id": "s3",
                "action": "Apply active constraints",
                "inputs": rules,
                "depends_on": ["s2"],
            },
            {
                "id": "s4",
                "action": "Prepare reviewable execution proposal",
                "inputs": [query_type],
                "depends_on": ["s3"],
            },
        ]
        review_steps: List[Dict[str, Any]] = []
        if any(
            term in query
            for term in ["compliance", "audit", "gdpr", "hipaa", "sox", "regulatory"]
        ):
            review_steps.extend(
                [
                    {
                        "id": "s2_reg",
                        "action": "Prepare regulatory evidence review",
                        "inputs": [],
                        "depends_on": ["s1"],
                    },
                    {
                        "id": "s2_pii",
                        "action": "Prepare privacy and sensitive-data review",
                        "inputs": [],
                        "depends_on": ["s1"],
                    },
                ]
            )
        if any(
            term in query
            for term in ["security", "adversarial", "jailbreak", "override", "bypass"]
        ):
            review_steps.extend(
                [
                    {
                        "id": "s4_shield",
                        "action": "Prepare adversarial-boundary review",
                        "inputs": [],
                        "depends_on": ["s1"],
                    },
                    {
                        "id": "s4_inject",
                        "action": "Prepare injection-defense review",
                        "inputs": [],
                        "depends_on": ["s4_shield"],
                    },
                ]
            )
        steps.extend(review_steps)
        steps.append(
            {
                "id": "s_synthesis",
                "action": "Synthesize reviewable candidate plan",
                "inputs": [],
                "depends_on": ["s4", *(step["id"] for step in review_steps)],
            }
        )
        
        # Expand sub-steps based on depth parameter
        if depth > 1:
            for step in steps:
                step["sub_steps"] = [
                    {
                        "id": f"{step['id']}_sub{level - 1}",
                        "action": f"Refine level {level}: {step['action']}",
                        "status": "PROPOSED",
                    }
                    for level in range(2, depth + 1)
                ]

        # Configure step durations and state from configuration
        default_duration = self.config.get("default_step_duration_ms", 100)
        for step in steps:
            step["estimated_duration_ms"] = default_duration
            step["status"] = "PROPOSED"
            
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
