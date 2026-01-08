"""
Definitions for the 10‑layer simulation stack used by the UKG system.

The 10‑layer stack represents increasing levels of reasoning depth and
computational complexity.  Layers L1 through L10 roughly correspond to:

  L1: Input parsing and context initialisation
  L2: Base knowledge retrieval and axis resolution
  L3: Simple reasoning and planning
  L4: Persona activation and domain analysis
  L5: Conflict detection and resolution
  L6: Evidence validation and truth scoring
  L7: Simulation and what‑if analysis
  L8: Compliance, risk and ethics checks
  L9: Explanation and narrative synthesis
  L10: Memory integration, lifecycle and long‑term persistence

These descriptions are provided for reference; the simplified SDK does not
implement distinct logic per layer but exposes the stack as a data structure
for downstream consumers.
"""

from __future__ import annotations

from typing import List, Tuple


# A list of tuples mapping layer identifiers to human‑readable names.
TEN_LAYER_STACK: List[Tuple[str, str]] = [
    ("L1", "Input Parsing & Context Init"),
    ("L2", "Knowledge Retrieval & Axis Resolution"),
    ("L3", "Planning & Simple Reasoning"),
    ("L4", "Persona Activation & Domain Analysis"),
    ("L5", "Conflict Detection & Resolution"),
    ("L6", "Evidence Validation & Truth Scoring"),
    ("L7", "Simulation & Emergent Analysis"),
    ("L8", "Compliance, Risk & Ethics Checks"),
    ("L9", "Explainability & Narrative Synthesis"),
    ("L10", "Memory & Lifecycle Management"),
]

def get_layer_name(layer_id: str) -> str:
    """Return the human‑readable name for a given layer identifier."""
    for ident, name in TEN_LAYER_STACK:
        if ident.upper() == layer_id.upper():
            return name
    return "Unknown Layer"
