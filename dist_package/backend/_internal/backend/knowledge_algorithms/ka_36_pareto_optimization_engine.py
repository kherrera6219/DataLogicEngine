"""
KA-036: Pareto Optimization Engine
Purpose: Optimize multi-objective trade-offs between conflicting goals like cost, performance, and risk.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA036Input(BaseModel):
    options: List[Dict[str, Any]] = Field(default_factory=list, description="Options to evaluate for Pareto optimality")

class KA036ParetoOptimizationEngine(KnowledgeAlgorithm):
    """
    KA-036: Multi-objective optimization engine for trade-off analysis.
    """
    input_schema = KA036Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-036"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_36_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA036Input) -> Dict[str, Any]:
        options = input_data.options
        self.log_execution_step("Finding Pareto Front", {"option_count": len(options)})
        
        def dominates(o1, o2):
            return o1.get("performance", 0) >= o2.get("performance", 0) and o1.get("cost", 100) <= o2.get("cost", 100)
            
        pareto_front = []
        for i, o1 in enumerate(options):
            is_dominated = False
            for j, o2 in enumerate(options):
                if i != j and dominates(o2, o1) and (o2["performance"] > o1["performance"] or o2["cost"] < o1["cost"]):
                    is_dominated = True
                    break
            if not is_dominated:
                pareto_front.append(o1)
                
        return {
            "success": True,
            "pareto_options": pareto_front,
            "recommended_optima": pareto_front[0] if pareto_front else None
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA036ParetoOptimizationEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-036 Failed: {e}")
        return {"success": False, "error": str(e)}
