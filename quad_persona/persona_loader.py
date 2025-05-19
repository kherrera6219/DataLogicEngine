"""
Universal Knowledge Graph (UKG) System - Persona Loader

This module loads and manages persona profiles for the Quad Persona Simulation Engine,
handling loading from storage, contextual selection, and persona customization.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
import uuid

from quad_persona.quad_engine import PersonaProfile

logger = logging.getLogger(__name__)

class PersonaLoader:
    """
    Manages loading and configuring persona profiles for the Quad Persona Engine.
    
    This includes:
    - Loading personas from JSON or database storage
    - Selecting appropriate personas based on query context
    - Customizing personas for specific domains or use cases
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the persona loader.
        
        Args:
            storage_path: Path to persona storage (file or directory)
        """
        self.storage_path = storage_path or os.path.join('data', 'personas_db.json')
        self.personas_by_type = {
            "knowledge": {},    # Axis 8
            "sector": {},       # Axis 9
            "regulatory": {},   # Axis 10
            "compliance": {}    # Axis 11
        }
        
        # Domain-specific persona mappings
        self.domain_mappings = {}  # domain -> persona_ids for each type
        
        # Try to load personas from storage
        self._load_personas()
    
    def _load_personas(self):
        """Load personas from the storage path."""
        if not os.path.exists(self.storage_path):
            logger.warning(f"Persona storage not found at {self.storage_path}, initializing empty collection")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
                # Load persona profiles
                for persona_data in data.get('personas', []):
                    persona_type = persona_data.get('persona_type')
                    if persona_type not in self.personas_by_type:
                        logger.warning(f"Skipping persona with invalid type: {persona_type}")
                        continue
                    
                    profile = PersonaProfile.from_dict(persona_data)
                    self.personas_by_type[persona_type][profile.persona_id] = profile
                
                # Load domain mappings
                self.domain_mappings = data.get('domain_mappings', {})
                
                logger.info(f"Loaded {sum(len(personas) for personas in self.personas_by_type.values())} personas from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load personas from {self.storage_path}: {e}")
    
    def save_personas(self):
        """Save personas to the storage path."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Prepare data for saving
            data = {
                'personas': [],
                'domain_mappings': self.domain_mappings
            }
            
            # Add all personas
            for persona_type, personas in self.personas_by_type.items():
                for persona in personas.values():
                    data['personas'].append(persona.to_dict())
            
            # Write to file
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(data['personas'])} personas to {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save personas to {self.storage_path}: {e}")
            return False
    
    def add_persona(self, profile: PersonaProfile) -> bool:
        """
        Add a persona profile to the collection.
        
        Args:
            profile: The persona profile to add
            
        Returns:
            True if added successfully, False otherwise
        """
        if profile.persona_type not in self.personas_by_type:
            logger.error(f"Invalid persona type: {profile.persona_type}")
            return False
        
        self.personas_by_type[profile.persona_type][profile.persona_id] = profile
        logger.info(f"Added persona {profile.name} (ID: {profile.persona_id}) of type {profile.persona_type}")
        return True
    
    def get_persona(self, persona_type: str, persona_id: str) -> Optional[PersonaProfile]:
        """
        Get a persona profile by type and ID.
        
        Args:
            persona_type: The type of the persona (knowledge, sector, regulatory, compliance)
            persona_id: The ID of the persona
            
        Returns:
            The persona profile if found, None otherwise
        """
        if persona_type not in self.personas_by_type:
            logger.error(f"Invalid persona type: {persona_type}")
            return None
        
        return self.personas_by_type[persona_type].get(persona_id)
    
    def get_all_personas_by_type(self, persona_type: str) -> Dict[str, PersonaProfile]:
        """
        Get all personas of a specific type.
        
        Args:
            persona_type: The type of personas to get
            
        Returns:
            A dictionary mapping persona IDs to profiles
        """
        if persona_type not in self.personas_by_type:
            logger.error(f"Invalid persona type: {persona_type}")
            return {}
        
        return self.personas_by_type[persona_type]
    
    def delete_persona(self, persona_type: str, persona_id: str) -> bool:
        """
        Delete a persona profile.
        
        Args:
            persona_type: The type of the persona
            persona_id: The ID of the persona
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if persona_type not in self.personas_by_type:
            logger.error(f"Invalid persona type: {persona_type}")
            return False
        
        if persona_id not in self.personas_by_type[persona_type]:
            logger.warning(f"Persona not found: {persona_type}/{persona_id}")
            return False
        
        del self.personas_by_type[persona_type][persona_id]
        logger.info(f"Deleted persona {persona_type}/{persona_id}")
        return True
    
    def select_personas_for_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Select the most appropriate personas for a query based on context.
        
        Args:
            query: The query text
            context: Optional context information
            
        Returns:
            A dictionary mapping persona types to selected persona IDs
        """
        context = context or {}
        selected_personas = {}
        
        # Extract domain from context if available
        domain = context.get('domain')
        
        # If domain is specified and we have mappings for it, use those
        if domain and domain in self.domain_mappings:
            domain_specific = self.domain_mappings[domain]
            for persona_type in self.personas_by_type.keys():
                if persona_type in domain_specific and domain_specific[persona_type]:
                    # Use the first mapped persona ID
                    persona_id = domain_specific[persona_type][0]
                    if persona_id in self.personas_by_type[persona_type]:
                        selected_personas[persona_type] = persona_id
        
        # For any persona types not yet selected, choose the best match
        # In a real implementation, this would use more sophisticated matching
        for persona_type in self.personas_by_type.keys():
            if persona_type not in selected_personas and self.personas_by_type[persona_type]:
                # For simplicity, just pick the first available persona
                persona_id = next(iter(self.personas_by_type[persona_type].keys()))
                selected_personas[persona_type] = persona_id
        
        logger.info(f"Selected personas for query: {selected_personas}")
        return selected_personas
    
    def create_domain_specific_personas(self, domain: str, domain_info: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Create domain-specific personas for a particular knowledge domain.
        
        Args:
            domain: The domain identifier (e.g., "healthcare", "finance")
            domain_info: Information about the domain for customizing personas
            
        Returns:
            A dictionary mapping persona types to lists of created persona IDs
        """
        created_personas = {
            "knowledge": [],
            "sector": [],
            "regulatory": [],
            "compliance": []
        }
        
        # Example information needed for persona creation
        domain_name = domain_info.get('name', domain.capitalize())
        sector = domain_info.get('sector', 'General')
        regulations = domain_info.get('regulations', [])
        standards = domain_info.get('standards', [])
        
        # Create domain-specific Knowledge Expert (Axis 8)
        knowledge_profile = PersonaProfile(
            persona_id=f"knowledge_{domain}_{str(uuid.uuid4())[:8]}",
            axis_number=8,
            persona_type="knowledge",
            name=f"{domain_name} Knowledge Expert",
            description=f"Specialist in {domain_name} knowledge and concepts"
        )
        
        knowledge_profile.set_component("job_role", {
            "title": f"{domain_name} Specialist",
            "description": f"Expert in {domain_name} concepts and theory"
        })
        
        knowledge_profile.set_component("education", {
            "level": "Advanced Degree",
            "description": f"Specialized education in {domain_name}"
        })
        
        knowledge_profile.set_component("skills", {
            "items": [f"{domain_name} Research", "Domain Analysis", "Knowledge Organization"],
            "description": f"Deep expertise in {domain_name} field"
        })
        
        # Add the persona
        if self.add_persona(knowledge_profile):
            created_personas["knowledge"].append(knowledge_profile.persona_id)
        
        # Create domain-specific Sector Expert (Axis 9)
        sector_profile = PersonaProfile(
            persona_id=f"sector_{domain}_{str(uuid.uuid4())[:8]}",
            axis_number=9,
            persona_type="sector",
            name=f"{sector} Sector Expert",
            description=f"Expert in {sector} sector with focus on {domain_name}"
        )
        
        sector_profile.set_component("job_role", {
            "title": f"{sector} Consultant",
            "description": f"Advises on {domain_name} within {sector} sector"
        })
        
        sector_profile.set_component("skills", {
            "items": [f"{sector} Analysis", f"{domain_name} Integration", "Strategic Planning"],
            "description": f"Skills in applying {domain_name} within {sector} context"
        })
        
        # Add the persona
        if self.add_persona(sector_profile):
            created_personas["sector"].append(sector_profile.persona_id)
        
        # Create domain-specific Regulatory Expert (Axis 10)
        if regulations:
            regulatory_profile = PersonaProfile(
                persona_id=f"regulatory_{domain}_{str(uuid.uuid4())[:8]}",
                axis_number=10,
                persona_type="regulatory",
                name=f"{domain_name} Regulatory Expert",
                description=f"Expert in regulations affecting {domain_name}"
            )
            
            regulatory_profile.set_component("job_role", {
                "title": f"{domain_name} Regulatory Specialist",
                "description": f"Specializes in regulations for {domain_name}"
            })
            
            regulatory_profile.set_component("skills", {
                "items": ["Regulatory Analysis", "Compliance Assessment", "Policy Interpretation"],
                "description": f"Skills in navigating {domain_name} regulatory landscape"
            })
            
            # Set Octopus connections (regulatory frameworks)
            regulatory_profile.octopus_connections = regulations
            
            # Add the persona
            if self.add_persona(regulatory_profile):
                created_personas["regulatory"].append(regulatory_profile.persona_id)
        
        # Create domain-specific Compliance Expert (Axis 11)
        if standards:
            compliance_profile = PersonaProfile(
                persona_id=f"compliance_{domain}_{str(uuid.uuid4())[:8]}",
                axis_number=11,
                persona_type="compliance",
                name=f"{domain_name} Compliance Expert",
                description=f"Expert in {domain_name} compliance requirements"
            )
            
            compliance_profile.set_component("job_role", {
                "title": f"{domain_name} Compliance Officer",
                "description": f"Ensures adherence to {domain_name} standards"
            })
            
            compliance_profile.set_component("skills", {
                "items": ["Compliance Monitoring", "Standard Implementation", "Audit Procedures"],
                "description": f"Skills in ensuring {domain_name} compliance"
            })
            
            # Set Spiderweb connections (compliance overlaps)
            compliance_profile.spiderweb_connections = [
                f"{standard} Integration" for standard in standards
            ]
            
            # Add the persona
            if self.add_persona(compliance_profile):
                created_personas["compliance"].append(compliance_profile.persona_id)
        
        # Create or update domain mapping
        self.domain_mappings[domain] = {
            persona_type: persona_ids for persona_type, persona_ids in created_personas.items() if persona_ids
        }
        
        # Save changes
        self.save_personas()
        
        return created_personas
    
    def load_from_json(self, json_path: str) -> int:
        """
        Load personas from a JSON file.
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            Number of personas loaded
        """
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return 0
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            count = 0
            for persona_data in data:
                persona_type = persona_data.get('persona_type')
                if persona_type not in self.personas_by_type:
                    logger.warning(f"Skipping persona with invalid type: {persona_type}")
                    continue
                
                profile = PersonaProfile.from_dict(persona_data)
                self.personas_by_type[persona_type][profile.persona_id] = profile
                count += 1
            
            logger.info(f"Loaded {count} personas from {json_path}")
            return count
        except Exception as e:
            logger.error(f"Failed to load personas from {json_path}: {e}")
            return 0