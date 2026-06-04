"""Compatibility wrapper for the legacy Layer 2 knowledge simulation module."""

from core.simulation.layer2_legacy_knowledge import (
    AxisNode,
    AxisRelationship,
    Layer2KnowledgeGraph,
    Layer2KnowledgeSimulator,
    NestedLayerDatabase,
    SeventeenAxisSystem,
    create_layer2_simulator,
)

__all__ = [
    "AxisNode",
    "AxisRelationship",
    "Layer2KnowledgeGraph",
    "Layer2KnowledgeSimulator",
    "NestedLayerDatabase",
    "SeventeenAxisSystem",
    "create_layer2_simulator",
]
