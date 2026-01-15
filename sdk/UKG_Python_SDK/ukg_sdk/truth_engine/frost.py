"""
FROST context aggregator.

The FROST (Fuzzy Reasoning Oriented Simulation Tree) system stores nested
simulation states and intermediate reasoning artifacts in a stack‑like
structure.  It does not persist any data to disk; instead it builds a
contextual history as the reasoning engine progresses through layers and
knowledge algorithms.  In the full UKG implementation this context can be
queried by downstream modules to synthesize final answers or to support
explainability.  Here we provide a simple in‑memory implementation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


class FROSTContext:
    """Maintain a stack of reasoning artifacts across layers and KAs."""

    def __init__(self) -> None:
        # Each entry is a mapping containing a layer or KA name and the
        # associated data.  The order reflects the sequence of execution.
        self._stack: List[Dict[str, Any]] = []
        self._snapshots: Dict[str, List[Dict[str, Any]]] = {}

    def push(self, name: str, data: Any) -> None:
        """Push a new artifact onto the FROST context."""
        self._stack.append({"name": name, "data": data})

    def snapshot(self, version: str) -> None:
        """Create a versioned snapshot of the current context state (e.g. 'USKD_v1')."""
        self._snapshots[version] = list(self._stack)

    def get_snapshot(self, version: str) -> List[Dict[str, Any]]:
        """Retrieve a previous snapshot by version."""
        return self._snapshots.get(version, [])

    def pop(self) -> Dict[str, Any]:
        """Remove and return the most recent artifact.  Raises if empty."""
        return self._stack.pop()

    def as_list(self) -> List[Dict[str, Any]]:
        """Return a shallow copy of the current context stack."""
        return list(self._stack)

    def get_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return all versioned snapshots (USKD lifecycle)."""
        return self._snapshots

    def clear(self) -> None:
        """Reset the context stack and snapshots."""
        self._stack.clear()
        self._snapshots.clear()
