from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
import time


@dataclass
class KAExecutionContext:
    """Runtime context passed to KA handlers."""
    ka_id: str
    input: Dict[str, Any]
    meta: Dict[str, Any] = field(default_factory=dict)

    # Backward-compatible alias
    @property
    def inputs(self) -> Dict[str, Any]:
        return self.input

@dataclass
class KAExecutionResult:
    """Standardized execution result (backward compatible)."""
    ok: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0
    ka_id: Optional[str] = None

    # Backward-compatible alias
    @property
    def outputs(self) -> Dict[str, Any]:
        return self.output

KAHandler = Callable[[KAExecutionContext], KAExecutionResult]

class KAExecutor:
    """Executes KAs by ID using a live handler map."""

    def __init__(self, registry_path: Optional[str] = None, registry: Any = None):
        self.handlers: Dict[str, KAHandler] = {}
        self.registry_path = registry_path
        self.registry = registry

    def register(self, ka_id: str, handler: KAHandler):
        self.handlers[ka_id] = handler

    def execute(self, ka_id: str, inputs: Optional[Dict[str, Any]] = None, meta: Optional[Dict[str, Any]] = None, **kwargs) -> KAExecutionResult:
        """
        Execute a Knowledge Agent by ID.
        Supports both 'inputs' (plural) and 'input' (singular) for backward compatibility with overlay.py.
        All extra keyword arguments are merged into 'meta'.
        """
        start = time.time()
        
        # Handle input name variation
        actual_input = inputs or kwargs.pop("input", {})
        
        # Merge extra kwargs into meta
        actual_meta = meta or {}
        if kwargs:
            actual_meta.update(kwargs)
            
        ctx = KAExecutionContext(ka_id=ka_id, input=actual_input, meta=actual_meta)
        handler = self.handlers.get(ka_id)
        if handler is None:
            dur = int((time.time() - start) * 1000)
            return KAExecutionResult(ok=False, output={}, error=f"No handler registered for {ka_id}", duration_ms=dur, ka_id=ka_id)
        try:
            res = handler(ctx)
            dur = int((time.time() - start) * 1000)
            if isinstance(res, KAExecutionResult):
                res.duration_ms = dur
                res.ka_id = res.ka_id or ka_id
                return res
            # if handler returned dict
            return KAExecutionResult(ok=True, output=dict(res or {}), duration_ms=dur, ka_id=ka_id)
        except Exception as e:
            dur = int((time.time() - start) * 1000)
            return KAExecutionResult(ok=False, output={}, error=str(e), duration_ms=dur, ka_id=ka_id)

    def run_all(self, inputs: Dict[str, Any], tier: Optional[str] = None) -> Dict[str, Any]:
        """
        Run all registered KAs (optionally filtering by tier if logic permits).
        Returns a dict of {ka_id: output_dict}.
        """
        results = {}
        # Simple iteration over all registered handlers
        # In a real system, we would filter based on 'tier' vs KA metadata (layers, etc.)
        for ka_id in self.handlers:
            res = self.execute(ka_id, input=inputs)
            if res.ok:
                results[ka_id] = res.output
            else:
                results[ka_id] = {"error": res.error}
        return results
