"""
core/persona/quad/models.py — Quad Persona Data Models

Shared, dependency-free data structures for the quad-persona subsystem
(axes 8-11: knowledge, sector, regulatory, compliance).

Extracted from the legacy ``quad_engine.py`` (which previously defined these
inline alongside a duplicated, shadowed engine). Keeping them here lets
consumers import the data model without pulling in any engine implementation.

DISTINCT FROM backend/dmrf/models.py, which defines DMRF routing and result
models. The two share no classes; the filename overlap is coincidental.
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PersonaProfile:
    """
    Represents a complete persona profile with 7 components:
    job_role, education, certifications, skills, training, career_path, related_jobs
    """
    
    def __init__(self, persona_id: str, axis_number: int, persona_type: str, name: str, description: str = None):
        """Initialize a persona profile."""
        self.persona_id = persona_id
        self.axis_number = axis_number  # 8, 9, 10, or 11
        self.persona_type = persona_type  # knowledge, sector, regulatory, compliance
        self.name = name
        self.description = description or ""
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        
        # The 7 core components of each persona
        self.components = {
            "job_role": {},
            "education": {},
            "certifications": {},
            "skills": {},
            "training": {},
            "career_path": {},
            "related_jobs": {}
        }
        
        # Additional metadata specific to this persona
        self.metadata = {}
        
        # Axis-specific attributes
        if axis_number == 10:  # Regulatory Expert (Octopus Node)
            self.octopus_connections = []  # Connections to different regulatory frameworks
        
        if axis_number == 11:  # Compliance Expert (Spiderweb Node)
            self.spiderweb_connections = []  # Cross-standard compliance connections
    
    def set_component(self, component_type: str, data: Dict[str, Any]) -> bool:
        """Set data for a specific component of the persona."""
        if component_type not in self.components:
            logger.error(f"Invalid component type: {component_type}")
            return False
            
        self.components[component_type] = data
        self.updated_at = datetime.now(UTC)
        return True
    
    def get_component(self, component_type: str) -> Dict[str, Any]:
        """Get data for a specific component of the persona."""
        if component_type not in self.components:
            logger.error(f"Invalid component type: {component_type}")
            return {}
            
        return self.components[component_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the persona profile to a dictionary."""
        result = {
            "persona_id": self.persona_id,
            "axis_number": self.axis_number,
            "persona_type": self.persona_type,
            "name": self.name,
            "description": self.description,
            "components": self.components,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if self.axis_number == 10:
            result["octopus_connections"] = self.octopus_connections
            
        if self.axis_number == 11:
            result["spiderweb_connections"] = self.spiderweb_connections
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonaProfile':
        """Create a persona profile from a dictionary."""
        profile = cls(
            persona_id=data.get("persona_id", str(uuid.uuid4())),
            axis_number=data.get("axis_number"),
            persona_type=data.get("persona_type"),
            name=data.get("name"),
            description=data.get("description")
        )
        
        # Load components
        for component_type, component_data in data.get("components", {}).items():
            if component_type in profile.components:
                profile.components[component_type] = component_data
        
        # Load metadata
        profile.metadata = data.get("metadata", {})
        
        # Load timestamps
        if "created_at" in data:
            profile.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            profile.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Load axis-specific attributes
        if profile.axis_number == 10 and "octopus_connections" in data:
            profile.octopus_connections = data["octopus_connections"]
            
        if profile.axis_number == 11 and "spiderweb_connections" in data:
            profile.spiderweb_connections = data["spiderweb_connections"]
            
        return profile


class QueryState:
    """Represents the state of a query being processed by the Quad Persona Engine."""
    
    def __init__(self, query_id: str, query_text: str, context: Dict = None):
        """Initialize a query state."""
        self.query_id = query_id
        self.query_text = query_text
        self.context = context or {}
        self.persona_results = {}
        self.refinement_history = []
        self.confidence = 0.0
        self.final_result = None
    
    def add_persona_result(self, persona_id: str, result: Dict):
        """Add a result from a persona."""
        self.persona_results[persona_id] = result
    
    def add_refinement_step(self, step_info: Dict):
        """Add a refinement step to the history."""
        self.refinement_history.append(step_info)
    
    def set_final_result(self, result: Dict, confidence: float):
        """Set the final result and confidence."""
        self.final_result = result
        self.confidence = confidence
    
    def get_summary(self) -> Dict:
        """Get a summary of the query state."""
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "personas_consulted": list(self.persona_results.keys()),
            "refinement_steps": len(self.refinement_history),
            "confidence": self.confidence
        }

