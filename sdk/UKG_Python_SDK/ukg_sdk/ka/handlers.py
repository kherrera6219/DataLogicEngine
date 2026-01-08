"""
Example KA handlers.

This module provides sample implementations for a handful of Knowledge Algorithms.
They demonstrate how to write functions that accept a request dictionary and return
structured output.  Real implementations should perform the intended reasoning
for each KA.

Naming convention:  the function name must be the lowercase KA identifier with
hyphens replaced by underscores (e.g. 'KA-001' -> 'ka_001').
"""
from __future__ import annotations

from typing import Any, Dict


def ka_001(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    KA‑001: Algorithm of Thought (AoT).

    This stub simply decomposes the query into words.  The real AoT would
    generate a task graph and identify subproblems.
    """
    query = request.get("query", "")
    subtasks = [w.strip() for w in query.split() if w.strip()]
    return {
        "ka_id": "KA-001",
        "status": "ok",
        "subtasks": subtasks,
    }


def ka_004(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    KA‑004: Input Validation & Normalization (VALID).

    This stub simply trims whitespace.  Real validation would sanitize input,
    detect prohibited content, and normalize case/formatting.
    """
    query = request.get("query", "")
    normalized = query.strip()
    return {
        "ka_id": "KA-004",
        "status": "ok",
        "normalized_query": normalized,
    }


def ka_005(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    KA‑005: Query Classification (QCLASS).

    Here we perform a naive classification based on keywords.  Real classification
    would use a trained model or heuristic to assign domain and complexity tags.
    """
    query = request.get("query", "").lower()
    domain = "general"
    if any(word in query for word in ("privacy", "gdpr", "hipaa")):
        domain = "compliance"
    elif any(word in query for word in ("finance", "stock", "budget")):
        domain = "finance"
    complexity = "simple" if len(query) < 50 else "complex"
    return {
        "ka_id": "KA-005",
        "status": "ok",
        "domain": domain,
        "complexity": complexity,
    }


def ka_113(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    KA‑113: Query Analysis & Complexity Router (QROUTER).

    This stub decides which tier to use based on the query complexity and
    length.  It overrides the tier set by the TruthGate if needed.
    """
    query = request.get("query", "")
    tier = "T0" if len(query) < 50 else "T1"
    # Update the request tier in place
    request["tier"] = tier
    return {
        "ka_id": "KA-113",
        "status": "ok",
        "selected_tier": tier,
    }

# Additional KA handlers

def ka_009(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    KA‑009: Evidence Validation (EVID).

    This stub pretends to validate evidence within the query context.  In the
    real system, this KA would examine the collected evidence from the
    knowledge graph, check for consistency, and discard any conflicting
    information.  Here we simply mark the evidence as valid and return a
    placeholder rationale.
    """
    # Pretend to find evidence (none here) and validate it
    rationale = "No conflicting evidence detected."
    return {
        "ka_id": "KA-009",
        "status": "ok",
        "validated": True,
        "rationale": rationale,
    }


def ka_014(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    KA‑014: Confidence Scoring (CONF).

    Compute a naive confidence score based on the request complexity.  The
    longer the query, the lower the confidence.  Real implementations would
    combine multiple factors (evidence quality, persona agreement, etc.).
    """
    query = request.get("query", "")
    # Simple heuristic: base score starts at 1.0 and decreases with length
    base_score = 1.0
    penalty = min(len(query) / 200.0, 0.8)  # cap penalty
    confidence = max(0.1, base_score - penalty)
    return {
        "ka_id": "KA-014",
        "status": "ok",
        "confidence": round(confidence, 3),
    }