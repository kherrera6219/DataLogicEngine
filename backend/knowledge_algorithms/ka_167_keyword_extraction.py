"""KA-167: deterministic corpus keyword extraction."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")


class KeywordDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1, max_length=200)
    text: str = Field(max_length=1_000_000)


class KA167Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "documents": [
                        {"document_id": "d1", "text": "audit evidence audit"},
                        {"document_id": "d2", "text": "security evidence"},
                    ],
                    "keywords_per_document": 2,
                }
            ]
        },
    )

    documents: list[KeywordDocument] = Field(min_length=1, max_length=10_000)
    stopwords: list[str] = Field(default_factory=list, max_length=10_000)
    keywords_per_document: int = Field(default=10, ge=1, le=100)


class KA167KeywordExtraction(KnowledgeAlgorithm):
    """Rank per-document terms with deterministic TF-IDF."""

    input_schema = KA167Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-167"

    def _run_logic(self, input_data: KA167Input) -> dict[str, Any]:
        stopwords = {term.casefold() for term in input_data.stopwords}
        token_counts = {}
        document_frequency: Counter[str] = Counter()
        for item in input_data.documents:
            counts = Counter(
                token.casefold()
                for token in TOKEN_RE.findall(item.text)
                if token.casefold() not in stopwords
            )
            token_counts[item.document_id] = counts
            document_frequency.update(counts)
        total_documents = len(input_data.documents)
        results = []
        for item in sorted(input_data.documents, key=lambda row: row.document_id):
            counts = token_counts[item.document_id]
            scores = [
                (
                    term,
                    count
                    * (math.log((1 + total_documents) / (1 + document_frequency[term])) + 1),
                )
                for term, count in counts.items()
            ]
            scores.sort(key=lambda row: (-row[1], row[0]))
            results.append(
                {
                    "document_id": item.document_id,
                    "keywords": [
                        {"term": term, "score": round(score, 8)}
                        for term, score in scores[: input_data.keywords_per_document]
                    ],
                }
            )
        return {
            "success": True,
            "status": "keywords_extracted",
            "documents": results,
            "method": "tf_idf",
            "deterministic": True,
            "limitations": (
                "Token-frequency ranking does not resolve synonyms, phrases, or "
                "semantic importance beyond the supplied corpus."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA167KeywordExtraction(context).run(context)
