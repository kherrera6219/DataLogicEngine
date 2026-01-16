from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List

from .executor import KAExecutionContext, KAExecutionResult, KAExecutor
from .registry import load_default_registry


def register_builtin_handlers(executor: KAExecutor) -> None:
    """Register a minimal set of built-in KA handlers.

    This is intentionally lightweight: it gives you *real hooks* and a
    runnable pipeline without forcing a single monolithic implementation.
    """
    # Core hygiene
    for ka_id, fn in [
        ("KA-004", ka_004_validate),
        ("KA-005", ka_005_classify),
        ("KA-113", ka_113_router),
        ("KA-001", ka_001_aot),
        ("KA-019", ka_019_synth),
        ("KA-056", ka_056_explain),
    ]:
        if executor.registry.has(ka_id):
            executor.register(ka_id, fn)


def ka_004_validate(ctx: KAExecutionContext) -> KAExecutionResult:
    q = (ctx.input.get("query") or "").strip()
    # simple sanitization (placeholder for real policy+shield)
    q = re.sub(r"\s+", " ", q)
    if not q:
        return KAExecutionResult(ok=False, output={"error": "empty_query"}, veto_reason="Empty query")
    return KAExecutionResult(ok=True, output={"normalized_query": q})


def ka_005_classify(ctx: KAExecutionContext) -> KAExecutionResult:
    q = ctx.input.get("normalized_query") or ctx.input.get("query") or ""
    ql = q.lower()
    # very small heuristic classifier; replace with your production model.
    domain = "general"
    if any(k in ql for k in ["far", "dfars", "soc 2", "iso 27001", "fedramp", "nist"]):
        domain = "compliance"
    elif any(k in ql for k in ["complexity", "np", "bqp", "quantum", "qiskit"]):
        domain = "theory"
    elif any(k in ql for k in ["postgres", "redis", "kubernetes", "python", "api"]):
        domain = "engineering"

    # complexity heuristic
    length = len(q.split())
    has_math = any(sym in q for sym in ["∀", "∃", "→", "⊕", "Σ", "∫"]) or any(k in ql for k in ["prove", "theorem", "lemma"])
    high_stakes = any(k in ql for k in ["legal", "medical", "clinical", "contract", "compliance", "audit", "security"])
    ambiguity = 1 if "?" in q and ("or" in ql or "vs" in ql) else 0

    complexity = "easy"
    if length > 60 or has_math:
        complexity = "hard"
    if length > 120 or (has_math and ambiguity):
        complexity = "extreme"

    return KAExecutionResult(
        ok=True,
        output={
            "domain": domain,
            "complexity_hint": complexity,
            "high_stakes": bool(high_stakes),
            "ambiguity_hint": ambiguity,
        },
    )


def ka_113_router(ctx: KAExecutionContext) -> KAExecutionResult:
    # Decide tier and how deep to run
    c = (ctx.input.get("complexity_hint") or "easy").lower()
    high_stakes = bool(ctx.input.get("high_stakes"))
    verdict = ctx.input.get("verdict", "OK")
    
    tier = "T1"
    layers = ["L1", "L2", "L9"]
    
    # Shield enforcement: If Ambiguous, force robust refinement (T4)
    if verdict == "AMBIGUOUS":
        tier, layers = "T4", ["L1", "L2", "L3", "L4", "L5", "L6", "L8", "L9", "L10"]
    elif c == "easy" and not high_stakes:
        tier, layers = "T0", ["L1", "L9"]
    elif c == "easy" and high_stakes:
        tier, layers = "T2", ["L1", "L2", "L6", "L8", "L9"]
    elif c == "hard" and not high_stakes:
        tier, layers = "T3", ["L1", "L2", "L3", "L4", "L6", "L9"]
    elif c == "hard" and high_stakes:
        tier, layers = "T4", ["L1", "L2", "L3", "L4", "L5", "L6", "L8", "L9", "L10"]
    elif c == "extreme":
        tier, layers = "T5", ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9", "L10"]

    return KAExecutionResult(ok=True, output={"tier": tier, "layers": layers, "budgets": {"max_branches": 6 if tier in {"T4","T5"} else 3}})


def ka_001_aot(ctx: KAExecutionContext) -> KAExecutionResult:
    q = ctx.input.get("normalized_query") or ctx.input.get("query") or ""
    # super-light AoT: split by sentences / semicolons
    parts = [p.strip() for p in re.split(r"[\n;]+", q) if p.strip()]
    if not parts:
        parts = [q]
    tasks = [{"id": f"task_{i+1}", "text": p} for i, p in enumerate(parts)]
    dag = [{"from": tasks[i]["id"], "to": tasks[i+1]["id"]} for i in range(len(tasks)-1)]
    return KAExecutionResult(ok=True, output={"tasks": tasks, "dag": dag})


def ka_019_synth(ctx: KAExecutionContext) -> KAExecutionResult:
    # merges findings objects without prose
    objects = ctx.input.get("objects") or []
    merged: Dict[str, Any] = {"items": [], "meta": {}}
    for obj in objects:
        if isinstance(obj, dict):
            merged["items"].append(obj)
    return KAExecutionResult(ok=True, output={"knowledge_object": merged})


def ka_056_explain(ctx: KAExecutionContext) -> KAExecutionResult:
    trace = ctx.input.get("trace") or []
    summary = []
    for step in trace:
        if isinstance(step, dict):
            summary.append(f"{step.get('ka_id')}: {step.get('status','ok')}")
    return KAExecutionResult(ok=True, output={"explainability": {"steps": summary}})
