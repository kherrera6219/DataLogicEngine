"""Metadata for the canonical governed L1-L10 reasoning stages.

``backend.governed_execution.ten_layers.LAYER_NAMES`` remains the naming
authority. This module adds read/write descriptions without creating a second
stage map. Provider execution and trace persistence are orchestrator concerns,
not replacements for canonical L6 or L9.
"""

from __future__ import annotations

from typing import Any, Final

from backend.governed_execution.ten_layers import LAYER_NAMES

_LAYER_DETAILS: Final[dict[str, dict[str, Any]]] = {
    "L1": {
        "reads": ["GovernedRequest", "routing context", "TruthCore input"],
        "writes": ["normalized route", "tier", "TruthCore/DSQP seed"],
        "side_effects": [],
    },
    "L2": {
        "reads": ["retrieved evidence"],
        "writes": ["reasoning evidence IDs", "retrieval disclosure"],
        "side_effects": [],
    },
    "L3": {
        "reads": ["retrieval decisions", "evidence provenance"],
        "writes": ["bounded evidence plan", "provider/connector disclosure"],
        "side_effects": [],
    },
    "L4": {
        "reads": ["DSQP profiles", "axis context"],
        "writes": ["validated persona context", "persona analysis"],
        "side_effects": [],
    },
    "L5": {
        "reads": ["committed persona analysis", "KA result cache"],
        "writes": ["candidate plan", "provider messages", "KA trace"],
        "side_effects": [],
    },
    "L6": {
        "reads": ["provider answer", "evidence", "governance policy"],
        "writes": ["claims", "citations", "validators", "confidence"],
        "side_effects": [],
    },
    "L7": {
        "reads": ["validated claims", "evidence bindings"],
        "writes": ["reasoning boundary", "claim dependency map"],
        "side_effects": [],
    },
    "L8": {
        "reads": ["validators", "policy decisions", "candidate"],
        "writes": ["trust/policy gate decision", "KA trace"],
        "side_effects": [],
    },
    "L9": {
        "reads": ["claims", "validators", "confidence", "layer trace"],
        "writes": ["convergence decision", "refinement/finalization action"],
        "side_effects": [],
    },
    "L10": {
        "reads": ["candidate", "convergence", "confidence", "risk domain"],
        "writes": ["release-gate decision", "final action", "KA trace"],
        "side_effects": [],
    },
}

if set(_LAYER_DETAILS) != set(LAYER_NAMES):  # pragma: no cover - import invariant
    raise RuntimeError("layer_contract_details_out_of_sync")

# Numeric layer id -> canonical name plus descriptive metadata.
LAYER_CONTRACTS: Final[dict[int, dict[str, Any]]] = {
    int(layer_id.removeprefix("L")): {
        "name": LAYER_NAMES[layer_id],
        **_LAYER_DETAILS[layer_id],
    }
    for layer_id in LAYER_NAMES
}


def layer_contract(layer: int) -> dict[str, Any]:
    if layer not in LAYER_CONTRACTS:
        raise KeyError(f"unknown_layer:{layer}")
    return dict(LAYER_CONTRACTS[layer])


def all_layer_ids() -> list[int]:
    return sorted(LAYER_CONTRACTS)
