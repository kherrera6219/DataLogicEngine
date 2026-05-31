"""
KA-046: Trend Analysis
Purpose: Analyze data trends over time.
"""
import logging
import statistics
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA046Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    time_series: List[Any] = Field(default_factory=list)


class KA046TrendAnalysis(KnowledgeAlgorithm):
    input_schema = KA046Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-046"

    def _run_logic(self, input_data: KA046Input) -> Dict[str, Any]:
        numeric = self._numeric_series(input_data.time_series)
        self.log_execution_step("Analyzing Trend", {"points": len(numeric)})

        slope, intercept = self._linear_regression(numeric)
        volatility = statistics.stdev(numeric) if len(numeric) > 1 else 0.0
        trend = "upward" if slope > 0.05 else "downward" if slope < -0.05 else "flat"
        change_pct = ((numeric[-1] - numeric[0]) / abs(numeric[0])) if len(numeric) > 1 and numeric[0] else 0.0
        return {
            "ka_id": self.ka_id,
            "success": True,
            "trend": trend,
            "slope": round(slope, 4),
            "intercept": round(intercept, 4),
            "change_percent": round(change_pct, 4),
            "volatility": round(volatility, 4),
            "points_analyzed": len(numeric),
            "confidence": round(min(0.95, max(0.25, len(numeric) / 10)), 3),
        }

    @staticmethod
    def _numeric_series(series: List[Any]) -> List[float]:
        values = []
        for item in series:
            if isinstance(item, (int, float)):
                values.append(float(item))
            elif isinstance(item, dict):
                value = item.get("value", item.get("y"))
                if isinstance(value, (int, float)):
                    values.append(float(value))
        return values

    @staticmethod
    def _linear_regression(values: List[float]) -> tuple[float, float]:
        if len(values) < 2:
            return 0.0, values[0] if values else 0.0
        xs = list(range(len(values)))
        mean_x = statistics.mean(xs)
        mean_y = statistics.mean(values)
        denominator = sum((x - mean_x) ** 2 for x in xs)
        slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values)) / denominator if denominator else 0.0
        intercept = mean_y - slope * mean_x
        return slope, intercept


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA046TrendAnalysis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-046 Failed: {e}")
        return {"success": False, "error": str(e)}
