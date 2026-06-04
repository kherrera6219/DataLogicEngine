"""
Universal Knowledge Graph (UKG) System - Quad Persona Subsystem

Components for the quad-persona model covering axes 8-11 of the UKG system
(knowledge, sector, regulatory, compliance): data models, the persona engine,
pod scaling/orchestration, and the mathematical framework.
"""

import logging

from quad_persona.models import PersonaProfile, QueryState
from quad_persona.quad_engine import (
    QuadPersona,
    KnowledgeExpert,
    SectorExpert,
    RegulatoryExpert,
    ComplianceExpert,
    QuadPersonaEngine,
    create_quad_persona_engine,
)

logger = logging.getLogger(__name__)

# Backwards-compatible alias (older callers referenced ``QuadEngine``).
QuadEngine = QuadPersonaEngine

__all__ = [
    "PersonaProfile",
    "QueryState",
    "QuadPersona",
    "KnowledgeExpert",
    "SectorExpert",
    "RegulatoryExpert",
    "ComplianceExpert",
    "QuadPersonaEngine",
    "QuadEngine",
    "create_quad_persona_engine",
]
