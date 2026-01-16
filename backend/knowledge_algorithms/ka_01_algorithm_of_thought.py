"""
KA-001: Algorithm of Thought (AoT)
Purpose: Decompose query into ordered tasks and dependencies using configurable strategies.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA001Input(BaseModel):
    query: str = Field(..., description="The complex query to decompose")

class KA001AlgorithmOfThought(KnowledgeAlgorithm):
    """
    KA-001: Decomposes complex queries into a Directed Acyclic Graph (DAG) of tasks.
    """
    input_schema = KA001Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-001"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_01_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA001Input) -> Dict[str, Any]:
        query = input_data.query
        self.log_execution_step("Decomposing query", {"query": query})
        
        # Determine strategy
        strategy_name = self._determine_strategy(query)
        self.log_execution_step("Selected Strategy", {"strategy": strategy_name})
        
        # Decompose
        tasks = self._decompose(query, strategy_name)
        
        return {
            "success": True,
            "strategy": strategy_name,
            "tasks": tasks,
            "graph": self._build_dependency_graph(tasks)
        }

    def _determine_strategy(self, query: str) -> str:
        length = len(query.split())
        complexity_score = 0.5 
        if length > 20 or "research" in query.lower():
            complexity_score = 0.8
        elif length < 5:
            complexity_score = 0.2
            
        thresholds = self.config.get("complexity_thresholds", {"simple": 0.3, "standard": 0.7})
        
        if "research" in query.lower():
            return "research"
        elif complexity_score < thresholds["simple"]:
            return "simple"
        else:
            return "standard"

    def _decompose(self, query: str, strategy_name: str) -> List[Dict[str, Any]]:
        strategies = self.config.get("strategies", {})
        steps = strategies.get(strategy_name, strategies.get("standard", []))
        
        tasks = []
        prev_id = None
        
        for i, step in enumerate(steps):
            task_id = f"t{i+1}"
            task = {
                "id": task_id,
                "name": step.get("desc", step.get("step")), 
                "step_type": step.get("step"),
                "ka": step.get("ka")
            }
            if prev_id:
                task["deps"] = [prev_id]
            tasks.append(task)
            prev_id = task_id
        return tasks

    def _build_dependency_graph(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        adj_list = {}
        for t in tasks:
            adj_list[t["id"]] = t.get("deps", [])
        return adj_list

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA001AlgorithmOfThought(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-001 Failed: {e}")
        return {"success": False, "error": str(e)}
