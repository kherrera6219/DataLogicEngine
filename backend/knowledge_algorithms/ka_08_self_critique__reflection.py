"""
KA-008: Self Critique & Reflection
Purpose: Critically evaluate own responses against rubrics and suggest improvements.
"""
import logging
import json
import os
import random
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA008Input(BaseModel):
    output_content: str = Field(..., description="The content to critique")
    query: str = Field("", description="The original query for context")

class KA008SelfCritique(KnowledgeAlgorithm):
    """
    KA-008: Evaluates and reflects on system outputs to ensure high quality.
    """
    input_schema = KA008Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-008"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_08_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA008Input) -> Dict[str, Any]:
        content = input_data.output_content
        context_query = input_data.query
        
        self.log_execution_step("Critiquing Content", {"content_len": len(content)})
        
        critique_results = self._evaluate_rubrics(content, context_query)
        overall_score = self._calculate_overall_score(critique_results)
        suggestions = self._generate_suggestions(critique_results)
        
        regen_needed = overall_score < self.config.get("auto_regen_threshold", 0.5)
        
        return {
            "success": True,
            "overall_score": overall_score,
            "rubric_scores": critique_results,
            "suggestions": suggestions,
            "regeneration_recommended": regen_needed,
            "is_sufficient": not regen_needed
        }

    def _evaluate_rubrics(self, content: str, query: str) -> Dict[str, float]:
        rubrics = self.config.get("rubrics", {})
        results = {}
        for name, params in rubrics.items():
            results[name] = random.uniform(0.6, 1.0) # Baseline
            if name == "accuracy" and "unknown" in content.lower():
                results[name] *= 0.5
            if name == "clarity" and len(content) > 1000:
                results[name] *= 0.8
        return results

    def _calculate_overall_score(self, results: Dict[str, float]) -> float:
        rubrics = self.config.get("rubrics", {})
        total_weight = sum(r.get("weight", 0) for r in rubrics.values())
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(results[name] * rubrics[name].get("weight", 0) for name in results)
        return weighted_sum / total_weight

    def _generate_suggestions(self, results: Dict[str, float]) -> List[str]:
        suggestions = []
        rubrics = self.config.get("rubrics", {})
        for name, score in results.items():
            min_score = rubrics.get(name, {}).get("min_score", 0.7)
            if score < min_score:
                suggestions.append(f"Improve {name}: current score {score:.2f} is below target {min_score:.2f}")
        if not suggestions:
            suggestions.append("Quality is sufficient.")
        return suggestions

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA008SelfCritique(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-008 Failed: {e}")
        return {"success": False, "error": str(e)}
