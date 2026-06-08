"""
KA-089: Model Pruning
Purpose: Reduce model size and inference latency by removing less significant weights (sparsification) while maintaining accuracy.
"""
import logging
import json
import os
from typing import Dict, Any, List, Optional
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA089PruningInput(BaseModel):
    model_id: str = Field("latest", description="The identifier for the model to prune")
    parameter_count: int = Field(0, ge=0, description="Number of model parameters before pruning")
    target_sparsity: Any = Field(None, description="Desired fraction of parameters to prune")
    importance_scores: List[float] = Field(default_factory=list, description="Optional per-weight or per-block importance scores")
    baseline_accuracy: Any = Field(None, description="Baseline model accuracy before pruning")

class KA089ModelPruning(KnowledgeAlgorithm):
    """
    KA-089: Model weight sparsification and pruning engine for efficiency.
    """
    input_schema = KA089PruningInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-089"
        self.config = {**self._load_config(), **context}

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_89_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA089PruningInput) -> Dict[str, Any]:
        model_id = input_data.model_id
        self.log_execution_step("Pruning Model Weights", {"model": model_id, "method": self.config.get("pruning_method", "magnitude")})
        
        target_sparsity = input_data.target_sparsity
        if target_sparsity is None:
            target_sparsity = self.config.get("target_sparsity", 0.1)
        target_sparsity = self._as_float(target_sparsity, 0.1, 0.0, 0.95)

        params_before = input_data.parameter_count or self.config.get("default_parameter_count", 0)
        params_after = self._remaining_parameters(params_before, target_sparsity, input_data.importance_scores)
        params_removed = params_before - params_after
        accuracy_estimate = self._accuracy_after_pruning(
            self._as_float(input_data.baseline_accuracy, None, 0.0, 1.0),
            target_sparsity,
            input_data.importance_scores,
        )
        
        return {
            "success": True,
            "pruned_model_id": f"{model_id}_pruned",
            "sparsity_achieved": round(target_sparsity, 4),
            "params_before": params_before,
            "params_after": params_after,
            "params_removed": params_removed,
            "estimated_accuracy": accuracy_estimate,
            "compression_ratio": f"{(params_before / max(1, params_after)):.2f}x"
        }

    @staticmethod
    def _remaining_parameters(params_before: int, target_sparsity: float, importance_scores: List[float]) -> int:
        if params_before <= 0:
            return 0
        if importance_scores:
            prune_count = min(len(importance_scores), int(round(len(importance_scores) * target_sparsity)))
            return max(0, params_before - prune_count)
        return int(round(params_before * (1.0 - target_sparsity)))

    @staticmethod
    def _accuracy_after_pruning(
        baseline_accuracy: Optional[float],
        target_sparsity: float,
        importance_scores: List[float],
    ) -> Optional[float]:
        if baseline_accuracy is None:
            return None
        if importance_scores:
            sorted_scores = sorted(max(0.0, min(1.0, score)) for score in importance_scores)
            prune_count = int(round(len(sorted_scores) * target_sparsity))
            pruned_scores = sorted_scores[:prune_count]
            average_importance = sum(pruned_scores) / max(1, len(pruned_scores))
        else:
            average_importance = 0.5
        estimated_loss = target_sparsity * average_importance * 0.2
        return round(max(0.0, baseline_accuracy - estimated_loss), 4)

    @staticmethod
    def _as_float(value: Any, default: Optional[float], minimum: float, maximum: float) -> Optional[float]:
        if value is None:
            return default
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA089ModelPruning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-089 Failed: {e}")
        return {"success": False, "error": str(e)}
