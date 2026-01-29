"""
17‑Axis coordinate resolver.

This module defines a placeholder implementation of a resolver that maps
queries onto the 17‑axis coordinate system used by UKG.  The real resolver
would parse domain, time, location, persona and other signals from the query
and context, consult axis schemas and return a structured coordinate.
"""
from __future__ import annotations

from typing import Any, Dict


class Coordinate:
    """A 17-axis coordinate vector."""
    def __init__(self, axes: Dict[str, Any]):
        self.axes = axes

    def as_compact_string(self) -> str:
        """Return a compact string representation of the coordinate."""
        # Focus on Pillar (axis_1) and Sector (axis_2) for compact representation
        p = self.axes.get("axis_1", "unk")
        s = self.axes.get("axis_2", "unk")
        return f"UKG:{p}:{s}"

    def to_dict(self) -> Dict[str, Any]:
        return self.axes


class CoordinateResolver17:
    """
    Resolve queries into 17‑axis coordinates.

    The UKG coordinate system uses 17 axes spanning pillar, sector, domain,
    personas, location, temporal context and additional semantic dimensions.
    This resolver attempts to derive a coordinate from the query by matching
    simple keywords against a loaded axis taxonomy.  If no match is found,
    the axes are populated with generic values such as ``unknown_pillar``.

    During initialisation, the resolver can load taxonomy files (e.g.
    ``AXIS2_UPDATED_WITH_IDS.json`` and ``PL1_107_UPDATED_WITH_IDS.json``) to
    perform basic lookups.  The JSON structures should correspond to the
    formats produced by the upstream data pipeline.  In the absence of
    external files, the resolver falls back to empty dictionaries.
    """

    def __init__(self, axis2_json: str = "AXIS2_UPDATED_WITH_IDS.json", pillar_json: str = "PL1_107_UPDATED_WITH_IDS.json") -> None:
        import json
        import os

        # Attempt to load axis definitions; ignore errors silently
        self.axis_data = {}
        self.pillar_data = {}
        if os.path.exists(axis2_json):
            try:
                with open(axis2_json, "r", encoding="utf-8") as f:
                    self.axis_data = json.load(f)
            except Exception:
                self.axis_data = {}
        if os.path.exists(pillar_json):
            try:
                with open(pillar_json, "r", encoding="utf-8") as f:
                    self.pillar_data = json.load(f)
            except Exception:
                self.pillar_data = {}

    def resolve(self, input_data: str | Dict[str, Any]) -> Coordinate:
        """
        Resolve a query or meta dict into a 17‑axis coordinate vector.

        Parameters
        ----------
        input_data:
            The raw user query or a metadata dictionary containing the query.

        Returns
        -------
        Coordinate
            A Coordinate object containing the 17-axis vector.
        """
        # Handle dict/meta input gracefully
        if isinstance(input_data, dict):
             query = input_data.get("query", "") or input_data.get("input", "") or str(input_data)
        else:
             query = str(input_data or "")

        text = query.lower()
        # Initialise coordinate with defaults
        axes: Dict[str, Any] = {
            "axis_1": "unknown_pillar",
            "axis_2": "unknown_sector",
            "axis_3": "unknown_domain",
            "axis_4": "unknown_branch",
            "axis_5": "unknown_node",
            "axis_6": "unknown_regulatory_octopus",
            "axis_7": "unknown_compliance_spider",
            "axis_8": "knowledge",
            "axis_9": "sector",
            "axis_10": "regulatory",
            "axis_11": "compliance",
            "axis_12": "global",
            "axis_13": "present",
            "axis_14": "risk_unscored",
            "axis_15": "federated_standby",
            "axis_16": "causality_unbound",
            "axis_17": "telemetry_inactive",
        }
        # Simple sector matching using loaded axis2 data
        if self.axis_data:
            # Flatten keywords from axis definitions (assuming sheet structure)
            keywords = {}
            sheets = self.axis_data.get("sheets", {})
            for sheet in sheets.values():
                for row in sheet.get("rows", {}).values():
                    name = str(row.get("value", "")).lower()
                    coords = row.get("coordinate", "")
                    if name:
                        keywords[name] = coords
            for word in text.split():
                if word in keywords:
                    axes["axis_2"] = keywords[word]
                    break
        # Simple location detection
        for loc in ["us", "europe", "asia", "africa"]:
            if loc in text:
                axes["axis_12"] = loc
                break
        # Simple temporal detection
        if any(t in text for t in ["today", "now", "current"]):
            axes["axis_13"] = "present"
        elif any(t in text for t in ["yesterday", "last week", "last month"]):
            axes["axis_13"] = "past"
        elif any(t in text for t in ["tomorrow", "next week", "next year"]):
            axes["axis_13"] = "future"
            
        return Coordinate(axes)