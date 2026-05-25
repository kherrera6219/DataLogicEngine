"""Axis 17: FROST-Mode Selector."""

from __future__ import annotations

from typing import Any


class FrostModeAxis:
    """Bridge reasoning tier to FROST depth and TruthCore execution mode."""

    axis_number = 17
    axis_name = "FROST-Mode Selector"
    description = "Maps tier to FROST layer depth and TruthCore mode"

    MODE_BY_TIER = {
        "trivial": {"frost_layer_depth": 2, "truth_engine_mode": "direct"},
        "moderate": {"frost_layer_depth": 4, "truth_engine_mode": "standard"},
        "high_stakes": {"frost_layer_depth": 7, "truth_engine_mode": "regulatory_strict"},
        "extreme": {"frost_layer_depth": 10, "truth_engine_mode": "full_refinement"},
        "autonomous": {"frost_layer_depth": 10, "truth_engine_mode": "governed_agentic"},
    }

    def resolve_context(self, axis_data: Any) -> dict[str, Any]:
        if isinstance(axis_data, dict):
            tier = str(axis_data.get("tier") or axis_data.get("risk_tier") or "moderate").lower()
        else:
            tier = str(axis_data or "moderate").lower()
        tier = tier if tier in self.MODE_BY_TIER else "moderate"
        mode = self.MODE_BY_TIER[tier]
        return {
            "axis": self.axis_number,
            "name": self.axis_name,
            "tier": tier,
            **mode,
            "confidence": 0.9,
        }

    def navigate(self, **kwargs: Any) -> dict[str, Any]:
        return self.resolve_context(kwargs)
