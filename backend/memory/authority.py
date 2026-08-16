"""Memory authority matrix — single operator-visible write/read model.

Phase 4 (audit remediation): operators and settings UIs should treat
``UnifiedMemoryService`` as the durable working-memory SoR for review/export
lifecycle. Other stores remain specialized.

| Store | Authority | Operator surface |
|---|---|---|
| UnifiedMemoryService (JSON graph) | **Write + review SoR** for working memory | `/api/v1/memory/*` |
| TraceRun graph (Postgres) | **SoR for run evidence** | `/api/v1/trace/*` |
| Chroma collections | Retrieval materialization (not operator memory CRUD) | ingestion pipeline |
| TruthMemory modules | Specialized truth-engine helpers; do not replace UnifiedMemory | truth APIs if any |
"""

from __future__ import annotations

from typing import Final

# Canonical operator memory service import path (documentation constant).
OPERATOR_MEMORY_SERVICE = "backend.memory.unified_memory_service.UnifiedMemoryService"

# Routes that own operator memory lifecycle (review/export/compact/recover).
OPERATOR_MEMORY_ROUTE_PREFIX: Final[str] = "/api/v1/memory"

# Stores that must not be presented as alternate operator write APIs.
NON_OPERATOR_MEMORY_STORES: Final[tuple[str, ...]] = (
    "backend.truth_engine.truth_memory",
    "ChromaDB knowledge_nodes",
    "TraceRun stages (evidence, not working memory)",
)


def authority_summary() -> dict[str, object]:
    """Return a JSON-serializable authority description for diagnostics."""
    return {
        "operator_memory_service": OPERATOR_MEMORY_SERVICE,
        "operator_memory_route_prefix": OPERATOR_MEMORY_ROUTE_PREFIX,
        "non_operator_memory_stores": list(NON_OPERATOR_MEMORY_STORES),
        "policy": (
            "Operator review/export/compact uses UnifiedMemoryService only. "
            "Trace evidence remains on TraceRun APIs."
        ),
    }
