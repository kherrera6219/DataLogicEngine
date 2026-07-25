"""KA-165: deterministic corpus topic-term modeling."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")


class TopicDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1, max_length=200)
    text: str = Field(max_length=1_000_000)
    topic_hint: str = Field(min_length=1, max_length=200)


class KA165Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "documents": [
                        {
                            "document_id": "d1",
                            "text": "audit evidence controls audit",
                            "topic_hint": "governance",
                        }
                    ],
                    "stopwords": ["the"],
                }
            ]
        },
    )

    documents: list[TopicDocument] = Field(min_length=1, max_length=10_000)
    stopwords: list[str] = Field(default_factory=list, max_length=10_000)
    terms_per_topic: int = Field(default=10, ge=1, le=100)


class KA165TopicModeling(KnowledgeAlgorithm):
    """Build auditable topic-term counts using caller-declared topic hints."""

    input_schema = KA165Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-165"

    def _run_logic(self, input_data: KA165Input) -> dict[str, Any]:
        stopwords = {term.casefold() for term in input_data.stopwords}
        counts: dict[str, Counter[str]] = defaultdict(Counter)
        members: dict[str, list[str]] = defaultdict(list)
        for item in sorted(input_data.documents, key=lambda row: row.document_id):
            members[item.topic_hint].append(item.document_id)
            counts[item.topic_hint].update(
                token.casefold()
                for token in TOKEN_RE.findall(item.text)
                if token.casefold() not in stopwords
            )
        topics = []
        for topic_id in sorted(counts):
            ranked = sorted(
                counts[topic_id].items(), key=lambda row: (-row[1], row[0])
            )[: input_data.terms_per_topic]
            topics.append(
                {
                    "topic_id": topic_id,
                    "document_ids": members[topic_id],
                    "terms": [
                        {"term": term, "count": count} for term, count in ranked
                    ],
                }
            )
        return {
            "success": True,
            "status": "topics_modeled",
            "topics": topics,
            "method": "hinted_term_frequency",
            "deterministic": True,
            "limitations": (
                "This transparent model uses caller-supplied topic hints and term "
                "frequency; it does not infer latent semantic topics."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA165TopicModeling(context).run(context)
