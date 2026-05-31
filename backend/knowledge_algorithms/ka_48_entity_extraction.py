"""
KA-048: Entity Extraction
Purpose: Extract named entities from text.
"""
import logging
import re
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA048Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str = ""

class KA048EntityExtraction(KnowledgeAlgorithm):
    input_schema = KA048Input
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def _run_logic(self, input_data: KA048Input) -> Dict[str, Any]:
        text = input_data.text
        
        self.log_execution_step("Extracting Entities", {})
        
        entities = self._extract_entities(text)
                
        return {
            "ka_id": "KA-048",
            "success": True,
            "entities": entities,
            "entity_count": len(entities),
        }

    @staticmethod
    def _extract_entities(text: str) -> List[Dict[str, Any]]:
        patterns = [
            ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
            ("URL", re.compile(r"\bhttps?://[^\s)]+", re.IGNORECASE)),
            ("DATE", re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")),
            ("MONEY", re.compile(r"\$\s?\d+(?:,\d{3})*(?:\.\d{2})?")),
            ("PERCENT", re.compile(r"\b\d+(?:\.\d+)?%")),
            ("REGULATION", re.compile(r"\b(?:FAR|DFARS|HIPAA|SOX|GDPR|NIST|ISO)\b(?:[-\s]?\d+(?:\.\d+)*)?", re.IGNORECASE)),
            ("ORG", re.compile(r"\b[A-Z][A-Za-z&.-]+(?:\s+[A-Z][A-Za-z&.-]+)*(?:\s+(?:Inc|LLC|Corp|Corporation|Agency|Department|Office|Authority))\b")),
            ("PERSON_OR_PLACE", re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")),
        ]
        seen: set[tuple[int, int, str]] = set()
        entities: List[Dict[str, Any]] = []
        for entity_type, pattern in patterns:
            for match in pattern.finditer(text):
                key = (match.start(), match.end(), entity_type)
                if key in seen:
                    continue
                seen.add(key)
                entities.append(
                    {
                        "text": match.group(0).strip(".,;:"),
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.9 if entity_type in {"EMAIL", "URL", "DATE", "MONEY", "PERCENT"} else 0.72,
                    }
                )
        entities.sort(key=lambda item: (item["start"], item["end"], item["type"]))
        return entities

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA048EntityExtraction(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-048 Failed: {e}")
        return {"success": False, "error": str(e)}


