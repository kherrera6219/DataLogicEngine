"""
Unified Identity & Entity Resolution Service (UIDS)

This module provides the central identity management for the UKG.
It handles canonical UKGID generation, entity resolution, and alias mapping
across disparate labeling systems (SAM.gov, NAICS, ISO, etc.).
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional

class UnifiedIdentityService:
    """
    Identity & Entity Resolution Service (UIDS)
    
    Responsibilities:
    1. Generate and manage canonical UKGIDs.
    2. Maintain mapping between UKGIDs and external aliases.
    3. Resolve entities across different data sources.
    4. Provide metadata for the Identity Plane of the Unified System.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # In-memory registry (should be backed by durable storage in production)
        # ukgid -> { aliases: set(), canonical_name: str, metadata: dict }
        self.registry: Dict[str, Dict[str, Any]] = {}
        
        # Reverse mapping: alias_type:alias_value -> ukgid
        self.alias_index: Dict[str, str] = {}

    def generate_ukgid(self, entity_type: str) -> str:
        """Generate a canonical UKGID."""
        # Format: ukg:<entity_type>:<short_uuid>
        unique_id = uuid.uuid4().hex[:12]
        return f"ukg:{entity_type}:{unique_id}"

    def register_entity(self, 
                        name: str, 
                        entity_type: str, 
                        aliases: Optional[Dict[str, str]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Register a new entity in the UIDS.
        
        Args:
            name: Canonical human-readable name.
            entity_type: Type of entity (e.g., 'reg', 'org', 'sector').
            aliases: Dict of alias_type -> alias_value (e.g., {'naics': '541512'}).
            metadata: Additional metadata properties.
            
        Returns:
            str: The assigned UKGID.
        """
        ukgid = self.generate_ukgid(entity_type)
        
        self.registry[ukgid] = {
            "name": name,
            "type": entity_type,
            "aliases": aliases or {},
            "metadata": metadata or {},
            "created_at": datetime.now(UTC).isoformat()
        }
        
        if aliases:
            for a_type, a_val in aliases.items():
                self.add_alias(ukgid, a_type, a_val)
                
        self.logger.info(f"Registered entity {name} with UKGID {ukgid}")
        return ukgid

    def add_alias(self, ukgid: str, alias_type: str, alias_value: str):
        """Add an alias to an existing UKGID."""
        if ukgid not in self.registry:
            raise ValueError(f"UKGID {ukgid} not found in registry")
            
        alias_key = f"{alias_type}:{alias_value}"
        
        # Check if alias already points to another UKGID
        if alias_key in self.alias_index and self.alias_index[alias_key] != ukgid:
            old_ukgid = self.alias_index[alias_key]
            self.logger.warning(f"Alias {alias_key} already belongs to {old_ukgid}. Resolution conflict possible.")
            
        self.registry[ukgid]["aliases"][alias_type] = alias_value
        self.alias_index[alias_key] = ukgid

    def resolve_ukgid(self, alias_type: str, alias_value: str) -> Optional[str]:
        """Resolve a UKGID from an alias."""
        alias_key = f"{alias_type}:{alias_value}"
        return self.alias_index.get(alias_key)

    def get_entity_info(self, ukgid: str) -> Optional[Dict[str, Any]]:
        """Get full information for a UKGID."""
        return self.registry.get(ukgid)

    def merge_entities(self, primary_ukgid: str, secondary_ukgid: str):
        """Merge two entities into the primary one."""
        if primary_ukgid not in self.registry or secondary_ukgid not in self.registry:
            raise ValueError("Both UKGIDs must exist to merge")
            
        secondary_info = self.registry.pop(secondary_ukgid)
        
        # Move aliases
        for a_type, a_val in secondary_info["aliases"].items():
            self.add_alias(primary_ukgid, a_type, a_val)
            
        # Merge metadata
        self.registry[primary_ukgid]["metadata"].update(secondary_info["metadata"])
        
        self.logger.info(f"Merged {secondary_ukgid} into {primary_ukgid}")

    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        return {
            "healthy": True,
            "entity_count": len(self.registry),
            "alias_count": len(self.alias_index)
        }
