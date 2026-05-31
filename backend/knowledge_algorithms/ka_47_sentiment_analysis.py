"""
KA-047: Sentiment Analysis
Purpose: Analyze emotional tone and sentiment.
"""
import logging
import re
from typing import Any, Dict

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class KA047Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str = ""


class KA047SentimentAnalysis(KnowledgeAlgorithm):
    input_schema = KA047Input
    POSITIVE = {
        "good", "great", "excellent", "strong", "success", "successful", "stable", "safe", "improved",
        "clear", "ready", "healthy", "reliable", "fast", "resolved", "positive",
    }
    NEGATIVE = {
        "bad", "terrible", "poor", "failed", "failure", "risk", "risky", "blocked", "broken", "slow",
        "outage", "degraded", "critical", "unsafe", "error", "negative", "problem",
    }
    INTENSIFIERS = {"very", "extremely", "highly", "severely", "critical"}
    NEGATORS = {"not", "never", "no", "without"}

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-047"

    def _run_logic(self, input_data: KA047Input) -> Dict[str, Any]:
        text = input_data.text or str(input_data.model_dump().get("query", ""))
        self.log_execution_step("Analyzing Sentiment", {"len": len(text)})

        tokens = re.findall(r"[a-z']+", text.lower())
        hits = []
        raw_score = 0.0
        for index, token in enumerate(tokens):
            polarity = 1 if token in self.POSITIVE else -1 if token in self.NEGATIVE else 0
            if not polarity:
                continue
            window = tokens[max(0, index - 3):index]
            if any(item in self.NEGATORS for item in window):
                polarity *= -1
            weight = 1.5 if any(item in self.INTENSIFIERS for item in window) else 1.0
            raw_score += polarity * weight
            hits.append({"token": token, "polarity": polarity, "weight": weight, "position": index})

        normalized = max(-1.0, min(1.0, raw_score / max(3.0, len(tokens) ** 0.5)))
        sentiment = "positive" if normalized > 0.15 else "negative" if normalized < -0.15 else "neutral"
        return {
            "ka_id": self.ka_id,
            "success": True,
            "sentiment": sentiment,
            "score": round(normalized, 4),
            "evidence": hits,
            "token_count": len(tokens),
            "confidence": round(min(0.95, 0.45 + min(len(hits), 5) * 0.1), 3),
        }


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA047SentimentAnalysis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-047 Failed: {e}")
        return {"success": False, "error": str(e)}
