"""
KA-084: Model Monitoring
Purpose: Monitor live model performance, detect data drift, and track latency/skew metrics.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA084MonitoringInput(BaseModel):
    live_metrics: Dict[str, Any] = Field(default_factory=dict, description="Live performance metrics from the running model")
    baseline_metrics: Dict[str, Any] = Field(default_factory=dict, description="Baseline metrics used for drift comparison")

class KA084ModelMonitoring(KnowledgeAlgorithm):
    """
    KA-084: ML performance monitoring and live drift detection engine.
    """
    input_schema = KA084MonitoringInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-084"
        self.config = {**self._load_config(), **context}

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_84_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA084MonitoringInput) -> Dict[str, Any]:
        live_metrics = input_data.live_metrics
        self.log_execution_step("Detecting Model Drift", {"metric_count": len(live_metrics)})
        
        thresholds = self.config.get("drift_thresholds", {})
        detected_anomalies = []
        metric_deltas = {}
        
        if live_metrics.get("p99_latency", 0) > thresholds.get("latency_spike_ms", 1000):
            detected_anomalies.append("LATENCY_SPIKE")
        
        if live_metrics.get("prediction_skew", 0) > thresholds.get("prediction_skew", 0.5):
            detected_anomalies.append("PREDICTION_SKEW")

        baseline_metrics = input_data.baseline_metrics
        drift_ratio_threshold = thresholds.get("relative_drift_ratio", 0.2)
        for metric, live_value in live_metrics.items():
            baseline_value = baseline_metrics.get(metric)
            if not isinstance(live_value, (int, float)) or not isinstance(baseline_value, (int, float)):
                continue
            if baseline_value == 0:
                continue
            delta_ratio = (live_value - baseline_value) / abs(baseline_value)
            metric_deltas[metric] = round(delta_ratio, 4)
            if abs(delta_ratio) > drift_ratio_threshold:
                detected_anomalies.append(f"{metric.upper()}_DRIFT")

        detected_anomalies = sorted(set(detected_anomalies))
        health_score = max(0.0, round(1.0 - (len(detected_anomalies) * 0.15), 4))
            
        return {
            "success": True,
            "drift_detected": len(detected_anomalies) > 0,
            "anomalies": detected_anomalies,
            "metric_deltas": metric_deltas,
            "health_score": health_score,
            "alert_recommended": len(detected_anomalies) > 0,
            "notification_applied": False,
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA084ModelMonitoring(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-084 Failed: {e}")
        return {"success": False, "error": str(e)}
