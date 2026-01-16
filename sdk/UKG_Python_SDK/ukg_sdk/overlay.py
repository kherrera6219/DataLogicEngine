from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .coordinates17 import CoordinateResolver17
from .ka.models import KARegistry
from .ka.registry import load_default_registry, load_registry_from_json
from .ka.executor import KAExecutor, KAExecutionContext, KAExecutionResult
from .ka.builtins import register_builtin_handlers
from .memory import MemoryAdapter, InMemoryMemoryAdapter
from .audit import AuditStore, FileAuditStore, AuditEvent
from .providers import LLMProvider, LLMResponse


class UKGOverlay:
    """Public API overlay system: LLM in, UKG controls around it, output out.

    This is the orchestrator you mount in:
      - FastAPI middleware
      - MCP server tools
      - CLI or batch jobs

    v0.2.0 focuses on:
      - KA registry -> execution map wiring
      - 17-axis coordinate resolver
      - Postgres/Redis memory adapters
      - compliance-grade audit storage (hash-chained)
      - OpenAI/Azure/Anthropic providers
    """

    def __init__(
        self,
        *,
        provider: LLMProvider,
        model: str,
        registry: Optional[KARegistry] = None,
        registry_path: str | Path | None = None,
        data_dir: str | Path | None = None,
        coordinate_resolver: Optional[CoordinateResolver17] = None,
        memory: Optional[MemoryAdapter] = None,
        audit: Optional[AuditStore] = None,
        actor: str = "ukg-sdk",
    ):
        self.provider = provider
        self.model = model
        self.actor = actor

        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent / "data"

        if registry is None:
            if registry_path:
                registry = load_registry_from_json(registry_path)
            else:
                registry = load_default_registry(self.data_dir) or KARegistry(items={})
        self.registry = registry

        self.executor = KAExecutor(registry=self.registry)
        register_builtin_handlers(self.executor)
        self.executor.register("KA-061", self._ka_61_handler)

        self.coordinate_resolver = coordinate_resolver or CoordinateResolver17(
            axis2_json=str(self.data_dir / "axis2_catalog.json"),
            pillar_json=str(self.data_dir / "pillar_catalog.json"),
        )

        self.memory = memory or InMemoryMemoryAdapter()
        self.audit = audit or FileAuditStore(self.data_dir / "audit" / "ukg_audit.jsonl")

    async def run(
        self,
        *,
        query: str,
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        tier_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_id = session_id or str(uuid.uuid4())
        meta = meta or {}
        coord = self.coordinate_resolver.resolve(meta).as_compact_string()

        trace: List[Dict[str, Any]] = []
        def t(ka_id: str, status: str, output: Dict[str, Any] | None = None):
            trace.append({"ka_id": ka_id, "status": status, "output": output or {}})

        # KA-61 Adversarial Shield (L1 Gate)
        # Goal: decide "is this a genuine query?" before retrieval or reasoning.
        out_shield = self.executor.execute("KA-061", input={"query": query}, layer="L1", state={}, memory=self.memory, audit=self.audit, strict=False)
        t("KA-061", "ok", out_shield.output)
        
        verdict = out_shield.output.get("verdict", "OK")
        if verdict in ["ADVERSARIAL", "UNSAFE"]:
             # Rejection / Safe Rewrite path
             action = out_shield.output.get("action", "refuse")
             reasons = out_shield.output.get("reasons", [])
             
             await self._audit(session_id, user_id, "blocked", coord, "KA-061", "L1", out_shield.output, correlation_id)
             
             error_msg = f"Request blocked by Adversarial Shield: {', '.join(reasons)}"
             if action == "ask_clarifying":
                 error_msg = f"Clarification needed: {out_shield.output.get('safe_query', 'Please clarify functionality.')}"
                 
             return {
                 "ok": False,
                 "error": error_msg,
                 "trace": trace,
                 "coordinate": coord,
                 "verdict": out_shield.output
             }

        # L1 hygiene
        out_valid = self.executor.execute("KA-004", input={"query": query}, layer="L1", state={}, memory=self.memory, audit=self.audit, strict=False)
        t("KA-004", "ok" if out_valid.ok else "fail", out_valid.output)
        if not out_valid.ok:
            await self._audit(session_id, user_id, "veto", coord, "KA-004", "L1", out_valid.output, correlation_id)
            return {"ok": False, "error": out_valid.veto_reason or "validation_failed", "trace": trace, "coordinate": coord}

        # classify + route
        out_cls = self.executor.execute("KA-005", input=out_valid.output, layer="L1", state={}, memory=self.memory, audit=self.audit, strict=False)
        t("KA-005", "ok", out_cls.output)

        router_input = {**out_valid.output, **out_cls.output, **out_shield.output}
        out_route = self.executor.execute("KA-113", input=router_input, layer="L1", state={}, memory=self.memory, audit=self.audit, strict=False)
        t("KA-113", "ok", out_route.output)

        tier = tier_override or out_route.output.get("tier") or "T1"
        layers = out_route.output.get("layers") or ["L1", "L2", "L9"]

        # light AoT in L2 if present
        aot = None
        if "L2" in layers and self.registry.has("KA-001"):
            aot = self.executor.execute("KA-001", input={**router_input, "normalized_query": out_valid.output.get("normalized_query")}, layer="L2", state={}, memory=self.memory, audit=self.audit, strict=False)
            t("KA-001", "ok", aot.output)

        # Build final prompt (your production system can inject UKG/USKD context here)
        system = (
            "You are running inside the UKG SDK overlay. "
            "Follow the user's intent. If unsure, state assumptions. "
            f"Coordinate: {coord}. Tier: {tier}. "
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ]

        llm: LLMResponse = await self.provider.complete(messages=messages, model=self.model, temperature=temperature, max_tokens=max_tokens)
        t("LLM", "ok", {"model": llm.model or self.model, "usage": llm.usage or {}})

        # explainability stub
        explain = self.executor.execute("KA-056", input={"trace": trace}, layer="L9", state={}, memory=self.memory, audit=self.audit, strict=False)
        t("KA-056", "ok", explain.output)
        # 5. Final Audit
        await self._audit(session_id, user_id, "completion", coord, "SDK-RUN", "L10", {"model": self.model}, correlation_id)

        return {
            "ok": True,
            "answer": llm.text,
            "coordinate": coord,
            "tier": tier,
            "layers": layers,
            "trace": trace,
            "explainability": explain.output.get("explainability"),
        }
        
    def _ka_61_handler(self, ctx: KAExecutionContext) -> KAExecutionResult:
        """KA-61: Adversarial Input Shield.
        
        Detects trick questions, paradoxes, and prompt injections.
        """
        try:
            raw_query = ctx.input.get("query")
            if not isinstance(raw_query, str):
                 return KAExecutionResult(ok=True, output={"verdict": "OK", "reasons": []})
                 
            query = raw_query.strip()
            
            # Hardening: Fail fast on huge inputs to prevent DoS via regex/processing
            if len(query) > 50000:
                return KAExecutionResult(
                    ok=True, 
                    output={
                        "verdict": "UNSAFE",
                        "reasons": ["input_too_large"],
                        "action": "refuse"
                    }
                )
            
            # 1. Fast Regex Checks (Deterministic)
            reasons = []
            verdict = "OK"
            action = "answer"
            
            # Prompt Injection / Policy Bait
            import re
            # Using compiled regexes is efficient but for this handler doing it inline is acceptable 
            # as long as they are simple.
            
            if re.search(r"(ignore|disregard)\s+(previous|all)\s+instructions", query, re.I):
                reasons.append("prompt_injection")
                verdict = "ADVERSARIAL"
                action = "refuse"
                
            if re.search(r"answer\s+(only|always)\s+with\s+(json|xml|yaml)", query, re.I) and len(query.split()) < 10:
                 # Suspicious constraint without context
                 reasons.append("hidden_constraint_trap")
                 verdict = "AMBIGUOUS"
                 action = "ask_clarifying"
    
            # 2. Heuristic Checks
            if verdict == "OK": 
                 # Impossible Premise (Time based)
                 current_year = datetime.now().year
                 # Check for future years 2026-2099 explicitly
                 if re.search(r"\b(202[6-9]|20[3-9][0-9])\b", query): 
                     if "when did" in query.lower() or "happened" in query.lower():
                          reasons.append("possible_future_premise")
                          verdict = "AMBIGUOUS"
                          action = "ask_clarifying"
                          
                 # Self-Ref Paradox / Logical Traps
                 q_lower = query.lower()
                 if "answer 'no' to this" in q_lower or "this statement is false" in q_lower:
                     reasons.append("self_reference_trap")
                     verdict = "ADVERSARIAL"
                     action = "refuse"
                     
            return KAExecutionResult(
                ok=True, 
                output={
                    "verdict": verdict,
                    "reasons": reasons,
                    "action": action,
                    "safe_query": query # Pass through if OK
                }
            )
        except Exception as e:
            # Fallback: Log error and Fail Safe (or Fail Open depending on policy).
            # We will Fail Safe (Block) for security triggers if we crash.
            return KAExecutionResult(
                ok=False, 
                output={
                    "verdict": "UNSAFE",
                    "reasons": ["internal_shield_error"],
                    "action": "refuse"
                },
                error=str(e)
            )

    async def _audit(self, sid: str, uid: str, kind: str, coord: str, ka_id: str | None, layer: str | None, payload: Dict[str, Any], correlation_id: Optional[str] = None) -> None:
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            ts=datetime.now(timezone.utc).isoformat(),
            kind=kind,
            actor=self.actor,
            session_id=sid,
            ka_id=ka_id,
            layer=layer,
            coordinate=coord,
            correlation_id=correlation_id,
            payload=payload,
        )
        await self.audit.append(event)
