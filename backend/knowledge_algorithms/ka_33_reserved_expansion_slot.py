"""KA-033: Extension slot for controlled experimental KA payloads."""
import logging
from typing import Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA033Input(BaseModel):
    model_config = ConfigDict(extra="allow")

    payload: Dict[str, Any] = Field(default_factory=dict)
    operation: str = "echo"

class KA033ExtensionSlot(KnowledgeAlgorithm):
    input_schema = KA033Input
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def _run_logic(self, input_data: KA033Input) -> Dict[str, Any]:
        payload = input_data.payload or {
            key: value
            for key, value in input_data.model_dump().items()
            if key not in {"payload", "operation"}
        }
        operation = input_data.operation.lower().strip()
        payload_keys = sorted(payload)
        payload_types = {key: type(value).__name__ for key, value in payload.items()}
        result_payload: Dict[str, Any] = {
            "payload": payload,
            "payload_keys": payload_keys,
            "payload_types": payload_types,
        }
        if operation == "summarize":
            result_payload["summary"] = {
                "field_count": len(payload),
                "empty_fields": [key for key, value in payload.items() if value in (None, "", [], {})],
            }
        elif operation != "echo":
            return {
                "ka_id": "KA-033",
                "success": False,
                "error": f"Unsupported extension operation: {operation}",
                "supported_operations": ["echo", "summarize"],
            }
        return {
            "ka_id": "KA-033",
            "success": True,
            "ka_name": "Extension Slot",
            "operation": operation,
            "result_payload": result_payload,
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    algo = KA033ExtensionSlot(context)
    return algo.run(context)
