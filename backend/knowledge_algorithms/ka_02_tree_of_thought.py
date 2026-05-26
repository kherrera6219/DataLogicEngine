"""
KA-002: Tree of Thought (ToT)
Purpose: Explore multiple reasoning paths using tree search (BFS/DFS).
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA002Input(BaseModel):
    initial_state: str = Field("start", description="Initial state node for tree search")
    goal: str = Field("", description="Optional goal/query to decompose")

class KA002TreeOfThought(KnowledgeAlgorithm):
    """
    KA-002: Implements Tree of Thought search using BFS/DFS.
    """
    input_schema = KA002Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-002"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_02_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA002Input) -> Dict[str, Any]:
        initial_state = input_data.goal or input_data.initial_state
        method = self.config.get("search_method", "BFS")
        
        self.log_execution_step("Tree Search", {"method": method, "start": initial_state})
        
        if method == "BFS":
            best_path = self._bfs_search(initial_state)
        else:
            best_path = self._dfs_search(initial_state)
            
        return {
            "success": True,
            "method": method,
            "best_path": best_path,
            "sub_goals": self._sub_goals(initial_state),
        }

    def _bfs_search(self, start_node: str) -> List[str]:
        queue = [[start_node]]
        max_depth = self.config.get("max_depth", 3)
        branching = self.config.get("branching_factor", 2)
        
        best_path = []
        best_score = -1.0
        
        while queue:
            path = queue.pop(0)
            if len(path) > max_depth:
                continue
                
            current = path[-1]
            children = [f"{current}_child_{i}" for i in range(branching)]
            
            for child in children:
                new_path = list(path)
                new_path.append(child)
                score = self._score_path(new_path)
                
                if score > best_score:
                    best_score = score
                    best_path = new_path
                
                if len(new_path) < max_depth:
                    queue.append(new_path)
                    
        return best_path

    def _dfs_search(self, start_node: str) -> List[str]:
        sub_goals = self._sub_goals(start_node)
        return [start_node] + [goal["label"] for goal in sub_goals]

    @staticmethod
    def _score_path(path: List[str]) -> float:
        joined = " ".join(path).lower()
        score = 0.25 + min(0.5, len(set(joined.split())) / 20)
        if any(word in joined for word in ("risk", "verify", "evidence", "compliance")):
            score += 0.2
        return min(1.0, score)

    @staticmethod
    def _sub_goals(goal: str) -> List[Dict[str, Any]]:
        clean_goal = goal.strip() or "reason about the request"
        return [
            {"branch": "evidence", "label": f"Gather evidence for {clean_goal}", "priority": 1},
            {"branch": "risk", "label": f"Identify risks and contradictions in {clean_goal}", "priority": 2},
            {"branch": "synthesis", "label": f"Synthesize a defensible answer for {clean_goal}", "priority": 3},
        ]

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA002TreeOfThought(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-002 Failed: {e}")
        return {"success": False, "error": str(e)}
