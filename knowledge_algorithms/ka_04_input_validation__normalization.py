"""
KA-004: Input Validation & Normalization
Purpose: Sanitize, normalize, and validate query and metadata.
Delegates to SDK handler.
"""
import logging
from typing import Dict, Any
import importlib
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA004InputValidation(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.sdk_module = "ukg_sdk.ka.handlers.ka_004"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.log_execution_step("Delegating to SDK", {"module": self.sdk_module})
        try:
            mod = importlib.import_module(self.sdk_module)
            # Use run if exists, else assume module call
            if hasattr(mod, "run"):
                result = mod.run(input_data)
            else:
                # Some handlers in SDK (KA-004) might be a function `ka_004(request)`
                func = getattr(mod, "ka_004", None)
                if not func:
                     func = getattr(mod, "calculate_validation_result", None) # specific to ka004 logic
                if not func:
                    raise ImportError("Cannot find entry point in SDK KA-004")
                
                result = func(input_data)

            return {
                "ka_id": "KA-004",
                "success": True,
                "sdk_response": result,
                # Flatten result if needed
                "normalized_query": result.get("normalized_query", input_data.get("query")),
                "is_valid": result.get("is_valid", False)
            }
        except Exception as e:
            logger.error(f"KA-004 SDK Delegation Failed: {e}")
            return {"success": False, "error": str(e)}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA004InputValidation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-004 Wrapper Failed: {e}")
        return {"success": False, "error": str(e)}
