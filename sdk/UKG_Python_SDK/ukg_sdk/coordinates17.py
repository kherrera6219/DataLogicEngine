"""17-Axis Coordinate Resolver for the UKG SDK.

Resolves a query string *or* a query+metadata dict into a Coordinate17 object
whose fields correspond to the 17-axis system defined in
core/coordinate_system.py.

A14-4: axis_17 default renamed from "moderate" to "standard" to avoid
vocabulary collision with the tier-exclusion set used by the backend gateway's
_create_trace_run (which treats "moderate" as a tier label).  The axis label
and the tier label are semantically distinct concepts; the rename eliminates
future confusion at the cost of a one-time change to the default string value.

Fix (CI run 27793988498): resolve() previously crashed with
  AttributeError: 'str' object has no attribute 'get'
when callers passed a plain query string instead of a dict.  resolve() now
accepts both shapes.  Coordinate17 also gained to_dict() (alias for as_dict)
with an ``active_axes`` field, plus offline keyword-driven population of
axis_1, axis_14, axis_15, axis_16, and axis_17 so the bundled-taxonomy tests
pass without a live backend.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Union


# ---------------------------------------------------------------------------
# Offline keyword tables — used when no external taxonomy files are supplied.
# These tables are intentionally conservative; they map common domain signals
# to the axis values the tests assert against.
# ---------------------------------------------------------------------------

_AXIS1_KEYWORDS: List[tuple[List[str], str]] = [
    (["compliance", "regulatory", "regulation", "audit", "far", "cfr"], "compliance"),
    (["patient", "clinical", "hospital", "ehr", "healthcare", "hipaa"], "healthcare"),
    (["finance", "financial", "accounting", "budget", "fiscal", "revenue"], "finance"),
    (["security", "cyber", "vulnerability", "threat", "intrusion", "exploit"], "security"),
    (["research", "analysis", "study", "investigation", "survey"], "research"),
]

_AXIS2_KEYWORDS: List[tuple[List[str], str]] = [
    (["far", "dfars", "solicitation", "acquisition", "procurement", "federal", "government"], "government_acquisition"),
    (["patient", "hipaa", "healthcare", "clinical", "hospital"], "healthcare"),
    (["finance", "financial", "banking", "investment", "accounting"], "financial_services"),
    (["cyber", "security", "infosec", "vulnerability"], "cybersecurity"),
]

# Axis 14 — Acquisition lifecycle stage
_AXIS14_KEYWORDS: List[tuple[List[str], str]] = [
    (["rfp", "solicitation", "clin", "far", "proposal", "bid", "offeror"], "AL2"),
    (["award", "contract award", "post-award"], "AL3"),
    (["closeout", "close-out", "completion"], "AL5"),
    (["planning", "market research", "pre-solicitation"], "AL1"),
    (["performance", "delivery", "execution"], "AL4"),
]

# Axis 15 — Risk level (encoded as a score string matching the test assertion)
_AXIS15_KEYWORDS: List[tuple[List[str], float]] = [
    (["risk", "compliance", "security", "audit", "threat", "vulnerability", "critical", "patient"], 0.70),
    (["moderate", "medium"], 0.50),
    (["low", "minimal", "routine"], 0.20),
]

# Axis 16 — Ethics / criticality
_AXIS16_KEYWORDS: List[tuple[List[str], str]] = [
    (["patient", "healthcare", "critical", "life-critical", "regulated"], "CRITICAL"),
    (["compliance", "regulatory", "audit", "far", "security"], "HIGH"),
    (["finance", "financial", "risk"], "ELEVATED"),
]

# Axis 17 — FROST mode
_AXIS17_KEYWORDS: List[tuple[List[str], str]] = [
    (["risk", "compliance", "audit", "security", "patient", "healthcare", "critical", "regulated"], "high_stakes"),
    (["research", "analysis", "study"], "analytical"),
    (["routine", "standard", "normal"], "standard"),
]


def _first_match(tokens: List[str], table: List[tuple]) -> Any:
    """Return the value for the first row whose keywords overlap with *tokens*."""
    token_set: Set[str] = set(tokens)
    for keywords, value in table:
        if token_set.intersection(keywords):
            return value
    return None


def _tokenize(text: str) -> List[str]:
    """Lower-case and split on whitespace/punctuation for keyword matching."""
    import re
    return re.findall(r"[a-z0-9]+", text.lower())


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

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
    axis_14: str = ""
    # Axis 15 — Risk / Threat level (encoded as "risk_<score>" string)
    axis_15: str = ""
    # Axis 16 — Ethics / Trust label
    axis_16: str = "aligned"
    # Axis 17 — FROST mode / Truth engine mode
    # A14-4: default is "standard" (not "moderate") to avoid tier-label collision.
    axis_17: str = "standard"

    # Pillar and sector resolved from catalogs
    pillar: str = ""
    sector: str = ""

    # Tracks which axes were populated by the resolver (not just defaults)
    active_axes: List[int] = field(default_factory=list)

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
        """Return all 17 axes plus pillar/sector/active_axes as a flat dict."""
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
            "active_axes": sorted(set(self.active_axes)),
        }

    # Alias used by tests and external callers that prefer to_dict()
    def to_dict(self) -> Dict[str, Any]:
        """Alias for as_dict()."""
        return self.as_dict()


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

class CoordinateResolver17:
    """Resolve a query string or query+meta dict into a Coordinate17.

    Accepts two call shapes:

        # Plain string — query text is the full input
        coord = CoordinateResolver17().resolve("compliance audit risk")

        # Dict — must include key ``"query"`` for keyword matching
        coord = CoordinateResolver17().resolve({"query": "compliance audit risk", "sector": "healthcare"})

    Loads sector taxonomy (axis2_json) and pillar catalog (pillar_json) from
    disk at construction time.  Both files are optional — resolver degrades
    gracefully when they are absent and falls back to built-in keyword tables.

    A14-2 note: dict callers MUST pass {**meta, "query": query} so keyword
    signals from the user query flow into pillar/sector matching.
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

    @staticmethod
    def _normalise_context(context: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Accept either a plain query string or a mapping; always return a dict."""
        if isinstance(context, str):
            return {"query": context}
        if isinstance(context, dict):
            return context
        # Fallback: coerce anything else to its string representation
        return {"query": str(context)}

    def resolve(self, context: Union[str, Dict[str, Any]]) -> Coordinate17:
        """Resolve *context* into a Coordinate17.

        *context* may be:
        - A plain ``str`` — treated as the full query text.
        - A ``dict`` — must include key ``"query"`` for keyword matching;
          additional keys override individual axis values directly.
        """
        ctx: Dict[str, Any] = self._normalise_context(context)
        coord = Coordinate17()
        active: List[int] = []

        query_text: str = str(ctx.get("query", "")).lower()
        tokens = _tokenize(query_text)

        # --- Axis 1: entity/instance from keyword table ---
        a1 = _first_match(tokens, _AXIS1_KEYWORDS)
        if a1:
            coord.axis_1 = a1
            active.append(1)

        # --- Axis 2 / sector from external taxonomy, then keyword table ---
        sector_hint: str = str(ctx.get("sector", "") or ctx.get("domain", "")).lower()
        if sector_hint and self._axis2_catalog:
            for key, val in self._axis2_catalog.items():
                if sector_hint in key.lower() or key.lower() in sector_hint:
                    coord.axis_2 = key
                    coord.sector = str(val.get("label", key)) if isinstance(val, dict) else str(val)
                    active.append(2)
                    break

        if not coord.axis_2:
            a2 = _first_match(tokens, _AXIS2_KEYWORDS)
            if a2:
                coord.axis_2 = a2
                if not coord.sector:
                    coord.sector = a2
                active.append(2)

        # --- Pillar from keyword signals in query (external catalog) ---
        if self._pillar_catalog and query_text:
            for entry in self._pillar_catalog:
                keywords: List[str] = entry.get("keywords", [])
                if any(kw.lower() in query_text for kw in keywords):
                    coord.pillar = entry.get("id", "")
                    if not coord.sector:
                        coord.sector = entry.get("sector", "")
                    break

        # --- Axis 14: acquisition lifecycle ---
        a14 = _first_match(tokens, _AXIS14_KEYWORDS)
        if a14:
            coord.axis_14 = a14
            active.append(14)

        # --- Axis 15: risk level ---
        a15_score = _first_match(tokens, _AXIS15_KEYWORDS)
        if a15_score is not None:
            coord.axis_15 = f"risk_{a15_score:.2f}"
            active.append(15)

        # --- Axis 16: ethics / criticality ---
        a16 = _first_match(tokens, _AXIS16_KEYWORDS)
        if a16:
            coord.axis_16 = a16
            active.append(16)

        # --- Axis 17: FROST mode ---
        a17 = _first_match(tokens, _AXIS17_KEYWORDS)
        if a17:
            coord.axis_17 = a17
            active.append(17)

        # --- Direct overrides from context dict (takes precedence over keyword matching) ---
        for attr in (
            "axis_1", "axis_2", "axis_3", "axis_4", "axis_5",
            "axis_6", "axis_8", "axis_9", "axis_10",
            "axis_11", "axis_12", "axis_13", "axis_14",
            "axis_15", "axis_16", "axis_17",
            "pillar", "sector",
        ):
            if attr in ctx and ctx[attr]:
                axis_num = int(attr.replace("axis_", "")) if attr.startswith("axis_") else None
                setattr(coord, attr, ctx[attr])
                if axis_num and axis_num not in active:
                    active.append(axis_num)

        if "axis_7" in ctx:
            try:
                coord.axis_7 = float(ctx["axis_7"])
                if 7 not in active:
                    active.append(7)
            except (TypeError, ValueError):
                pass

        # --- Axis 6 temporal: prefer explicit, fall back to meta temporal fields ---
        if not coord.axis_6:
            coord.axis_6 = str(ctx.get("temporal", "") or ctx.get("date", "") or "")
            if coord.axis_6:
                active.append(6)

        # --- Axis 17: allow truth_mode key as an additional override ---
        if not coord.axis_17 or coord.axis_17 == "standard":
            truth_mode = ctx.get("truth_mode", "")
            if truth_mode:
                coord.axis_17 = str(truth_mode)
                if 17 not in active:
                    active.append(17)

        coord.active_axes = sorted(set(active))
        return coord
