"""
Core public API for the simplified UKG Truth Engine.

This module defines a single entry point, :class:`TruthEngineAPI`, which exposes a
high‑level `query` method.  Under the hood, the API orchestrates a TruthGate,
TruthCore, TruthMemory and TruthLink instance.  It also loads a KA registry and
executes each Knowledge Algorithm (KA) via a KAExecutor.

The goal of this skeleton is to demonstrate how to wire these components together.
It does not implement the full reasoning or validation logic of the real system.

"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .truth_engine.truthgate import TruthGate
from .truth_engine.truthcore import TruthCore
from .truth_engine.truthmemory import TruthMemory
from .truth_engine.truthlink import TruthLink
from .ka.executor import KAExecutor


class TruthEngineAPI:
    """High‑level interface to the UKG Truth Engine."""

    def __init__(
        self,
        *,
        memory_adapter: Optional[str] = None,
        ka_registry_path: str = "UKG_KA_1_to_114_Enterprise_Registry.xlsx",
    ) -> None:
        """
        Create a new API instance.

        Parameters
        ----------
        memory_adapter:
            Optional string specifying a persistent memory backend.  Supported values
            include ``postgres`` or ``redis``.  If omitted or unknown, the system will
            fallback to in‑memory storage.
        ka_registry_path:
            Path to the Excel file containing KA definitions.  This is used to
            dynamically build stubs for any KA entries that are not yet implemented.
        """
        # Wire truth engine modules
        self.gate = TruthGate()
        self.link = TruthLink()
        # Choose memory adapter; default to in memory
        self.memory = TruthMemory(adapter=memory_adapter or "inmemory")
        # Initialise the KA executor
        self.executor = KAExecutor(registry_path=ka_registry_path)
        # Load a coordinate resolver to map queries into 17‑axis vectors
        try:
            from .coordinates17 import CoordinateResolver17
            coord_resolver = CoordinateResolver17()
        except Exception:
            coord_resolver = None
        # Core reasoning engine accepts a coordinate resolver and a KA executor
        self.core = TruthCore(executor=self.executor, coordinate_resolver=coord_resolver)

    def query(
        self,
        query: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        tier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query through the truth engine.

        The API performs the following steps:

        1. Pass the raw query and context to the TruthGate to produce a request object.
        2. Execute the configured Knowledge Algorithms via the TruthCore.
        3. Store the request and result in TruthMemory for auditability.
        4. Return a result dictionary with an answer and any metadata.

        This implementation does not perform real reasoning; instead it calls each KA
        stub and collates their outputs.  Real logic can be added by overriding the
        KA stubs or extending TruthCore.
        """
        # Step 1: gateway pre‑processing
        request = self.gate.create_request(query, context=context or {})
        request["tier"] = tier or self.gate.select_tier(request)
        # Step 2: core execution
        result = self.core.process(request)
        # Step 3: memory logging
        self.memory.log_request(request, result)
        # Step 4: return the result
        return result