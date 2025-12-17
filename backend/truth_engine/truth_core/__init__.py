"""
TruthCore - Adaptive Reasoning Engine

Provides:
- 5-tier workflow routing (Trivial → Autonomous)
- LLM router with task-based profiles
- Multi-persona reasoning enhancement
- Integration with UKG simulation layers
"""

from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.tiers import TierManager, WorkflowTier
from backend.truth_engine.truth_core.router import LLMRouter
from backend.truth_engine.truth_core.personas import PersonaEnhancer

__all__ = ["TruthCoreEngine", "TierManager", "WorkflowTier", "LLMRouter", "PersonaEnhancer"]
