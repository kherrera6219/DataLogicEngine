"""
KA-049: Relation Extraction
Purpose: Extract relationships between entities.
"""

import logging
import re
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA049Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str = ""
    entities: List[Any] = Field(default_factory=list)


class KA049RelationExtraction(KnowledgeAlgorithm):
    input_schema = KA049Input
    RELATION_PATTERNS = [
        (
            "owns",
            re.compile(
                r"(?P<s>[\w\s&.-]+?)\s+(?:owns|owned by|controls)\s+(?P<o>[\w\s&.-]+)",
                re.I,
            ),
        ),
        (
            "works_for",
            re.compile(
                r"(?P<s>[\w\s&.-]+?)\s+(?:works for|employed by|reports to)\s+(?P<o>[\w\s&.-]+)",
                re.I,
            ),
        ),
        (
            "located_in",
            re.compile(
                r"(?P<s>[\w\s&.-]+?)\s+(?:located in|based in|operates in)\s+(?P<o>[\w\s&.-]+)",
                re.I,
            ),
        ),
        (
            "depends_on",
            re.compile(
                r"(?P<s>[\w\s&.-]+?)\s+(?:depends on|requires|uses)\s+(?P<o>[\w\s&.-]+)",
                re.I,
            ),
        ),
        (
            "complies_with",
            re.compile(
                r"(?P<s>[\w\s&.-]+?)\s+(?:complies with|must follow|is governed by)\s+(?P<o>[\w\s&.-]+)",
                re.I,
            ),
        ),
    ]

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-049"

    def _run_logic(self, input_data: KA049Input) -> Dict[str, Any]:
        entities = [self._entity_text(entity) for entity in input_data.entities]
        text = input_data.text or " ".join(entities)
        self.log_execution_step(
            "Extracting Relations",
            {"entity_count": len(entities), "text_len": len(text)},
        )

        relations = self._pattern_relations(text)
        relations.extend(self._proximity_relations(text, entities))
        deduped = self._dedupe(relations)
        return {
            "ka_id": self.ka_id,
            "success": True,
            "relations": deduped,
            "relation_count": len(deduped),
            "method": "pattern_and_proximity_relation_extraction",
            "relations_persisted": False,
            "deterministic": True,
            "limitations": (
                "Pattern matches and co-occurrence are candidate relations and "
                "do not establish semantic or causal truth."
            ),
        }

    @classmethod
    def _pattern_relations(cls, text: str) -> List[Dict[str, Any]]:
        relations = []
        for predicate, pattern in cls.RELATION_PATTERNS:
            for match in pattern.finditer(text):
                subject = cls._clean(match.group("s"))
                obj = cls._clean(match.group("o"))
                if subject and obj and subject != obj:
                    relations.append(
                        {
                            "subject": subject,
                            "predicate": predicate,
                            "object": obj,
                            "confidence": 0.82,
                            "source": "pattern",
                        }
                    )
        return relations

    @classmethod
    def _proximity_relations(
        cls, text: str, entities: List[str]
    ) -> List[Dict[str, Any]]:
        relations = []
        lowered = text.lower()
        for left_index, subject in enumerate(entities):
            for obj in entities[left_index + 1 :]:
                s_pos = lowered.find(subject.lower())
                o_pos = lowered.find(obj.lower())
                if s_pos < 0 or o_pos < 0:
                    continue
                distance = abs(s_pos - o_pos)
                if distance <= 120:
                    relations.append(
                        {
                            "subject": subject,
                            "predicate": "co_occurs_with",
                            "object": obj,
                            "confidence": round(max(0.35, 0.75 - distance / 300), 3),
                            "source": "proximity",
                        }
                    )
        return relations

    @staticmethod
    def _entity_text(entity: Any) -> str:
        if isinstance(entity, dict):
            return str(
                entity.get("text") or entity.get("name") or entity.get("id") or entity
            )
        return str(entity)

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" .,;:")

    @staticmethod
    def _dedupe(relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for relation in relations:
            key = (
                relation["subject"].lower(),
                relation["predicate"],
                relation["object"].lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(relation)
        return deduped


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA049RelationExtraction(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-049 Failed: {e}")
        return {"success": False, "error": str(e)}
