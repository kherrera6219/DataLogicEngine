"""Layer 9 Knowledge Algorithms.

Modules are loaded lazily by the canonical controller so the first bounded
parallel L9 batch cannot deadlock on eager sibling imports.
"""

L9_KA_REGISTRY = {
    "L9-KA-001": "backend.knowledge_algorithms.l9.l9_ka_001_trace_analyzer",
    "L9-KA-002": "backend.knowledge_algorithms.l9.l9_ka_002_belief_drift",
    "L9-KA-003": "backend.knowledge_algorithms.l9.l9_ka_003_persona_auditor",
    "L9-KA-004": "backend.knowledge_algorithms.l9.l9_ka_004_meta_evaluator",
    "L9-KA-005": "backend.knowledge_algorithms.l9.l9_ka_005_recursion_trigger",
    "L9-KA-006": "backend.knowledge_algorithms.l9.l9_ka_006_confidence_calc",
    "L9-KA-007": "backend.knowledge_algorithms.l9.l9_ka_007_loop_controller",
}
