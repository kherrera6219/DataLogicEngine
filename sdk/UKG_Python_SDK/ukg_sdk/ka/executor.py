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

    def execute(self, ka_id: str, inputs: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> KAExecutionResult:
        start = time.time()
        ctx = KAExecutionContext(ka_id=ka_id, input=inputs, meta=meta or {})
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
