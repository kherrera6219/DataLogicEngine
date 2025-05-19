
"""
Universal Knowledge Graph (UKG) System - Models

This module defines the core data models for the UKG system.
It acts as a single import point for all models.
"""

# Import models from db_models.py to avoid duplication
from db_models import (
    Node, Edge, PillarLevel, Sector, Domain,
    Location, KnowledgeNode, KnowledgeAlgorithm, 
    KAExecution, SimulationSession
)

# Don't redefine models already defined in db_models.py
# This prevents the SQLAlchemy error: "Table is already defined for this MetaData instance"
