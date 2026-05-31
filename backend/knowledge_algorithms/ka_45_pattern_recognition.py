"""
KA-045: Pattern Recognition
Purpose: Identify recurring patterns in data.
"""
import logging
from collections import Counter
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA045Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    stream: List[Any] = Field(default_factory=list)
    min_repetitions: int = 2
    window_size: int = 3


class KA045PatternRecognition(KnowledgeAlgorithm):
    input_schema = KA045Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-045"

    def _run_logic(self, input_data: KA045Input) -> Dict[str, Any]:
        data_stream = input_data.stream
        min_repetitions = max(2, self._safe_int(input_data.min_repetitions, 2))
        window_size = max(2, self._safe_int(input_data.window_size, 3))

        self.log_execution_step("Recognizing Patterns", {"len": len(data_stream)})

        patterns = []
        patterns.extend(self._repeated_values(data_stream, min_repetitions))
        patterns.extend(self._repeated_windows(data_stream, window_size, min_repetitions))
        patterns.extend(self._monotonic_runs(data_stream))
        return {
            "ka_id": self.ka_id,
            "success": True,
            "patterns": patterns,
            "pattern_count": len(patterns),
            "method": "repeat_window_monotonic_detection",
        }

    @staticmethod
    def _repeated_values(stream: List[Any], min_repetitions: int) -> List[Dict[str, Any]]:
        counts = Counter(map(str, stream))
        return [
            {"type": "repeated_value", "value": value, "count": count, "confidence": min(0.95, count / max(1, len(stream)))}
            for value, count in counts.items()
            if count >= min_repetitions
        ]

    @staticmethod
    def _repeated_windows(stream: List[Any], window_size: int, min_repetitions: int) -> List[Dict[str, Any]]:
        if len(stream) < window_size * min_repetitions:
            return []
        windows = Counter(tuple(map(str, stream[index:index + window_size])) for index in range(len(stream) - window_size + 1))
        return [
            {"type": "repeated_sequence", "sequence": list(window), "count": count, "confidence": min(0.95, 0.4 + count * 0.15)}
            for window, count in windows.items()
            if count >= min_repetitions
        ]

    @staticmethod
    def _monotonic_runs(stream: List[Any]) -> List[Dict[str, Any]]:
        numeric = [float(item) for item in stream if isinstance(item, (int, float))]
        if len(numeric) < 3:
            return []
        runs = []
        start = 0
        direction = 0
        for index in range(1, len(numeric)):
            delta = numeric[index] - numeric[index - 1]
            current_direction = 1 if delta > 0 else -1 if delta < 0 else direction
            if direction == 0:
                direction = current_direction
            elif current_direction and current_direction != direction:
                if index - start >= 3:
                    runs.append({"type": "monotonic_run", "direction": "increasing" if direction > 0 else "decreasing", "length": index - start, "confidence": 0.8})
                start = index - 1
                direction = current_direction
        if len(numeric) - start >= 3 and direction:
            runs.append({"type": "monotonic_run", "direction": "increasing" if direction > 0 else "decreasing", "length": len(numeric) - start, "confidence": 0.8})
        return runs

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA045PatternRecognition(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-045 Failed: {e}")
        return {"success": False, "error": str(e)}
