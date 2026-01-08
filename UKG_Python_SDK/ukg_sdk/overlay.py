from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .coordinates17 import CoordinateResolver17
from .ka.models import KARegistry
from .ka.registry import load_default_registry, load_registry_from_json
from .ka.executor import KAExecutor
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

        self.coordinate_resolver = coordinate_resolver or CoordinateResolver17(
            axis2_catalog_xlsx=self.data_dir / "axis2_catalog.xlsx",
            pillar_catalog_xlsx=self.data_dir / "pillar_catalog.xlsx",
            strict_validation=False,
        )

        self.memory = memory or InMemoryMemoryAdapter()
        self.audit = audit or FileAuditStore(self.data_dir / "audit" / "ukg_audit.jsonl")

    async def run(
        self,
        *,
        query: str,
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
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

        # L1 hygiene
        out_valid = self.executor.execute("KA-004", input={"query": query}, layer="L1", state={}, memory=self.memory, audit=self.audit, strict=False)
        t("KA-004", "ok" if out_valid.ok else "fail", out_valid.output)
        if not out_valid.ok:
            await self._audit(session_id, user_id, "veto", coord, "KA-004", "L1", out_valid.output)
            return {"ok": False, "error": out_valid.veto_reason or "validation_failed", "trace": trace, "coordinate": coord}

        # classify + route
        out_cls = self.executor.execute("KA-005", input=out_valid.output, layer="L1", state={}, memory=self.memory, audit=self.audit, strict=False)
        t("KA-005", "ok", out_cls.output)

        router_input = {**out_valid.output, **out_cls.output}
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

        await self._audit(session_id, user_id, "complete", coord, None, None, {"tier": tier, "layers": layers, "usage": llm.usage})

        return {
            "ok": True,
            "answer": llm.text,
            "coordinate": coord,
            "tier": tier,
            "layers": layers,
            "trace": trace,
            "explainability": explain.output.get("explainability"),
        }

    async def _audit(self, session_id: str, user_id: str, kind: str, coordinate: str, ka_id: str | None, layer: str | None, payload: Dict[str, Any]) -> None:
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            ts=datetime.now(timezone.utc).isoformat(),
            kind=kind,
            actor=self.actor,
            session_id=session_id,
            ka_id=ka_id,
            layer=layer,
            coordinate=coordinate,
            payload=payload or {},
        )
        await self.audit.append(event)
