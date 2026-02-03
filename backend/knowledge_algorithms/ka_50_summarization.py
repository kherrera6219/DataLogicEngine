"""
KA-050: Summarization
Purpose: Summarize text or data.
"""
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA050Input(BaseModel):
    class Config:
        extra = 'allow'
class KA050Summarization(KnowledgeAlgorithm):
    input_schema = KA050Input
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def _run_logic(self, input_data: KA050Input) -> Dict[str, Any]:
        input_dict = input_data.model_dump()
        """
        Summarize content.
        """
        text = input_dict.get("text", "")
        max_len = input_dict.get("max_length", 100)
        
        self.log_execution_step("Summarizing", {"len": len(text)})
        
        summary = text[:max_len] + "..." if len(text) > max_len else text
            
        return {
            "ka_id": "KA-050",
            "success": True,
            "summary": summary
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA050Summarization(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-050 Failed: {e}")
        return {"success": False, "error": str(e)}
