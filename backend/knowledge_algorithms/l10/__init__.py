"""Layer 10 Knowledge Algorithms.

The package intentionally avoids eager imports. CP19-E executes independent
Layer 10 modules concurrently through the canonical controller, and importing
all sibling modules from ``__init__`` can deadlock Python's module locks during
a cold parallel start.
"""

L10_KA_REGISTRY = {
    "L10-KA-001": "backend.knowledge_algorithms.l10.l10_ka_001_entropy_scorer",
    "L10-KA-002": "backend.knowledge_algorithms.l10.l10_ka_002_self_awareness",
    "L10-KA-003": "backend.knowledge_algorithms.l10.l10_ka_003_pii_redactor",
    "L10-KA-004": "backend.knowledge_algorithms.l10.l10_ka_004_ethics_validator",
    "L10-KA-005": "backend.knowledge_algorithms.l10.l10_ka_005_containment",
    "L10-KA-006": "backend.knowledge_algorithms.l10.l10_ka_006_trust_gate",
    "L10-KA-007": "backend.knowledge_algorithms.l10.l10_ka_007_escalation_router",
}
