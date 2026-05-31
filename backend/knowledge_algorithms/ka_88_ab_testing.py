"""
KA-088: AB Testing
Purpose: Orchestrate deterministic traffic assignment and experiment metric summaries.
"""
import hashlib
import json
import logging
import math
import os
from typing import Any, Dict

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA088ABInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    request_id: str = Field(..., description="The unique identifier for the inference request")
    subject_id: str | None = None
    experiment_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class KA088ABTesting(KnowledgeAlgorithm):
    """
    KA-088: Deterministic traffic splitting and statistical experiment engine.
    """
    input_schema = KA088ABInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-088"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_88_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA088ABInput) -> Dict[str, Any]:
        subject = input_data.subject_id or input_data.request_id
        self.log_execution_step("Selecting Experiment Variant", {"req": input_data.request_id})

        split = self.config.get("traffic_split_percent", {"control": 50, "variant_a": 50})
        variant = self._assign_variant(subject, split)
        analysis = self._analyze_metrics(input_data.experiment_metrics)
        return {
            "success": True,
            "assigned_variant": variant,
            "assignment_basis": subject,
            "experiment_active": True,
            "metrics_tracked": self.config.get("metrics_to_track", []),
            "analysis": analysis,
        }

    @staticmethod
    def _assign_variant(subject: str, split: Dict[str, Any]) -> str:
        variants = [(name, float(percent)) for name, percent in split.items()]
        total = sum(percent for _name, percent in variants) or 100.0
        bucket = int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16) % 10000 / 10000 * total
        cumulative = 0.0
        for name, percent in variants:
            cumulative += percent
            if bucket <= cumulative:
                return name
        return variants[-1][0] if variants else "control"

    def _analyze_metrics(self, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        control = metrics.get("control", {})
        variant = metrics.get("variant_a", metrics.get("variant", {}))
        if not control or not variant:
            return {"sufficient_data": False, "reason": "missing_control_or_variant_metrics"}
        control_rate = self._rate(control)
        variant_rate = self._rate(variant)
        z_score = self._z_score(control_rate, variant_rate, self._safe_int(control.get("n"), 0), self._safe_int(variant.get("n"), 0))
        significant = abs(z_score) >= 1.96
        return {
            "sufficient_data": self._safe_int(control.get("n"), 0) >= self.config.get("min_sample_size", 1000)
            and self._safe_int(variant.get("n"), 0) >= self.config.get("min_sample_size", 1000),
            "control_rate": round(control_rate, 4),
            "variant_rate": round(variant_rate, 4),
            "lift": round(variant_rate - control_rate, 4),
            "z_score": round(z_score, 4),
            "statistically_significant": significant,
        }

    @staticmethod
    def _rate(values: Dict[str, Any]) -> float:
        n = KA088ABTesting._safe_int(values.get("n"), 0)
        conversions = KA088ABTesting._safe_int(values.get("conversions", values.get("successes", 0)), 0)
        return conversions / n if n else 0.0

    @staticmethod
    def _z_score(control_rate: float, variant_rate: float, control_n: int, variant_n: int) -> float:
        if not control_n or not variant_n:
            return 0.0
        pooled = ((control_rate * control_n) + (variant_rate * variant_n)) / (control_n + variant_n)
        stderr = math.sqrt(max(1e-9, pooled * (1 - pooled) * (1 / control_n + 1 / variant_n)))
        return (variant_rate - control_rate) / stderr

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA088ABTesting(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-088 Failed: {e}")
        return {"success": False, "error": str(e)}
