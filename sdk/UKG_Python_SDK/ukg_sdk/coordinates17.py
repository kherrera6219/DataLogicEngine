"""
17-axis coordinate resolver.

This module defines a placeholder implementation of a resolver that maps
queries onto the 17‑axis coordinate system used by UKG.  The real resolver
would parse domain, time, location, persona and other signals from the query
and context, consult axis schemas and return a structured coordinate.
"""
from __future__ import annotations

import json
from pathlib import Path
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

    def __init__(self, axis2_json: str | None = None, pillar_json: str | None = None) -> None:
        # Load bundled offline taxonomy by default. Explicit paths still work for
        # tests or generated taxonomy refreshes.
        data_dir = Path(__file__).resolve().parent / "data"
        axis2_path = Path(axis2_json) if axis2_json else data_dir / "axis2_catalog.json"
        pillar_path = Path(pillar_json) if pillar_json else data_dir / "pillar_catalog.json"
        self.axis_data = self._load_json(axis2_path)
        self.pillar_data = self._load_json(pillar_path)

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return {}

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
            "axis_14": "AL1",
            "axis_15": "risk_0.15",
            "axis_16": "LOW",
            "axis_17": "moderate",
            "active_axes": [],
        }
        # Simple pillar matching from bundled taxonomy.
        for item in self.pillar_data.get("items", []):
            terms = [str(item.get("name", "")).lower(), *[str(t).lower() for t in item.get("keywords", [])]]
            if any(term and term in text for term in terms):
                axes["axis_1"] = item.get("coordinate", axes["axis_1"])
                axes["active_axes"].append(1)
                break

        # Simple sector matching using loaded axis2 data
        if self.axis_data:
            keywords = {}
            for item in self.axis_data.get("items", []):
                coord = item.get("coordinate", "")
                for term in [item.get("name", ""), *item.get("keywords", [])]:
                    if term:
                        keywords[str(term).lower()] = coord
            for term, coord in keywords.items():
                if term in text:
                    axes["axis_2"] = coord
                    axes["active_axes"].append(2)
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

        if any(term in text for term in ["far", "dfars", "solicitation", "rfp", "idiq", "clin"]):
            axes["axis_14"] = "AL2"
            axes["active_axes"].append(14)
        if any(term in text for term in ["breach", "security", "compliance", "audit", "risk"]):
            axes["axis_15"] = "risk_0.70"
            axes["active_axes"].append(15)
        if any(term in text for term in ["medical", "patient", "critical", "regulated"]):
            axes["axis_16"] = "CRITICAL"
            axes["active_axes"].append(16)
        if any(term in text for term in ["compliance", "audit", "regulated", "high stakes"]):
            axes["axis_17"] = "high_stakes"
            axes["active_axes"].append(17)
            
        return Coordinate(axes)
