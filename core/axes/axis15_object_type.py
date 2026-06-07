"""
Universal Knowledge Graph (UKG) System - Axis 15: Object Type

This module implements the Object Type axis (A15), defining the structural category
of knowledge elements (e.g., statute, regulation, control, claim).
"""

import logging
from typing import Dict, Any
from core.coordinate_system import ObjectType

logger = logging.getLogger(__name__)

class ObjectTypeAxis:
    """Handler for Axis 15: Object Type"""
    
    def __init__(self):
        self.axis_number = 15
        self.axis_name = "Object Type"
        self.description = "Defines the structural category of knowledge elements"
        self.object_types = [t.value for t in ObjectType]
        
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """Navigate Axis 15 based on object type filters."""
        obj_type = kwargs.get('object_type')
        
        return {
            "axis": self.axis_number,
            "name": self.axis_name,
            "filters": {"object_type": obj_type},
            "available_types": self.object_types
        }

    def validate_type(self, obj_type: str) -> bool:
        """Check if a string is a valid object type."""
        try:
            ObjectType(obj_type)
            return True
        except ValueError:
            return False
