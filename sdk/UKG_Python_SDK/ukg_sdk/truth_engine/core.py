from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .truthgate import TruthGate
from .truthcore import TruthCore
from .truthlink import TruthLink
from .truthmemory import TruthMemory
from .frost import FROSTContext


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
    ):
        self.config = config or TruthEngineConfig()
        self.frost = frost or FROSTContext()
        self.truthgate = truthgate or TruthGate()
        self.truthcore = truthcore or TruthCore()
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

        core = self.truthcore.score(claim, ctx)
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
