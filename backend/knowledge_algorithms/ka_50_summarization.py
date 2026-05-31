"""
KA-050: Summarization
Purpose: Summarize text or data.
"""
import logging
import re
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA050Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str = ""
    max_length: int = 100
    focus_terms: List[str] = Field(default_factory=list)
    style: str = "paragraph"


class KA050Summarization(KnowledgeAlgorithm):
    input_schema = KA050Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-050"

    def _run_logic(self, input_data: KA050Input) -> Dict[str, Any]:
        text = input_data.text
        max_len = max(40, int(input_data.max_length or 100))
        
        self.log_execution_step("Summarizing", {"len": len(text)})

        sentences = self._split_sentences(text)
        selected = self._select_sentences(sentences, input_data.focus_terms, max_len)
        summary = self._format_summary(selected, input_data.style, max_len)

        return {
            "ka_id": "KA-050",
            "success": True,
            "summary": summary,
            "source_sentence_count": len(sentences),
            "summary_sentence_count": len(selected),
            "compression_ratio": round(len(summary) / len(text), 3) if text else 0.0,
            "method": "extractive_frequency_rank",
        }

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]

    @classmethod
    def _select_sentences(cls, sentences: List[str], focus_terms: List[str], max_len: int) -> List[str]:
        if not sentences:
            return []
        frequencies = cls._term_frequencies(" ".join(sentences))
        focus = {term.lower() for term in focus_terms}
        scored = []
        for index, sentence in enumerate(sentences):
            terms = cls._tokens(sentence)
            term_score = sum(frequencies.get(term, 0) for term in terms)
            focus_score = 2.5 * len(terms & focus)
            position_score = 1.0 if index == 0 else 0.3 if index == len(sentences) - 1 else 0.0
            scored.append((term_score + focus_score + position_score, index, sentence))
        scored.sort(key=lambda item: (-item[0], item[1]))

        selected: List[tuple[int, str]] = []
        current_len = 0
        for _score, index, sentence in scored:
            projected = current_len + len(sentence) + (1 if selected else 0)
            if projected <= max_len or not selected:
                selected.append((index, sentence))
                current_len = projected
            if current_len >= max_len * 0.75:
                break
        selected.sort(key=lambda item: item[0])
        return [sentence for _index, sentence in selected]

    @staticmethod
    def _format_summary(sentences: List[str], style: str, max_len: int) -> str:
        if not sentences:
            return ""
        if style == "bullets":
            summary = "\n".join(f"- {sentence}" for sentence in sentences)
        else:
            summary = " ".join(sentences)
        if len(summary) <= max_len:
            return summary
        trimmed = summary[: max_len + 1].rsplit(" ", 1)[0].rstrip(" ,;:")
        return f"{trimmed}..."

    @classmethod
    def _term_frequencies(cls, text: str) -> Dict[str, int]:
        frequencies: Dict[str, int] = {}
        for token in cls._tokens(text):
            frequencies[token] = frequencies.get(token, 0) + 1
        return frequencies

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stopwords = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was", "were"}
        return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in stopwords}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA050Summarization(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-050 Failed: {e}")
        return {"success": False, "error": str(e)}


