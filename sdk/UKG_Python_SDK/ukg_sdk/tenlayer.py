"""Ten-Layer Processing Stack (TEN_LAYER_STACK).

Canonical layer names and descriptions as of backend v0.5.0.
Docstring kept in sync with TEN_LAYER_STACK constant below.

Layer overview:
  L1  — Input Validation & Routing
  L2  — USKD Materialization
  L3  — Temporal Context Binding
  L4  — POV Overlays
  L5  — Quad Persona Projections
  L6  — AGI Planning & Goal Decomposition
  L7  — Meta-Reasoning & Refinement Controller
  L8  — Trust Validation Gateway
  L9  — Meta-Reasoning Controller (output)
  L10 — Emergence Controller
"""

from __future__ import annotations

from typing import Dict, List


TEN_LAYER_STACK: Dict[str, Dict[str, str]] = {
    "L1": {
        "name": "Input Validation & Routing",
        "description": "Validates, sanitizes, and routes incoming queries; runs adversarial shield (KA-061) and complexity classifier.",
    },
    "L2": {
        "name": "USKD Materialization",
        "description": "Materializes USKD knowledge nodes relevant to the query into the working context.",
    },
    "L3": {
        "name": "Temporal Context Binding",
        "description": "Binds temporal markers, versioning, and time-aware axis values to the reasoning context.",
    },
    "L4": {
        "name": "POV Overlays",
        "description": "Applies point-of-view overlays (regulatory, domain-specific, ethical) to the materialized context.",
    },
    "L5": {
        "name": "Quad Persona Projections",
        "description": "Projects the four quad-persona archetypes (Scientist, Practitioner, Critic, Futurist) onto the context for multi-perspective synthesis.",
    },
    "L6": {
        "name": "AGI Planning & Goal Decomposition",
        "description": "Decomposes complex goals using BFS planning (KA-021); generates sub-goals with depth and iteration caps.",
    },
    "L7": {
        "name": "Meta-Reasoning & Refinement Controller",
        "description": "Drives iterative refinement loops (max 5 iterations); decides REFINE vs FINALIZE per step.",
    },
    "L8": {
        "name": "Trust Validation Gateway",
        "description": "5-phase trust gate: consistency scan (KA-026/030), cross-domain validation, trust computation, self-critique, gate decision. Fail-closed on timeout or exception.",
    },
    "L9": {
        "name": "Meta-Reasoning Controller",
        "description": "Produces explainability traces, provenance annotations, and final output assembly.",
    },
    "L10": {
        "name": "Emergence Controller",
        "description": "Lane A/B emergence safety gate: RELEASE / HALT / MODIFY / ESCALATE decisions; authorized knowledge commit path.",
    },
}


def get_layer(layer_id: str) -> Dict[str, str]:
    """Return metadata dict for a layer ID (e.g. 'L8').

    Raises KeyError for unknown IDs.
    """
    return TEN_LAYER_STACK[layer_id]


def layer_ids() -> List[str]:
    """Return ordered list of layer IDs L1–L10."""
    return list(TEN_LAYER_STACK.keys())
