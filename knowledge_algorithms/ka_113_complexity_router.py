"""
KA-113: Complexity Router
Purpose: Route based on complexity.
Delegates to SDK handler.
"""
import logging
from typing import Dict, Any
import importlib
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA113ComplexityRouter(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.sdk_module = "ukg_sdk.ka.builtins"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log_execution_step("Delegating to SDK", {"module": self.sdk_module})
        try:
            mod = importlib.import_module(self.sdk_module)
            func = getattr(mod, "ka_113_router", None)
            
            if not func:
                 return {"success": True, "output": {"tier": "T1", "note": "SDK Handler not found"}}
            
            from ukg_sdk.ka.executor import KAExecutionContext
            ctx = KAExecutionContext(input=input_data, logger=logger)
            result = func(ctx)
            
            return {
                "ka_id": "KA-113",
                "success": result.ok,
                "output": result.output,
                "routing_decision": result.output
            }
        except Exception as e:
            logger.error(f"KA-113 SDK Delegation Failed: {e}")
            return {"success": False, "error": str(e)}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA113ComplexityRouter(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-113 Wrapper Failed: {e}")
        return {"success": False, "error": str(e)}
