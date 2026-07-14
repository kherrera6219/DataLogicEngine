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
        domain, domain_signals = self._domain(q, context)
        sector, sector_signals = self._sector(q, context)
        risk, risk_signals = self._risk(q, context)
        axis17 = self.frost_axis.resolve_context({"tier": tier})

        def measured(name: str, value: Any, signals: list[str]) -> dict[str, Any]:
            return {
                "name": name,
                "value": value,
                "signal_count": len(signals),
                "signals": signals,
                "signal_score": min(1.0, len(signals) / 3.0),
                "selection_source": "request_signal" if signals else "deterministic_default",
            }

        axes: dict[str, Any] = {
            "1": measured("Pillar Level System", domain, domain_signals),
            "2": measured("Sector of Industry", sector, sector_signals),
            "3": {"name": "Honeycomb System", "bridges": [domain, sector], "selection_source": "derived"},
            "4": measured("Branch System", context.get("branch") or domain, ["context.branch"] if context.get("branch") else []),
            "5": measured("Node System", "interdisciplinary", []),
            "6": measured("Octopus Node", "multi_regulatory" if risk != "standard" else "standard", risk_signals),
            "7": measured("Spiderweb Node", "constraint_mesh", []),
            "8": {"name": "Knowledge Expert", "persona_type": "knowledge", "selection_source": "required_persona_axis"},
            "9": {"name": "Sector Expert", "persona_type": "sector", "selection_source": "required_persona_axis"},
            "10": {"name": "Regulatory Expert", "persona_type": "regulatory", "selection_source": "required_persona_axis"},
            "11": {"name": "Compliance Expert", "persona_type": "compliance", "selection_source": "required_persona_axis"},
            "12": measured("Location", context.get("jurisdiction") or "global", ["context.jurisdiction"] if context.get("jurisdiction") else []),
            "13": measured("Temporal", context.get("timeframe") or "current", ["context.timeframe"] if context.get("timeframe") else []),
            "14": measured("Acquisition Lifecycle", context.get("acquisition_stage") or "analysis", ["context.acquisition_stage"] if context.get("acquisition_stage") else []),
            "15": measured("Risk & Threat Context", risk, risk_signals),
            "16": measured("Ethics, Trust & Criticality", "high" if tier in {"high_stakes", "extreme", "autonomous"} else "standard", [f"tier:{tier}"]),
            "17": axis17,
        }
        active_axes = list(range(1, 18))
        signaled_axes = sum(
            1
            for item in axes.values()
            if item.get("selection_source") in {"request_signal", "required_persona_axis", "derived"}
        )
        confidence = round(signaled_axes / len(axes), 4)
        return AxisVector(
            axes=axes,
            confidence=confidence,
            active_axes=active_axes,
            frost_layer_depth=int(axis17["frost_layer_depth"]),
            truth_engine_mode=str(axis17["truth_engine_mode"]),
        )

    @staticmethod
    def _domain(query: str, context: dict[str, Any]) -> tuple[str, list[str]]:
        if context.get("domain"):
            return str(context["domain"]), ["context.domain"]
        groups = (
            ("healthcare", ("hipaa", "health", "clinical", "patient")),
            ("finance", ("sox", "finance", "bank", "payment")),
            ("legal", ("legal", "contract", "regulation", "compliance")),
        )
        for value, terms in groups:
            hits = [term for term in terms if term in query]
            if hits:
                return value, [f"query:{term}" for term in hits]
        return "general", []

    @staticmethod
    def _sector(query: str, context: dict[str, Any]) -> tuple[str, list[str]]:
        if context.get("sector"):
            return str(context["sector"]), ["context.sector"]
        groups = (
            ("technology", ("software", "ai")),
            ("healthcare", ("hospital", "patient")),
            ("financial_services", ("bank", "payment")),
        )
        for value, terms in groups:
            hits = [term for term in terms if term in query]
            if hits:
                return value, [f"query:{term}" for term in hits]
        return "cross_industry", []

    @staticmethod
    def _risk(query: str, context: dict[str, Any]) -> tuple[str, list[str]]:
        if context.get("risk_domain"):
            return str(context["risk_domain"]), ["context.risk_domain"]
        groups = (
            ("healthcare", ("safety", "patient", "clinical", "medical")),
            ("finance", ("financial", "payment", "sox", "bank")),
            ("legal", ("legal", "regulatory", "compliance", "audit")),
        )
        for value, terms in groups:
            hits = [term for term in terms if term in query]
            if hits:
                return value, [f"query:{term}" for term in hits]
        return "standard", []
