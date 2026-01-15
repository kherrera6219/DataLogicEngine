"""
SDK Delegate for ka_113_query_analysis__complexity_router.py
Delegates execution to ukg_sdk.ka.handlers.ka_113
"""
import logging
from typing import Dict, Any
import importlib

logger = logging.getLogger(__name__)

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Delegate to SDK"""
    try:
        module_name, func_name = "ukg_sdk.ka.handlers.ka_113".rsplit(".", 1)
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        
        # SDK handlers often take "request" dict aka context
        result = func(context)
        
        # Ensure result has status
        if "status" not in result:
             result["status"] = "success"
             
        return {
            "success": True,
            "output": result
        }
    except Exception as e:
        logger.error(f"Failed to delegate to SDK ukg_sdk.ka.handlers.ka_113: {e}")
        return {
            "success": False,
            "error": str(e)
        }
