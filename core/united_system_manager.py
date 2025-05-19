
import uuid
import hashlib
import json
from datetime import datetime
import logging

class UnitedSystemManager:
    """
    The United System Manager is responsible for generating and managing unique identifiers
    across the entire UKG system. It ensures that every entity in the system has a consistent
    and traceable identity across all 13 axes of the knowledge graph.
    """
    
    def __init__(self, config):
        """
        Initialize the United System Manager.
        
        Args:
            config (dict): Configuration dictionary
        """
        self.config = config
        self.id_namespace = uuid.uuid4()  # Generate a unique namespace for this instance
        self.uid_registry_entry_type = "uid_registry_entry"
        logging.info(f"UnitedSystemManager initialized with namespace: {self.id_namespace}")
    
    def create_unified_id(self, entity_label, entity_type, ukg_coords=None, specific_id_part=None):
        """
        Create a unified ID for an entity in the UKG.
        
        Args:
            entity_label (str): Human-readable label for the entity
            entity_type (str): Type of entity (Node, Edge, PillarLevel, etc.)
            ukg_coords (dict): Dictionary of axis coordinates in the UKG
            specific_id_part (str, optional): An optional specific ID part to include
            
        Returns:
            dict: A dictionary containing the unified ID components
        """
        timestamp = datetime.now().isoformat()
        
        # Base components for the ID
        id_components = {
            "entity_label": entity_label,
            "entity_type": entity_type,
            "timestamp": timestamp,
            "namespace": str(self.id_namespace)
        }
        
        # Add UKG coordinates if provided
        if ukg_coords:
            id_components["ukg_coords"] = ukg_coords
        
        # Add specific ID part if provided
        if specific_id_part:
            id_components["specific_id"] = specific_id_part
        
        # Generate a JSON string and hash it for the UID
        json_str = json.dumps(id_components, sort_keys=True)
        uid_hash = hashlib.sha256(json_str.encode()).hexdigest()
        
        # Create the final UID package
        uid_package = {
            "uid_string": f"UID_{uid_hash}",
            "uid_creation_time": timestamp,
            "entity_label": entity_label,
            "entity_type": entity_type
        }
        
        # Include coordinates and specific ID if they exist
        if ukg_coords:
            uid_package["ukg_coords"] = ukg_coords
        if specific_id_part:
            uid_package["specific_id_part"] = specific_id_part
        
        return uid_package
    
    def validate_uid(self, uid_string):
        """
        Validate that a UID string matches the expected format.
        
        Args:
            uid_string (str): The UID string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not uid_string or not isinstance(uid_string, str):
            return False
        
        # Check if the UID has the expected prefix and length
        if not uid_string.startswith("UID_"):
            return False
        
        # The SHA-256 hash should be 64 characters long
        hash_part = uid_string[4:]  # Remove 'UID_' prefix
        if len(hash_part) != 64 or not all(c in '0123456789abcdef' for c in hash_part.lower()):
            return False
        
        return True
    
    def extract_axis_context(self, uid_package):
        """
        Extract axis context information from a UID package.
        
        Args:
            uid_package (dict): The UID package to extract context from
            
        Returns:
            dict: Dictionary of axis contexts
        """
        if not uid_package or not isinstance(uid_package, dict):
            return {}
        
        return uid_package.get("ukg_coords", {})
    
    def compare_uids(self, uid1, uid2):
        """
        Compare two UIDs for functional equivalence.
        
        Args:
            uid1 (str): The first UID string
            uid2 (str): The second UID string
            
        Returns:
            bool: True if UIDs are functionally equivalent
        """
        return uid1 == uid2
