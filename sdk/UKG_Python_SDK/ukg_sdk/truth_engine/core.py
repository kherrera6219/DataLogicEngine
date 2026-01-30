from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .truthgate import TruthGate
from .truthcore import TruthCore
from .truthlink import TruthLink
from .truthmemory import TruthMemory
from .frost import FROSTContext
from ..ka.executor import KAExecutor


@dataclass
class TruthEngineConfig:
    """High-level configuration for TruthEngine wiring.

    This SDK version keeps the config intentionally small; enterprise deployments
    should extend this with policy packs, cryptographic settings, and storage routing.
    """
    enable_truthgate: bool = True
    enable_truthlink: bool = True
    enable_truthmemory: bool = True
    min_confidence: float = 0.95


@dataclass
class TruthResult:
    ok: bool
    confidence: float
    verdict: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class TruthEngine:
    """Composite TruthEngine (TruthGate + TruthCore + TruthLink + TruthMemory).

    Notes:
    - FROSTContext is treated as an *in-context* simulated store (not a real DB).
    - Persistence adapters (Postgres/Redis) live in ukg_sdk.memory_adapters and may
      be used to checkpoint snapshots and audit trails.
    """

    def __init__(
        self,
        config: Optional[TruthEngineConfig] = None,
        frost: Optional[FROSTContext] = None,
        truthgate: Optional[TruthGate] = None,
        truthcore: Optional[TruthCore] = None,
        truthlink: Optional[TruthLink] = None,
        truthmemory: Optional[TruthMemory] = None,
        executor: Optional[KAExecutor] = None,
    ):
        self.config = config or TruthEngineConfig()
        self.frost = frost or FROSTContext()
        self.executor = executor or KAExecutor()
        self.truthgate = truthgate or TruthGate()
        self.truthcore = truthcore or TruthCore(executor=self.executor)
        self.truthlink = truthlink or TruthLink()
        self.truthmemory = truthmemory or TruthMemory()

    def evaluate(self, claim: str, context: Optional[Dict[str, Any]] = None) -> TruthResult:
        ctx = context or {}
        diagnostics: Dict[str, Any] = {}

        if self.config.enable_truthmemory:
            try:
                mem = self.truthmemory.recall(claim, ctx, frost=self.frost)
                diagnostics["memory"] = mem
            except Exception as e:
                diagnostics["memory_error"] = str(e)

        if self.config.enable_truthgate:
            gate = self.truthgate.check(claim, ctx)
            diagnostics["truthgate"] = gate
            if isinstance(gate, dict) and gate.get("veto") is True:
                return TruthResult(ok=False, confidence=float(gate.get("confidence", 0.0)), verdict="veto", evidence={}, diagnostics=diagnostics)
            
            # Prepare request for core
            # If gate returns a 'request' dict, use it. Otherwise construct one.
            if isinstance(gate, dict) and "request" in gate:
                request = gate["request"]
                if "tier" not in request and "tier" in gate:
                     request["tier"] = gate["tier"]
            else:
                 request = {"query": claim, "context": ctx, "tier": gate.get("tier") if isinstance(gate, dict) else None}
        else:
             request = {"query": claim, "context": ctx}

        core = self.truthcore.process(request)
        diagnostics["truthcore"] = core
        confidence = float(core.get("confidence", 0.0)) if isinstance(core, dict) else 0.0

        if self.config.enable_truthlink:
            try:
                links = self.truthlink.link(claim, ctx, frost=self.frost)
                diagnostics["truthlink"] = links
            except Exception as e:
                diagnostics["truthlink_error"] = str(e)

        ok = confidence >= self.config.min_confidence
        verdict = "pass" if ok else "fail"
        return TruthResult(ok=ok, confidence=confidence, verdict=verdict, evidence={"core": core}, diagnostics=diagnostics)

    def summarize(self) -> Dict[str, Any]:
        """Return a summary of the engine state."""
        return {
            "config": self.config.__dict__ if hasattr(self.config, "__dict__") else str(self.config),
            "gate": str(self.truthgate),
            "core": str(self.truthcore),
            "memory_adapter": str(self.truthmemory._adapter) if hasattr(self.truthmemory, "_adapter") else "unknown"
        }

    @classmethod
    def load_default(cls) -> "TruthEngine":
        """Load a TruthEngine with default configuration."""
        return cls()
