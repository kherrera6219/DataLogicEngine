"""
Simplified implementation of the TruthCore component.

The TruthCore is responsible for orchestrating the Knowledge Algorithms (KAs).
Here it accepts a KAExecutor and simply iterates over all registered KAs, calling
each handler in sequence.  In the full system, TruthCore would manage personas,
simulate multi‑step reasoning, and enforce the 10‑layer/12‑step workflow.
"""
from __future__ import annotations

from typing import Any, Dict

from ..ka.executor import KAExecutor


class TruthCore:
    """
    Minimal reasoning core that delegates to a KA executor and manages context.

    This implementation adds integration with a 17‑axis coordinate resolver and
    a FROST context.  As each KA is executed, its output is recorded in the
    FROST context.  The final result includes the computed coordinate and a
    snapshot of the context stack.  Real logic would further synthesise
    persona outputs, confidence scores and other metadata.
    """

    def __init__(self, executor: KAExecutor, coordinate_resolver: Any | None = None) -> None:
        from .frost import FROSTContext
        self.executor = executor
        self.coord_resolver = coordinate_resolver
        self.frost = FROSTContext()

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute knowledge algorithms based on the request tier, capture
        intermediate context and compute a coordinate vector.

        Parameters
        ----------
        request:
            The request dictionary produced by the TruthGate.  Should
            contain at least a ``query`` and optionally a ``tier``.

        Returns
        -------
        Dict[str, Any]
            A result dictionary containing the tier, aggregated KA outputs,
            the resolved coordinate and a snapshot of the FROST context.  A
            simple answer summary is also included.
        """
        tier = request.get("tier")
        # Resolve coordinates if a resolver is provided
        coordinate = None
        if self.coord_resolver:
            try:
                coordinate = self.coord_resolver.resolve(request.get("query", ""))
            except Exception:
                coordinate = None
        # Execute KAs and record outputs in FROST
        ka_outputs = self.executor.run_all(request, tier=tier)
        for ka_id, output in ka_outputs.items():
            self.frost.push(ka_id, output)
        # Compose a trivial answer.  In practice, a separate synthesis step
        # would generate a final answer using persona consensus and scoring.
        answer = f"Processed {len(ka_outputs)} KAs for tier {tier}."
        return {
            "answer": answer,
            "tier": tier,
            "coordinate": coordinate,
            "ka_outputs": ka_outputs,
            "frost_context": self.frost.as_list(),
        }