"""
Truth Engine v7.3 - Enterprise AI Gateway System

This module provides the core Truth Engine functionality for the UKG system:
- TruthCore: Adaptive reasoning with 5-tier workflows
- TruthGate: Security gateway with budget control and compliance
- TruthMemory: Audit trail and metrics tracking
- TruthLink: Inter-module messaging and event bus
"""

from backend.truth_engine.truth_core import TruthCoreEngine
from backend.truth_engine.truth_gate import TruthGateGateway
from backend.truth_engine.truth_memory import TruthMemoryManager
from backend.truth_engine.truth_link import TruthLinkBus

__version__ = "7.3"
__all__ = ["TruthCoreEngine", "TruthGateGateway", "TruthMemoryManager", "TruthLinkBus"]
