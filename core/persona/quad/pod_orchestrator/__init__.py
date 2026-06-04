"""Compatibility exports for pod orchestration.

This package replaces the former ``pod_orchestrator.py`` module while preserving
imports such as::

    from core.persona.quad.pod_orchestrator import PodOrchestrator
"""

from core.persona.quad.pod_orchestrator.builder import PersonaBuilder
from core.persona.quad.pod_orchestrator.orchestrator import (
    PodOrchestrator,
    create_pod_orchestrator,
)
from core.persona.quad.pod_orchestrator.synthesis import (
    CrossPodDeconfliction,
    PodSynthesizer,
)

__all__ = [
    "PersonaBuilder",
    "PodSynthesizer",
    "CrossPodDeconfliction",
    "PodOrchestrator",
    "create_pod_orchestrator",
]
