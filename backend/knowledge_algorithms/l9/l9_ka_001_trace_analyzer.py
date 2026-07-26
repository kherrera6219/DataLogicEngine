"""L9-KA-001: deterministic integrity checks for the committed L1-L8 trace."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TraceAnalyzerKA:
    """KA for analyzing reasoning trace integrity."""

    KA_ID = "L9-KA-001"
    NAME = "Trace Analyzer"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        trace = inputs.get("trace", {})
        layers = inputs.get("layers", [])
        if not isinstance(trace, dict):
            raise TypeError("trace must be an object")
        if not isinstance(layers, list) or any(
            not isinstance(layer, int) or not 1 <= layer <= 8 for layer in layers
        ):
            raise ValueError("layers must contain only integers from 1 through 8")
        if len(layers) != len(set(layers)):
            raise ValueError("layers must not contain duplicates")

        issues: list[dict[str, Any]] = []

        # Check for missing layers
        expected_layers = set(range(1, 9))
        actual_layers = set(layers)
        missing = expected_layers - actual_layers

        for layer in sorted(missing):
            issues.append(
                {
                    "layer": layer,
                    "type": "missing_layer",
                    "description": f"Layer {layer} not found in trace",
                }
            )

        # Check for empty outputs
        for layer_num in layers:
            layer_key = f"layer{layer_num}"
            if layer_key in trace:
                layer_data = trace[layer_key]
                if not isinstance(layer_data, dict):
                    issues.append(
                        {
                            "layer": layer_num,
                            "type": "invalid_layer_record",
                            "description": f"Layer {layer_num} is not an object",
                        }
                    )
                    continue
                if not layer_data.get("output") and not layer_data.get("result"):
                    issues.append(
                        {
                            "layer": layer_num,
                            "type": "empty_output",
                            "description": f"Layer {layer_num} has empty output",
                        }
                    )

                selected = set(layer_data.get("selected_ka_ids") or [])
                committed = set((layer_data.get("ka_results") or {}).keys())
                forged = sorted(selected - committed)
                if forged:
                    issues.append(
                        {
                            "layer": layer_num,
                            "type": "uncommitted_ka_invocation",
                            "description": (
                                "Selected KA IDs lack committed canonical results"
                            ),
                            "ka_ids": forged,
                        }
                    )

        # Calculate integrity score
        max_issues = len(expected_layers) * 2  # Missing + empty for each layer
        integrity_score = 1.0 - (len(issues) / max(1, max_issues))
        integrity_score = max(0.0, min(1.0, integrity_score))

        logger.info(
            f"L9-KA-001: Analyzed {len(layers)} layers, found {len(issues)} issues"
        )

        return {
            "integrity_score": integrity_score,
            "issues": issues,
            "layers_analyzed": len(layers),
            "trace_complete": not issues,
            "measurement_basis": "committed_layer_and_ka_result_records",
        }


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    return TraceAnalyzerKA({}).execute(inputs)
