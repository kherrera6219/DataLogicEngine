"""Compatibility wrapper for the core viewpoint registry module."""

from core.simulation.viewpoint_registry import (
    ExpertProfile,
    RedactionPolicy,
    ViewpointProfile,
    ViewpointRegistry,
    create_viewpoint_registry,
)

__all__ = [
    "ExpertProfile",
    "RedactionPolicy",
    "ViewpointProfile",
    "ViewpointRegistry",
    "create_viewpoint_registry",
]
