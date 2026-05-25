"""Axis 14: Acquisition Lifecycle.

Canonical Phase B axis for acquisition-stage routing. Legacy provenance fields
remain knowledge-node metadata, not Axis 14 coordinates.
"""

from __future__ import annotations

from typing import Any


class AcquisitionLifecycleAxis:
    """Resolve AL1-AL7 acquisition lifecycle stage hints."""

    axis_number = 14
    axis_name = "Acquisition Lifecycle"
    description = "AL1-AL7 acquisition stage detection and routing"

    STAGES = {
        "AL1": "market_research",
        "AL2": "solicitation",
        "AL3": "evaluation",
        "AL4": "award",
        "AL5": "performance",
        "AL6": "closeout",
        "AL7": "dispute_or_protest",
    }

    KEYWORDS = {
        "market research": "AL1",
        "sources sought": "AL1",
        "rfp": "AL2",
        "solicitation": "AL2",
        "far": "AL2",
        "dfars": "AL2",
        "clin": "AL2",
        "idiq": "AL2",
        "proposal": "AL3",
        "evaluation": "AL3",
        "award": "AL4",
        "contract award": "AL4",
        "performance": "AL5",
        "deliverable": "AL5",
        "closeout": "AL6",
        "protest": "AL7",
        "dispute": "AL7",
    }

    def resolve_context(self, axis_data: Any) -> dict[str, Any]:
        text = str(axis_data or "").lower()
        selected = "AL1"
        matched = []
        for keyword, stage in self.KEYWORDS.items():
            if keyword in text:
                selected = stage
                matched.append(keyword)

        return {
            "axis": self.axis_number,
            "name": self.axis_name,
            "stage_code": selected,
            "stage_name": self.STAGES[selected],
            "matched_keywords": matched,
            "ka_hooks": ["KA-024", "KA-029"],
            "confidence": 0.85 if matched else 0.45,
        }

    def navigate(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("query") or kwargs.get("text") or kwargs
        return self.resolve_context(query)
