from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict, Literal, Tuple
import math
import uuid
import logging

# LangGraph imports
from langgraph.graph import StateGraph, END

# DataLogicEngine imports
from simulation.layer5_schemas import (
    Layer5RunRequest, 
    PersonaEnvelope, 
    PersonaType, 
    Consensus, 
    VetoLog
)

logger = logging.getLogger("Layer5-Pipeline")

# -----------------------------
# State definition for LangGraph
# -----------------------------
class Layer5State(TypedDict, total=False):
    # Inputs
    run_id: str
    trace_id: str
    problem_spec: Dict[str, Any]
    coord: Dict[str, Any]
    context_pack: Dict[str, Any]
    gatekeeper_config: Dict[str, Any]

    # Gatekeeper decisions
    personas_to_spawn: List[str]              # e.g. ["KNOWLEDGE","REGULATORY",...]
    thresholds: Dict[str, float]              # release/escalate thresholds
    persona_weights: Dict[str, float]         # weighting for consensus
    policy_context: Dict[str, Any]            # resolved policy/rbac/sensitivity
    vetoed: bool
    veto_reason: str
    redactions: List[str]

    # Persona outputs (envelopes)
    persona_outputs: List[Dict[str, Any]]     

    # Adjudication artifacts
    conflict_matrix: Dict[str, Any]
    consensus: Dict[str, Any]                # status, confidence_sys, rationale
    timings: Dict[str, Any]
    
    # Internal iteration tracking
    _iter: int


# -----------------------------
# Helpers (math + checks)
# -----------------------------
def clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def persona_confidence(persona_env: Dict[str, Any]) -> float:
    """
    Conf'(p) = Conf(p) * (0.5 + 0.5 * coverage)
    Fallback to persona_env["scores"]["confidence_overall"] if already computed.
    """
    scores = persona_env.get("scores", {})
    base = float(scores.get("confidence_overall", 0.0))
    cov = float(scores.get("coverage", 0.0))
    return clip01(base * (0.5 + 0.5 * cov))


def has_hard_veto(persona_env: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Hard veto if any constraint severity=block applies_to contains output:final
    and persona is REGULATORY or COMPLIANCE (or VALIDATION if you allow).
    """
    ptype = persona_env.get("persona_type")
    if ptype not in ("REGULATORY", "COMPLIANCE"):
        return (False, None)

    for c in persona_env.get("constraints", []) or []:
        if c.get("severity") == "block":
            applies = c.get("applies_to", []) or []
            if any(a == "output:final" for a in applies):
                return (True, f"{ptype} hard-veto: {c.get('text','')}")
    return (False, None)


# -----------------------------
# Node 1: Gatekeeper
# -----------------------------
def gatekeeper_node(state: Layer5State) -> Layer5State:
    logger.info("Executing Gatekeeper Node")
    problem_spec = state.get("problem_spec", {})
    coord = state.get("coord", {})
    ctx = state.get("context_pack", {})
    cfg = state.get("gatekeeper_config", {})

    # ---- Derive basic signals
    # Use presence of regulatory/compliance axes as triggers
    # Check if axes are non-empty strings
    regulatory_trigger = bool(coord.get("a6") or coord.get("a10"))
    compliance_trigger = bool(coord.get("a7") or coord.get("a11") or coord.get("a17"))

    risk_profile = problem_spec.get("risk_profile", {}) or {}
    safety_class = risk_profile.get("safety_class") or "public"

    # ---- Spawn rules
    personas = ["KNOWLEDGE"]

    # Sector if axis2 active or "implementation-ish" tasks
    if coord.get("a2") or problem_spec.get("task_type") in ("design", "debug", "evaluate"):
        personas.append("SECTOR")

    if regulatory_trigger:
        personas.append("REGULATORY")

    if compliance_trigger or safety_class in ("internal", "cui", "secret"):
        personas.append("COMPLIANCE")

    # ---- Thresholds
    thresholds = {
        "release": float(cfg.get("release_threshold", 0.92)),
        "escalate": float(cfg.get("escalate_threshold", 0.75)),
    }

    # ---- Weights
    persona_weights = cfg.get("persona_weights") or {
        "KNOWLEDGE": 0.25,
        "SECTOR": 0.20,
        "REGULATORY": 0.30,
        "COMPLIANCE": 0.25,
        "VALIDATION": 0.10,  # used only if spawned
        "RISK": 0.10,        # used only if spawned
    }

    # ---- Policy context
    policy_context = {
        "safety_class": safety_class,
        "regulatory_trigger": regulatory_trigger,
        "compliance_trigger": compliance_trigger,
        "budgets": ctx.get("budgets", {}),
    }

    state["personas_to_spawn"] = list(dict.fromkeys(personas))  # dedupe preserve order
    state["thresholds"] = thresholds
    state["persona_weights"] = persona_weights
    state["policy_context"] = policy_context
    state["vetoed"] = False
    state["veto_reason"] = ""
    state["redactions"] = []
    
    # Initialize defaults if missing
    if "persona_outputs" not in state:
        state["persona_outputs"] = []
    if "timings" not in state:
        state["timings"] = {}
        
    logger.info(f"Gatekeeper decided to spawn: {state['personas_to_spawn']}")
    return state


# -----------------------------
# Node 2: Personas fan-out
# -----------------------------
# -----------------------------
# Node 2: Personas fan-out
# -----------------------------
def persona_runner_node(state: Layer5State) -> Layer5State:
    personas = state.get("personas_to_spawn", [])
    logger.info(f"Running Personas: {personas}")
    
    current_outputs = state.get("persona_outputs", [])
    new_outputs: List[Dict[str, Any]] = []

    # Import KA-20 on demand to avoid circular deps at top level if any
    try:
    # Import KA-012 (Persona Simulation) instead of deprecated KA-20
    try:
        from backend.knowledge_algorithms.ka_12_persona_simulation import KA012PersonaSimulation
        # KA012 requires context dict in constructor
        ka_engine = KA012PersonaSimulation({}) 
        ka_available = True
    except ImportError as e:
        logger.warning(f"KA-012 not found: {e}. Falling back to simulation stub.")
        ka_available = False

    # Prepare context for KA
    ka_context = {
        "domain": state.get("problem_spec", {}).get("risk_profile", {}).get("domain_risk", "general"),
        "policy_context": state.get("policy_context", {})
    }
    # We use the raw problem or query as the input
    # Assuming the query is somewhere in context_pack or passed down
    # But current State doesn't explicitly store the raw 'query string' easily in top level, 
    # it's likely deep in context_pack["evidence"] or similar.
    # We'll use a placeholder or extract from problem_spec if available.
    query_text = "Query Context" 
    
    for p in personas:
        # Determine confidence
        confidence = 0.85
        if p == "REGULATORY" and state["policy_context"]["regulatory_trigger"]:
            confidence = 0.9

        claims = []
        
        # Call KA if available and appropriate
        if ka_available:
            # KA-20 expects a single query and orchestrates all personas.
            # But here we are iterating per persona (parallel fan-out pattern).
            # We can ask KA-20 for a specific persona response or use its internal methods.
            # KA-20 has `_process_with_persona`.
            
            try:
                # Map our upper-case persona to KA-20 lower-case
                ka_p_type = p.lower()
                ka_result = ka_engine._process_with_persona(ka_p_type, query_text, ka_context)
                
                if ka_result.get("success"):
                    claims.append({
                        "claim_id": f"c-{uuid.uuid4().hex[:6]}",
                        "text": ka_result.get("response", f"Simulated finding from {p}"),
                        "claim_type": "analysis",
                        "confidence": ka_result.get("confidence", confidence)
                    })
                    confidence = ka_result.get("confidence", confidence)
            except Exception as e:
                logger.error(f"KA execution failed for {p}: {e}")
                
        # Fallback if KA didn't produce claims
        if not claims:
            claims.append({
                "claim_id": f"c-{uuid.uuid4().hex[:6]}",
                "text": f"Simulated finding from {p} (KA Unavailable/Failed)",
                "claim_type": "fact",
                "confidence": confidence
            })
        
        constraints = []
        # Simulate a constraint for compliance if internal
        if p == "COMPLIANCE" and state["policy_context"]["safety_class"] == "internal":
             constraints.append({
                 "constraint_id": "cons-1",
                 "text": "Internal data must be handled with appropriate controls.",
                 "severity": "warn",
                 "type": "policy",
                 "applies_to": ["output:final"]
             })

        new_outputs.append({
            "persona_type": p,
            "persona_id": f"{p.lower()}-001",
            "version": "1.0.0",
            "claims": claims,
            "constraints": constraints,
            "risks": [],
            "open_questions": [],
            "self_check": {"contradictions_found": False, "missing_evidence": [], "hallucination_risk": 0.05},
            "scores": {
                "confidence_overall": confidence, 
                "coverage": 0.85, 
                "evidence_quality": 0.80, 
                "policy_alignment": 0.95
            },
            "flags": []
        })

    state["persona_outputs"] = new_outputs
    return state


# -----------------------------
# Node 3: Adjudication
# -----------------------------
def adjudication_node(state: Layer5State) -> Layer5State:
    logger.info("Executing Adjudication Node")
    outputs = state.get("persona_outputs", [])
    weights = state.get("persona_weights", {})
    thresholds = state.get("thresholds", {"release": 0.92, "escalate": 0.75})

    # 1) Hard-veto check
    for env in outputs:
        veto, reason = has_hard_veto(env)
        if veto:
            logger.warning(f"Veto triggered: {reason}")
            state["vetoed"] = True
            state["veto_reason"] = reason or "hard-veto"
            state["consensus"] = {
                "status": "BLOCK",
                "confidence_sys": 0.0,
                "rationale": [state["veto_reason"]],
                "release_threshold": thresholds["release"],
                "escalate_threshold": thresholds["escalate"],
            }
            state["conflict_matrix"] = {"note": "veto-short-circuit"}
            return state

    # 2) Compute consensus confidence (no veto)
    conf_sys = 0.0
    used = 0.0
    for env in outputs:
        ptype = env.get("persona_type", "")
        w = float(weights.get(ptype, 0.0))
        if w <= 0:
            continue
        conf_p = persona_confidence(env)
        conf_sys += w * conf_p
        used += w

    if used > 0:
        conf_sys = conf_sys / used
    
    logger.info(f"System Confidence: {conf_sys:.4f}")

    # 3) Conflict matrix (stub)
    conflict_matrix = {"contradiction_rate": 0.0}

    # 4) Decide status
    if conf_sys >= thresholds["release"]:
        status = "FINALIZE"
    elif conf_sys >= thresholds["escalate"]:
        status = "ESCALATE"
    else:
        status = "CLARIFY"

    state["conflict_matrix"] = conflict_matrix
    state["consensus"] = {
        "status": status,
        "confidence_sys": conf_sys,
        "rationale": [f"consensus_confidence={conf_sys:.3f}", f"contradiction_rate={conflict_matrix['contradiction_rate']}"],
        "release_threshold": thresholds["release"],
        "escalate_threshold": thresholds["escalate"],
    }

    # 5) If escalating, spawn VALIDATION persona next time (optional)
    if status == "ESCALATE":
        personas = state.get("personas_to_spawn", [])
        if "VALIDATION" not in personas:
            personas.append("VALIDATION")
            logger.info("Escalation triggered: Adding VALIDATION persona for next loop.")
        state["personas_to_spawn"] = personas

    return state


# -----------------------------
# Node 4: Build response
# -----------------------------
# -----------------------------
# Node 4: Build response
# -----------------------------
def build_response_node(state: Layer5State) -> Layer5State:
    # Increment iteration counter here to ensure it persists in state
    it = int(state.get("_iter", 0)) + 1
    state["_iter"] = it
    logger.info(f"Refinement Iteration: {it}")
    return state


# -----------------------------
# Router: decide end / loop
# -----------------------------
def router(state: Layer5State) -> str:
    consensus = state.get("consensus", {})
    status = consensus.get("status", "CLARIFY")

    # If status is finalized/blocked/redacted/clarify, we are done
    # (CLARIFY means low confidence but no desire/ability to spiral up to Escalation)
    if status in ("FINALIZE", "BLOCK", "REDACT", "CLARIFY"):
        logger.info(f"Refinement Loop Ending with status: {status}")
        return "end"

    # ESCALATE (0.75 <= conf < 0.92): try to refine/validate if budget allows
    budgets = (state.get("context_pack", {}) or {}).get("budgets", {})
    max_iters = int(budgets.get("max_iterations", 2)) 
    
    current_iter = int(state.get("_iter", 0))

    if current_iter >= max_iters:
        # Hit budget; finalize with what we have
        logger.warning(f"Max iterations ({max_iters}) reached. Finalizing.")
        # Force status change to avoid confusion in final output
        state["consensus"]["status"] = "FINALIZE"
        state["consensus"]["rationale"].append("max_iterations_reached; finalizing")
        return "end"

    logger.info("Looping back for refinement.")
    return "loop"


# -----------------------------
# Graph assembly
# -----------------------------
def build_layer5_graph():
    g = StateGraph(Layer5State)

    g.add_node("gatekeeper", gatekeeper_node)
    g.add_node("personas", persona_runner_node)
    g.add_node("adjudication", adjudication_node)
    g.add_node("build_response", build_response_node)

    g.set_entry_point("gatekeeper")
    g.add_edge("gatekeeper", "personas")
    g.add_edge("personas", "adjudication")
    g.add_edge("adjudication", "build_response")

    g.add_conditional_edges(
        "build_response",
        router,
        {
            "loop": "personas",  # rerun personas (with VALIDATION appended)
            "end": END,
        },
    )
    return g.compile()
