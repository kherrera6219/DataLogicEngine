"""
KA-044: Analogical Mapping
Purpose: Map concepts between domains via analogy.
"""
import logging
import re
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA044Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    source: Any = ""
    target_domain: str = ""
    target_candidates: List[Any] = Field(default_factory=list)
    source_attributes: Dict[str, Any] = Field(default_factory=dict)


class KA044AnalogicalMapping(KnowledgeAlgorithm):
    input_schema = KA044Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-044"

    def _run_logic(self, input_data: KA044Input) -> Dict[str, Any]:
        source_name, source_attrs = self._normalize_concept(input_data.source)
        source_attrs = {**source_attrs, **input_data.source_attributes}
        candidates = input_data.target_candidates or [{"name": input_data.target_domain, "attributes": {}}]

        self.log_execution_step("Mapping Analogy", {"source": source_name, "target": input_data.target_domain})

        mappings = [self._score_mapping(source_name, source_attrs, candidate) for candidate in candidates]
        mappings.sort(key=lambda item: (-item["score"], item["target"]))
        best = mappings[0] if mappings else {"target": input_data.target_domain, "score": 0.0, "shared_structure": []}
        strength = "strong" if best["score"] >= 0.7 else "medium" if best["score"] >= 0.25 else "weak"
        return {
            "ka_id": self.ka_id,
            "success": True,
            "analogy": f"{source_name} maps to {best['target']} in {input_data.target_domain or best['target']}",
            "strength": strength,
            "mappings": mappings,
            "method": "attribute_and_token_overlap",
        }

    @classmethod
    def _score_mapping(cls, source_name: str, source_attrs: Dict[str, Any], candidate: Any) -> Dict[str, Any]:
        target_name, target_attrs = cls._normalize_concept(candidate)
        shared_keys = sorted(set(source_attrs) & set(target_attrs))
        matching_values = [key for key in shared_keys if str(source_attrs.get(key)).lower() == str(target_attrs.get(key)).lower()]
        token_overlap = cls._tokens(source_name) & cls._tokens(target_name)
        denominator = max(1, len(set(source_attrs) | set(target_attrs)) + len(cls._tokens(source_name)))
        score = (len(shared_keys) * 0.4 + len(matching_values) * 0.4 + len(token_overlap) * 0.2) / denominator
        return {
            "source": source_name,
            "target": target_name,
            "score": round(min(1.0, score), 4),
            "shared_structure": shared_keys,
            "matching_values": matching_values,
            "token_overlap": sorted(token_overlap),
        }

    @staticmethod
    def _normalize_concept(value: Any) -> tuple[str, Dict[str, Any]]:
        if isinstance(value, dict):
            name = str(value.get("name") or value.get("label") or value.get("id") or value)
            attrs = value.get("attributes") if isinstance(value.get("attributes"), dict) else {
                key: item for key, item in value.items() if key not in {"name", "label", "id"}
            }
            return name, attrs
        return str(value), {}

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA044AnalogicalMapping(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-044 Failed: {e}")
        return {"success": False, "error": str(e)}
