"""
KA-011: Analytical Modeling
Purpose: Perform statistical, structural, or structural modeling on input data.
"""

import logging
import json
import os
import statistics
from collections import Counter
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA011Input(BaseModel):
    data: List[Any] = Field(
        default_factory=list, description="The data points to model"
    )
    model_type: str = Field(
        None, description="The type of modeling to perform (e.g., statistical)"
    )


class KA011AnalyticalModeling(KnowledgeAlgorithm):
    """
    KA-011: Performs data analysis and modeling.
    """

    input_schema = KA011Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-011"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_11_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA011Input) -> Dict[str, Any]:
        data = input_data.data
        model_type = input_data.model_type or self.config.get(
            "default_model_type", "statistical"
        )

        self.log_execution_step(
            "Analytical Modeling", {"model_type": model_type, "data_points": len(data)}
        )

        if not data:
            return {
                "success": True,
                "status": "measurement_required",
                "model_type": model_type,
                "results": {},
                "missing_inputs": ["data"],
                "calibrated_probability": False,
                "external_effect_applied": False,
                "deterministic": True,
            }

        nums = [x for x in data if isinstance(x, (int, float))]

        if model_type == "statistical" and nums:
            results = {
                "mean": statistics.mean(nums),
                "median": statistics.median(nums),
                "stdev": statistics.stdev(nums) if len(nums) > 1 else 0.0,
                "variance": statistics.variance(nums) if len(nums) > 1 else 0.0,
                "min": min(nums),
                "max": max(nums),
                "count": len(nums),
            }
        elif model_type == "structural":
            results = self._structural_summary(data)
        elif model_type == "bayesian" and nums:
            results = self._bayesian_summary(nums)
        else:
            supported = self.config.get(
                "supported_types", ["statistical", "structural", "bayesian"]
            )
            return {
                "success": False,
                "model_type": model_type,
                "supported_types": supported,
                "error": f"Unsupported model type or incompatible data: {model_type}",
            }

        return {
            "success": True,
            "status": "descriptive_model_computed",
            "model_type": model_type,
            "results": results,
            "confidence_adjustment": None,
            "confidence_adjustment_status": "not_measured",
            "calibrated_probability": False,
            "external_effect_applied": False,
            "deterministic": True,
            "limitations": (
                "Statistics describe only supplied values. Bayesian output is a "
                "declared shrinkage heuristic, not a calibrated posterior model."
            ),
        }

    @staticmethod
    def _structural_summary(data: List[Any]) -> Dict[str, Any]:
        type_counts = Counter(type(item).__name__ for item in data)
        dict_keys: Counter[str] = Counter()
        list_lengths = []
        scalar_count = 0
        for item in data:
            if isinstance(item, dict):
                dict_keys.update(str(key) for key in item)
            elif isinstance(item, (list, tuple, set)):
                list_lengths.append(len(item))
            else:
                scalar_count += 1
        return {
            "record_count": len(data),
            "type_counts": dict(type_counts),
            "common_fields": [key for key, _count in dict_keys.most_common(10)],
            "field_frequency": dict(dict_keys),
            "nested_collection_count": len(list_lengths),
            "average_nested_length": statistics.mean(list_lengths)
            if list_lengths
            else 0.0,
            "scalar_count": scalar_count,
        }

    @staticmethod
    def _bayesian_summary(nums: List[float]) -> Dict[str, Any]:
        prior_mean = 0.0
        prior_strength = 2.0
        sample_mean = statistics.mean(nums)
        posterior_mean = ((prior_strength * prior_mean) + (len(nums) * sample_mean)) / (
            prior_strength + len(nums)
        )
        sample_stdev = statistics.stdev(nums) if len(nums) > 1 else 0.0
        credible_half_width = (
            1.96 * (sample_stdev / (len(nums) ** 0.5)) if len(nums) > 1 else 0.0
        )
        return {
            "prior_mean": prior_mean,
            "prior_strength": prior_strength,
            "sample_mean": sample_mean,
            "posterior_mean": posterior_mean,
            "heuristic_interval_95": [
                posterior_mean - credible_half_width,
                posterior_mean + credible_half_width,
            ],
            "sample_count": len(nums),
        }


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA011AnalyticalModeling(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-011 Failed: {e}")
        return {"success": False, "error": str(e)}
