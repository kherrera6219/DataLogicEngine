"""17-Axis Coordinate Resolver for the UKG SDK.

Resolves a query + metadata dict into a Coordinate17 object whose fields
correspond to the 17-axis system defined in core/coordinate_system.py.

A14-4: axis_17 default renamed from "moderate" to "standard" to avoid
vocabulary collision with the tier-exclusion set used by the backend gateway's
_create_trace_run (which treats "moderate" as a tier label).  The axis label
and the tier label are semantically distinct concepts; the rename eliminates
future confusion at the cost of a one-time change to the default string value.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Coordinate17:
    """A resolved 17-axis coordinate vector."""

    # Axis 1 — Instance / Entity
    axis_1: str = ""
    # Axis 2 — Sector / Domain taxonomy
    axis_2: str = ""
    # Axis 3 — Honeycomb / Conceptual cluster
    axis_3: str = ""
    # Axis 4 — Branch / Broader-narrower taxonomy
    axis_4: str = ""
    # Axis 5 — Node / Convergence (unmanaged; address via coordinate system)
    axis_5: str = ""
    # Axis 6 — Temporal
    axis_6: str = ""
    # Axis 7 — Confidence / Epistemic weight
    axis_7: float = 1.0
    # Axis 8 — Source provenance type
    axis_8: str = "primary"
    # Axis 9 — Audience / Consumer persona
    axis_9: str = ""
    # Axis 10 — Regulatory / Jurisdictional scope
    axis_10: str = ""
    # Axis 11 — Language / Locale
    axis_11: str = "en"
    # Axis 12 — Format / Modality
    axis_12: str = "text"
    # Axis 13 — Sensitivity classification
    axis_13: str = "general"
    # Axis 14 — Acquisition lifecycle stage
    axis_14: str = "active"
    # Axis 15 — Risk / Threat level
    axis_15: str = "low"
    # Axis 16 — Ethics / Trust label
    axis_16: str = "aligned"
    # Axis 17 — FROST mode / Truth engine mode
    # A14-4: default is "standard" (not "moderate") to avoid tier-label collision.
    axis_17: str = "standard"

    # Pillar and sector resolved from catalogs
    pillar: str = ""
    sector: str = ""

    def as_compact_string(self) -> str:
        """Return a compact dot-separated coordinate string suitable for trace records."""
        parts = [
            self.pillar or "UKG",
            self.sector or "general",
            self.axis_6 or "current",
            self.axis_13,
            self.axis_17,
        ]
        return ".".join(parts)

    def as_dict(self) -> Dict[str, Any]:
        """Return all 17 axes plus pillar/sector as a flat dict."""
        return {
            "axis_1": self.axis_1,
            "axis_2": self.axis_2,
            "axis_3": self.axis_3,
            "axis_4": self.axis_4,
            "axis_5": self.axis_5,
            "axis_6": self.axis_6,
            "axis_7": self.axis_7,
            "axis_8": self.axis_8,
            "axis_9": self.axis_9,
            "axis_10": self.axis_10,
            "axis_11": self.axis_11,
            "axis_12": self.axis_12,
            "axis_13": self.axis_13,
            "axis_14": self.axis_14,
            "axis_15": self.axis_15,
            "axis_16": self.axis_16,
            "axis_17": self.axis_17,
            "pillar": self.pillar,
            "sector": self.sector,
        }


class CoordinateResolver17:
    """Resolve a query+meta dict into a Coordinate17.

    Loads sector taxonomy (axis2_json) and pillar catalog (pillar_json) from
    disk at construction time.  Both files are optional — resolver degrades
    gracefully when they are absent.

    A14-2 note: callers MUST pass {**meta, "query": query} so keyword signals
    from the user query flow into pillar/sector matching.  UKGOverlay.run()
    was updated in this commit to do exactly that.
    """

    def __init__(
        self,
        axis2_json: str | Path | None = None,
        pillar_json: str | Path | None = None,
    ) -> None:
        self._axis2_catalog: Dict[str, Any] = {}
        self._pillar_catalog: List[Dict[str, Any]] = []

        if axis2_json:
            try:
                self._axis2_catalog = json.loads(Path(axis2_json).read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass

        if pillar_json:
            try:
                raw = json.loads(Path(pillar_json).read_text(encoding="utf-8"))
                self._pillar_catalog = raw if isinstance(raw, list) else raw.get("pillars", [])
            except Exception:  # noqa: BLE001
                pass

    def resolve(self, context: Dict[str, Any]) -> Coordinate17:
        """Resolve *context* (which must include key ``"query"`` for keyword
        matching) into a Coordinate17.

        Unknown / missing keys default to the Coordinate17 field defaults.
        """
        coord = Coordinate17()

        query_text: str = str(context.get("query", "")).lower()

        # --- Axis 2 / sector from taxonomy ---
        sector_hint: str = str(context.get("sector", "") or context.get("domain", "")).lower()
        if sector_hint and self._axis2_catalog:
            for key, val in self._axis2_catalog.items():
                if sector_hint in key.lower() or key.lower() in sector_hint:
                    coord.axis_2 = key
                    coord.sector = str(val.get("label", key)) if isinstance(val, dict) else str(val)
                    break

        # --- Pillar from keyword signals in query ---
        if self._pillar_catalog and query_text:
            for entry in self._pillar_catalog:
                keywords: List[str] = entry.get("keywords", [])
                if any(kw.lower() in query_text for kw in keywords):
                    coord.pillar = entry.get("id", "")
                    if not coord.sector:
                        coord.sector = entry.get("sector", "")
                    break

        # --- Direct overrides from context dict ---
        for attr in (
            "axis_1", "axis_2", "axis_3", "axis_4", "axis_5",
            "axis_6", "axis_8", "axis_9", "axis_10",
            "axis_11", "axis_12", "axis_13", "axis_14",
            "axis_15", "axis_16", "axis_17",
            "pillar", "sector",
        ):
            if attr in context and context[attr]:
                setattr(coord, attr, context[attr])

        if "axis_7" in context:
            try:
                coord.axis_7 = float(context["axis_7"])
            except (TypeError, ValueError):
                pass

        # --- Axis 6 temporal: prefer explicit, fall back to meta temporal fields ---
        if not coord.axis_6:
            coord.axis_6 = str(context.get("temporal", "") or context.get("date", "") or "")

        # --- Axis 17: FROST / truth engine mode ---
        # A14-4: default "standard" is set at the dataclass level.  Only
        # override when an explicit axis_17 or truth_mode key is present.
        if not coord.axis_17 or coord.axis_17 == "standard":
            truth_mode = context.get("truth_mode", "")
            if truth_mode:
                coord.axis_17 = str(truth_mode)

        return coord
