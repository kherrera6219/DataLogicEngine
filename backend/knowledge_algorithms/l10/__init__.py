"""Layer 10: Emergence Detection and Final Safety Gate KA suite."""

from backend.knowledge_algorithms.l10.l10_ka_001_entropy_scorer import run as entropy_scorer
from backend.knowledge_algorithms.l10.l10_ka_002_self_awareness import run as self_awareness
from backend.knowledge_algorithms.l10.l10_ka_003_pii_redactor import run as pii_redactor
from backend.knowledge_algorithms.l10.l10_ka_004_ethics_validator import run as ethics_validator
from backend.knowledge_algorithms.l10.l10_ka_005_containment import run as containment
from backend.knowledge_algorithms.l10.l10_ka_006_trust_gate import run as trust_gate
from backend.knowledge_algorithms.l10.l10_ka_007_escalation_router import run as escalation_router

L10_KA_REGISTRY = {
    "L10-KA-001": entropy_scorer,
    "L10-KA-002": self_awareness,
    "L10-KA-003": pii_redactor,
    "L10-KA-004": ethics_validator,
    "L10-KA-005": containment,
    "L10-KA-006": trust_gate,
    "L10-KA-007": escalation_router,
}
