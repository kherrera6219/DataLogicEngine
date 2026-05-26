"""
KA-036: Complexity Estimator
Purpose: Estimate problem complexity (time/space/cognitive).
"""
import logging
import math
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA036Input(BaseModel):
    model_config = ConfigDict(extra="allow")
class KA036ComplexityEstimator(KnowledgeAlgorithm):
    input_schema = KA036Input
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def _run_logic(self, input_data: KA036Input) -> Dict[str, Any]:
        input_dict = input_data.model_dump()
        """
        Estimate complexity.
        """
        problem = input_dict.get("problem", "")
        target_ka_id = input_dict.get("target_ka_id") or input_dict.get("ka_id")
        
        self.log_execution_step("Estimating Complexity", {})
        
        score = 1
        if len(problem) > 100:
            score = 5

        latency_sample = self._recent_latencies(target_ka_id)
        p95_latency_ms = self._percentile(latency_sample, 95) if latency_sample else None
        if p95_latency_ms is not None:
            if p95_latency_ms >= 5000:
                score = max(score, 5)
            elif p95_latency_ms >= 1500:
                score = max(score, 3)
        
        return {
            "ka_id": "KA-036",
            "success": True,
            "complexity_score": score,
            "category": "polynomial" if score < 3 else "exponential",
            "latency_baseline": {
                "target_ka_id": target_ka_id,
                "sample_size": len(latency_sample),
                "p95_latency_ms": p95_latency_ms,
                "source": "ukg_ka_executions_last_100",
            },
        }

    @staticmethod
    def _recent_latencies(target_ka_id: str | None = None) -> List[int]:
        try:
            from extensions import db
            from models import KAExecution

            query = db.session.query(KAExecution).filter(KAExecution.execution_time_ms.isnot(None))
            if target_ka_id:
                query = query.filter(KAExecution.ka_id == target_ka_id)
            rows = (
                query.order_by(KAExecution.completed_at.desc())
                .limit(100)
                .all()
            )
            return [int(row.execution_time_ms) for row in rows if row.execution_time_ms is not None]
        except Exception as exc:
            logger.debug(f"KA-036 latency baseline unavailable: {exc}")
            return []

    @staticmethod
    def _percentile(values: List[int], percentile: int) -> int | None:
        if not values:
            return None
        sorted_values = sorted(values)
        rank = math.ceil((percentile / 100) * len(sorted_values)) - 1
        rank = max(0, min(rank, len(sorted_values) - 1))
        return sorted_values[rank]

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA036ComplexityEstimator(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-036 Failed: {e}")
        return {"success": False, "error": str(e)}


