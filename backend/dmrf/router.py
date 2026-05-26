"""17-axis DMRF routing."""

from __future__ import annotations

from typing import Any

from core.axes.axis17_frost_mode import FrostModeAxis

from .models import AxisVector


class DMRFRouter:
    """Resolve a compact, SQLite-safe 17-axis vector for a query."""

    def __init__(self, axis_system: Any | None = None):
        self.axis_system = axis_system
        self.frost_axis = FrostModeAxis()

    def route(
        self,
        query: str,
        *,
        tier: str = "moderate",
        context: dict[str, Any] | None = None,
    ) -> AxisVector:
        context = context or {}
        q = query.lower()
        domain = self._domain(q, context)
        sector = self._sector(q, context)
        risk = self._risk(q, context)
        axis17 = self.frost_axis.resolve_context({"tier": tier})

        axes: dict[str, Any] = {
            "1": {"name": "Pillar Level System", "value": domain, "confidence": 0.78},
            "2": {"name": "Sector of Industry", "value": sector, "confidence": 0.76},
            "3": {"name": "Honeycomb System", "bridges": [domain, sector], "confidence": 0.70},
            "4": {"name": "Branch System", "value": context.get("branch") or domain, "confidence": 0.70},
            "5": {"name": "Node System", "value": "interdisciplinary", "confidence": 0.65},
            "6": {"name": "Octopus Node", "value": "multi_regulatory" if risk != "standard" else "standard", "confidence": 0.72},
            "7": {"name": "Spiderweb Node", "value": "constraint_mesh", "confidence": 0.72},
            "8": {"name": "Knowledge Expert", "persona_type": "knowledge", "confidence": 0.80},
            "9": {"name": "Sector Expert", "persona_type": "sector", "confidence": 0.80},
            "10": {"name": "Regulatory Expert", "persona_type": "regulatory", "confidence": 0.80},
            "11": {"name": "Compliance Expert", "persona_type": "compliance", "confidence": 0.80},
            "12": {"name": "Location", "value": context.get("jurisdiction") or "global", "confidence": 0.68},
            "13": {"name": "Temporal", "value": context.get("timeframe") or "current", "confidence": 0.68},
            "14": {"name": "Acquisition Lifecycle", "value": context.get("acquisition_stage") or "analysis", "confidence": 0.66},
            "15": {"name": "Risk & Threat Context", "value": risk, "confidence": 0.82},
            "16": {"name": "Ethics, Trust & Criticality", "value": "high" if tier in {"high_stakes", "extreme", "autonomous"} else "standard", "confidence": 0.78},
            "17": axis17,
        }
        active_axes = list(range(1, 18))
        confidence = round(sum(float(item.get("confidence", 0.7)) for item in axes.values()) / 17, 4)
        return AxisVector(
            axes=axes,
            confidence=confidence,
            active_axes=active_axes,
            frost_layer_depth=int(axis17["frost_layer_depth"]),
            truth_engine_mode=str(axis17["truth_engine_mode"]),
        )

    @staticmethod
    def _domain(query: str, context: dict[str, Any]) -> str:
        if context.get("domain"):
            return str(context["domain"])
        if any(term in query for term in ("hipaa", "health", "clinical", "patient")):
            return "healthcare"
        if any(term in query for term in ("sox", "finance", "bank", "payment")):
            return "finance"
        if any(term in query for term in ("legal", "contract", "regulation", "compliance")):
            return "legal"
        return "general"

    @staticmethod
    def _sector(query: str, context: dict[str, Any]) -> str:
        if context.get("sector"):
            return str(context["sector"])
        if "software" in query or "ai" in query:
            return "technology"
        if "hospital" in query or "patient" in query:
            return "healthcare"
        if "bank" in query or "payment" in query:
            return "financial_services"
        return "cross_industry"

    @staticmethod
    def _risk(query: str, context: dict[str, Any]) -> str:
        if context.get("risk_domain"):
            return str(context["risk_domain"])
        if any(term in query for term in ("safety", "patient", "clinical", "medical")):
            return "healthcare"
        if any(term in query for term in ("financial", "payment", "sox", "bank")):
            return "finance"
        if any(term in query for term in ("legal", "regulatory", "compliance", "audit")):
            return "legal"
        return "standard"

