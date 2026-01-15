"""
Layer 9 Knowledge Algorithms Package

This package contains the 7 KAs that power the MetaReasoningController:

- L9-KA-001: Trace Analyzer
- L9-KA-002: Belief Drift Detector  
- L9-KA-003: Persona Agreement Auditor
- L9-KA-004: Meta-Cognitive Evaluator
- L9-KA-005: Recursion Trigger
- L9-KA-006: Readiness Scorer
- L9-KA-007: Loop Controller
"""

from .l9_ka_001_trace_analyzer import TraceAnalyzerKA
from .l9_ka_002_belief_drift import BeliefDriftDetectorKA
from .l9_ka_003_persona_auditor import PersonaAgreementAuditorKA
from .l9_ka_004_meta_evaluator import MetaCognitiveEvaluatorKA
from .l9_ka_005_recursion_trigger import RecursionTriggerKA
from .l9_ka_006_confidence_calc import ReadinessScorerKA
from .l9_ka_007_loop_controller import LoopControllerKA

__all__ = [
    "TraceAnalyzerKA",
    "BeliefDriftDetectorKA",
    "PersonaAgreementAuditorKA",
    "MetaCognitiveEvaluatorKA",
    "RecursionTriggerKA",
    "ReadinessScorerKA",
    "LoopControllerKA"
]

# KA Registry entries for this package
L9_KA_REGISTRY = {
    "L9-KA-001": {
        "name": "Trace Analyzer",
        "class": "TraceAnalyzerKA",
        "module": "knowledge_algorithms.l9.l9_ka_001_trace_analyzer"
    },
    "L9-KA-002": {
        "name": "Belief Drift Detector",
        "class": "BeliefDriftDetectorKA",
        "module": "knowledge_algorithms.l9.l9_ka_002_belief_drift"
    },
    "L9-KA-003": {
        "name": "Persona Agreement Auditor",
        "class": "PersonaAgreementAuditorKA",
        "module": "knowledge_algorithms.l9.l9_ka_003_persona_auditor"
    },
    "L9-KA-004": {
        "name": "Meta-Cognitive Evaluator",
        "class": "MetaCognitiveEvaluatorKA",
        "module": "knowledge_algorithms.l9.l9_ka_004_meta_evaluator"
    },
    "L9-KA-005": {
        "name": "Recursion Trigger",
        "class": "RecursionTriggerKA",
        "module": "knowledge_algorithms.l9.l9_ka_005_recursion_trigger"
    },
    "L9-KA-006": {
        "name": "Readiness Scorer",
        "class": "ReadinessScorerKA",
        "module": "knowledge_algorithms.l9.l9_ka_006_confidence_calc"
    },
    "L9-KA-007": {
        "name": "Loop Controller",
        "class": "LoopControllerKA",
        "module": "knowledge_algorithms.l9.l9_ka_007_loop_controller"
    }
}
