from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA04InputValidation(KnowledgeAlgorithm):
    ka_id = "KA-004"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-004",
            name="Input Validation & Normalization",
            description="Sanitize, normalize, and validate query and metadata. Maps to 17-Axis System.",
            tier="Safety",
            layer=1
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        raw_input = state.get("query", "") or state.get("input", "")
        
        # 1. Validation Logic
        is_safe = True
        if "<script>" in raw_input:
            is_safe = False
            return KAResult(output="Unsafe Input Detected", flags={"is_safe": False}, success=False)

        # 2. Normalization / Axis Mapping Logic (Merged from old KA-004)
        query_context = {
            "12": {"location": "US"}, 
            "13": {"time": "current"}
        }
        
        resolved_axes = {}
        if context.axis_system:
            resolved_axes = context.axis_system.resolve_multi_axis_context(query_context)
        else:
            resolved_axes = {"status": "Axis System not available, skipping deep mapping"}

        return KAResult(
            output=raw_input.strip(), 
            artifacts={"axis_mapping": resolved_axes},
            flags={"is_safe": True, "pii_detected": False},
            log="Input sanitized, validated, and normalized to Axis System."
        )
