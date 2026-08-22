"""Compatibility exports for the Quad Persona mathematical framework.

This package replaces the former ``mathematical_framework.py`` module while
preserving imports such as::

    from core.persona.quad.mathematical_framework import QuadPersonaMathematicalSystem

``RefinementWorkflow12Step`` was removed 2026-08-21 (legacy demo stubs).
Canonical 12-step refinement: ``backend.governed_execution.refinement``.
"""

from core.persona.quad.mathematical_framework.integration import (
    IntegrationFunction,
    QuadPersonaMathematicalSystem,
)
from core.persona.quad.mathematical_framework.memory_graph import (
    KnowledgePoint,
    MemoryEdge,
    MemoryVertex,
    StructuredMemoryGraph,
)
from core.persona.quad.mathematical_framework.refinement import (
    DeepRecursiveLearning,
)
from core.persona.quad.mathematical_framework.weights import (
    DynamicWeightFunctions,
    KnowledgeSpaceMapper,
)

__all__ = [
    "KnowledgePoint",
    "MemoryVertex",
    "MemoryEdge",
    "DynamicWeightFunctions",
    "KnowledgeSpaceMapper",
    "StructuredMemoryGraph",
    "DeepRecursiveLearning",
    "IntegrationFunction",
    "QuadPersonaMathematicalSystem",
]
