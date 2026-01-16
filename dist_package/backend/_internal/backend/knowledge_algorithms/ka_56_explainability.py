"""
KA-056: Explainability/XAI
Purpose: Generate explanations for reasoning path.
Delegates to SDK handler.
"""
import logging
from typing import Dict, Any
import importlib
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA056Explainability(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.sdk_module = "ukg_sdk.ka.builtins"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log_execution_step("Delegating to SDK", {"module": self.sdk_module})
        try:
            mod = importlib.import_module(self.sdk_module)
            # Find generic entry point from builtins
            func = getattr(mod, "ka_056_explain", None)
            
            if not func:
                 # Fallback
                 return {"success": True, "explanation": "SDK Handler ka_056_explain not found"}
            
            # SDK builtins use KAExecutionContext
            # We mock it or adapt
            from ukg_sdk.ka.executor import KAExecutionContext
            ctx = KAExecutionContext(input=input_data, logger=logger)
            result = func(ctx) # Returns KAExecutionResult
            
            return {
                "ka_id": "KA-056",
                "success": result.ok,
                "output": result.output,
                "explanation": result.output.get("explainability", {})
            }
        except Exception as e:
            logger.error(f"KA-056 SDK Delegation Failed: {e}")
            return {"success": False, "error": str(e)}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA056Explainability(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-056 Wrapper Failed: {e}")
        return {"success": False, "error": str(e)}
