"""Compatibility exports for the Quad Persona mathematical framework.

This package replaces the former ``mathematical_framework.py`` module while
preserving imports such as::

    from core.persona.quad.mathematical_framework import QuadPersonaMathematicalSystem
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
    RefinementWorkflow12Step,
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
    "RefinementWorkflow12Step",
    "QuadPersonaMathematicalSystem",
]
