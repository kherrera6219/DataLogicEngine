"""
KA-039: Anomaly Detection
Purpose: Detect anomalies in data streams or logic.
"""

import logging
import statistics
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, ConfigDict, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA039Input(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: List[Any] = Field(default_factory=list)
    method: Literal["zscore", "iqr"] = "zscore"
    threshold: float = Field(default=3.0, gt=0, le=10)


class KA039AnomalyDetection(KnowledgeAlgorithm):
    input_schema = KA039Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def _run_logic(self, input_data: KA039Input) -> Dict[str, Any]:
        data = input_data.data

        self.log_execution_step("Detecting Anomalies", {"points": len(data)})

        numeric = [float(item) for item in data if isinstance(item, (int, float))]
        anomalies = self._detect_numeric_anomalies(
            numeric, input_data.method, input_data.threshold
        )

        return {
            "ka_id": "KA-039",
            "success": True,
            "anomalies": anomalies,
            "count": len(anomalies),
            "method": input_data.method,
            "baseline": self._baseline(numeric),
            "measurement_status": "measured"
            if len(numeric) >= 3
            else "insufficient_data",
            "deterministic": True,
            "limitations": (
                "Only numeric values are measured; threshold findings are statistical "
                "signals and do not identify a root cause."
            ),
        }

    @staticmethod
    def _baseline(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0}
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        }

    @staticmethod
    def _detect_numeric_anomalies(
        values: List[float], method: str, threshold: float
    ) -> List[Dict[str, Any]]:
        if len(values) < 3:
            return []
        method = method.lower().strip()
        if method == "iqr":
            ordered = sorted(values)
            mid = len(ordered) // 2
            lower = ordered[:mid]
            upper = ordered[mid + (0 if len(ordered) % 2 == 0 else 1) :]
            q1 = statistics.median(lower)
            q3 = statistics.median(upper)
            iqr = q3 - q1
            low = q1 - threshold * iqr
            high = q3 + threshold * iqr
            return [
                {
                    "index": index,
                    "value": value,
                    "score": None,
                    "reason": "outside_iqr_fence",
                }
                for index, value in enumerate(values)
                if value < low or value > high
            ]

        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        if stdev == 0:
            return []
        return [
            {
                "index": index,
                "value": value,
                "score": zscore,
                "reason": "zscore_threshold",
            }
            for index, value in enumerate(values)
            if abs((zscore := (value - mean) / stdev)) >= threshold
        ]


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA039AnomalyDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-039 Failed: {e}")
        return {"success": False, "error": str(e)}
