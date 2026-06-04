"""
Universal Knowledge Graph (UKG) System - Axis 17: Security & Access Control

This module implements the Security Axis (A17), defining visibility, classification,
and access control policies for knowledge elements.
"""

import logging
from typing import Dict, Any
from core.simulation.coordinate_system import SecurityClassification

logger = logging.getLogger(__name__)

class SecurityAxis:
    """Handler for Axis 17: Security & Access Control"""
    
    def __init__(self):
        self.axis_number = 17
        self.axis_name = "Security & Access Control"
        self.description = "Defines visibility, classification, and access policies"
        self.classifications = [c.value for c in SecurityClassification]
        
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """Navigate Axis 17 based on security clearance."""
        user_clearance = kwargs.get('user_clearance')
        
        return {
            "axis": self.axis_number,
            "name": self.axis_name,
            "filters": {"user_clearance": user_clearance},
            "available_classifications": self.classifications
        }

    def can_access(self, resource_class: SecurityClassification, user_class: SecurityClassification) -> bool:
        """Check if user can access resource (simple hierarchy)."""
        # Hierarchy: PUBLIC < INTERNAL < CONFIDENTIAL < CUI < RESTRICTED < SECRET
        # Using string comparison is not enough, need rank
        ranks = {
            SecurityClassification.PUBLIC: 0,
            SecurityClassification.INTERNAL: 1,
            SecurityClassification.CONFIDENTIAL: 2,
            SecurityClassification.CUI: 3,
            SecurityClassification.RESTRICTED: 4,
            SecurityClassification.SECRET: 5
        }
        return ranks.get(user_class, 0) >= ranks.get(resource_class, 0)
