"""
KA-005: Query Classification
Purpose: Identify query intent and domain using local rules and SDK delegation.
"""
import logging
import json
import os
from typing import Dict, Any, List, Tuple
import importlib
logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA005Input(BaseModel):
    query: str = Field(..., description="The query to classify")

class KA005QueryClassification(KnowledgeAlgorithm):
    """
    KA-005: Classifies queries into logical categories.
    """
    input_schema = KA005Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-005"
        self.config = self._load_config()
        self.sdk_module = "ukg_sdk.ka.handlers.ka_005"

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_05_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA005Input) -> Dict[str, Any]:
        query = input_data.query
        
        # 1. Local Rule-based Classification
        local_category, local_conf = self._perform_local_classification(query)
        
        # 2. SDK Delegation
        self.log_execution_step("Delegating to SDK for refined classification", {"query": query})
        sdk_result = self._delegate_to_sdk({"query": query})
        
        final_category = sdk_result.get("category", local_category)
        final_conf = sdk_result.get("confidence", local_conf)
        
        return {
            "success": True,
            "category": final_category,
            "confidence": final_conf,
            "metadata": {
                "local_guess": local_category,
                "sdk_response": sdk_result
            }
        }

    def _perform_local_classification(self, query: str) -> Tuple[str, float]:
        if not query:
            return "GENERAL", 0.0
            
        categories = self.config.get("categories", {})
        query_lower = query.lower()
        
        best_cat = self.config.get("fallback_category", "GENERAL")
        best_conf = categories.get(best_cat, {}).get("default_confidence", 0.5)
        
        for cat_name, info in categories.items():
            keywords = info.get("keywords", [])
            for kw in keywords:
                if kw in query_lower:
                    return cat_name, info.get("default_confidence", 0.8)
        return best_cat, best_conf

    async def _delegate_to_sdk_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of SDK delegation."""
        return await self._classify_via_gateway(data.get("query", ""))

    def _delegate_to_sdk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replacement for SDK delegation: Use LLMGateway directly.
        """
        import asyncio
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop and running_loop.is_running():
            # Running a nested loop here would fail; return a safe fallback.
            logger.warning("KA-005 delegation skipped because an event loop is already running")
            return {}

        return asyncio.run(self._classify_via_gateway(data.get("query", "")))

    async def _classify_via_gateway(self, query: str) -> Dict[str, Any]:
        """
        Use LLMGateway (Fast Chat Tier) to classify query.
        """
        try:
             # Lazy import
            from backend.llm_gateway.gateway import get_gateway
            gateway = get_gateway()
            
            prompt = f"""
            Classify the following user query into a domain category.
            Query: "{query}"
            
            Return ONLY a JSON object:
            {{
                "category": "ACCESS_CONTROL|FINANCE|COMPLIANCE|GENERAL|HR|IT_SUPPORT",
                "confidence": 0.0-1.0
            }}
            """
            
            result = await gateway.process(
                prompt=prompt,
                tier="fast_chat", # Cost effective for high volume
                system_instruction="You are a precise semantic classifier.",
                metadata={"ka_id": "KA-005"}
            )
            
            if result and result.content:
                import json
                try:
                    content = result.content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    return json.loads(content.strip())
                except json.JSONDecodeError:
                    pass
            
            return {}
        except Exception as e:
            logger.warning(f"KA-005 Gateway classification failed: {e}")
            return {}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA005QueryClassification(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-005 Failed: {e}")
        return {"success": False, "error": str(e)}
