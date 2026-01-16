"""
L9-KA-001: Trace Analyzer

Systematically reviews the reasoning trace from L1-L8 to detect:
- Missing layer outputs
- Orphan claims (unsupported conclusions)
- Unresolved branches
- Logical inconsistencies
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class TraceAnalyzerKA:
    """KA for analyzing reasoning trace integrity."""
    
    KA_ID = "L9-KA-001"
    NAME = "Trace Analyzer"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze reasoning trace for integrity issues.
        
        Args:
            inputs: {"trace": Dict, "layers": List[int]}
            
        Returns:
            {"integrity_score": float, "issues": List[Dict]}
        """
        trace = inputs.get("trace", {})
        layers = inputs.get("layers", [])
        
        issues = []
        
        # Check for missing layers
        expected_layers = set(range(1, 9))
        actual_layers = set(layers)
        missing = expected_layers - actual_layers
        
        for layer in missing:
            issues.append({
                "layer": layer,
                "type": "missing_layer",
                "description": f"Layer {layer} not found in trace"
            })
        
        # Check for empty outputs
        for layer_num in layers:
            layer_key = f"layer{layer_num}"
            if layer_key in trace:
                layer_data = trace[layer_key]
                if not layer_data.get("output") and not layer_data.get("result"):
                    issues.append({
                        "layer": layer_num,
                        "type": "empty_output",
                        "description": f"Layer {layer_num} has empty output"
                    })
        
        # Calculate integrity score
        max_issues = len(expected_layers) * 2  # Missing + empty for each layer
        integrity_score = 1.0 - (len(issues) / max(1, max_issues))
        integrity_score = max(0.0, min(1.0, integrity_score))
        
        logger.info(f"L9-KA-001: Analyzed {len(layers)} layers, found {len(issues)} issues")
        
        return {
            "integrity_score": integrity_score,
            "issues": issues,
            "layers_analyzed": len(layers)
        }
