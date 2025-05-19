"""
KA-06: Coordinate Projection Mapper

This algorithm handles the mapping and projection of knowledge coordinates
across the Universal Knowledge Graph's multidimensional space.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import re

logger = logging.getLogger(__name__)

class CoordinateProjectionMapper:
    """
    KA-06: Maps and projects coordinates across the UKG's multidimensional space.
    
    This algorithm translates between pillar levels, axes, and domains to create
    navigable coordinate representations within the Universal Knowledge Graph.
    """
    
    def __init__(self):
        """Initialize the Coordinate Projection Mapper."""
        self.pillar_level_mappings = self._initialize_pillar_level_mappings()
        self.axis_mappings = self._initialize_axis_mappings()
        logger.info("KA-06: Coordinate Projection Mapper initialized")
    
    def _initialize_pillar_level_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mappings for pillar levels."""
        return {
            "PL1": {
                "name": "Fundamental Knowledge",
                "description": "Basic foundations and core principles",
                "depth": 1,
                "coordinates": [1, 0, 0]
            },
            "PL2": {
                "name": "Conceptual Framework",
                "description": "Theoretical models and paradigms",
                "depth": 2,
                "coordinates": [2, 0, 0]
            },
            "PL3": {
                "name": "Applied Knowledge",
                "description": "Practical applications and implementations",
                "depth": 3,
                "coordinates": [3, 0, 0]
            },
            "PL4": {
                "name": "Expert Knowledge",
                "description": "Specialized expertise and advanced concepts",
                "depth": 4,
                "coordinates": [4, 0, 0]
            },
            "PL5": {
                "name": "Integrative Knowledge",
                "description": "Cross-domain synthesis and holistic understanding",
                "depth": 5,
                "coordinates": [5, 0, 0]
            },
            "PL6": {
                "name": "Innovative Knowledge",
                "description": "Novel approaches and cutting-edge developments",
                "depth": 6,
                "coordinates": [6, 0, 0]
            },
            "PL7": {
                "name": "Governance Knowledge",
                "description": "Oversight, management, and regulatory frameworks",
                "depth": 7,
                "coordinates": [7, 0, 0]
            }
        }
    
    def _initialize_axis_mappings(self) -> Dict[int, Dict[str, Any]]:
        """Initialize mappings for axes."""
        return {
            1: {
                "name": "Knowledge Structure",
                "description": "Core organization of knowledge elements",
                "coordinates": [0, 1, 0]
            },
            2: {
                "name": "Contextual Environment",
                "description": "Surrounding conditions and settings",
                "coordinates": [0, 2, 0]
            },
            3: {
                "name": "Interconnection Network",
                "description": "Relationships and connections between elements",
                "coordinates": [0, 3, 0]
            },
            4: {
                "name": "Organizational Framework",
                "description": "Structural arrangement and hierarchy",
                "coordinates": [0, 4, 0]
            },
            5: {
                "name": "Nodal Points",
                "description": "Critical junctions and intersections",
                "coordinates": [0, 5, 0]
            },
            6: {
                "name": "Spatial Positioning",
                "description": "Relative location and orientation",
                "coordinates": [0, 6, 0]
            },
            7: {
                "name": "Verification System",
                "description": "Validation and confirmation mechanisms",
                "coordinates": [0, 7, 0]
            },
            8: {
                "name": "Knowledge Role",
                "description": "Functional position and responsibility",
                "coordinates": [0, 8, 0]
            },
            9: {
                "name": "Sector Classification",
                "description": "Industry and domain categorization",
                "coordinates": [0, 9, 0]
            },
            10: {
                "name": "Regulatory Framework",
                "description": "Rules, policies, and legal structures",
                "coordinates": [0, 10, 0]
            },
            11: {
                "name": "Compliance System",
                "description": "Adherence to standards and requirements",
                "coordinates": [0, 11, 0]
            },
            12: {
                "name": "Geographical Mapping",
                "description": "Physical location and regional context",
                "coordinates": [0, 12, 0]
            },
            13: {
                "name": "Temporal Dimension",
                "description": "Time-related aspects and chronology",
                "coordinates": [0, 13, 0]
            }
        }
    
    def generate_coordinates(self, pillar_level: str, axes: List[int], domain: str) -> Dict[str, Any]:
        """
        Generate coordinate projections for given pillar level, axes, and domain.
        
        Args:
            pillar_level: The pillar level code (e.g., "PL1")
            axes: List of axis numbers
            domain: The domain context
            
        Returns:
            Dictionary with coordinate projections
        """
        # Validate inputs
        if not pillar_level or not isinstance(pillar_level, str):
            return {
                "algorithm": "KA-06",
                "error": "Invalid pillar level provided",
                "success": False
            }
        
        # Normalize pillar level format
        pillar_level = pillar_level.upper()
        if not pillar_level.startswith("PL"):
            pillar_level = "PL" + pillar_level
        
        # Check if pillar level exists
        if pillar_level not in self.pillar_level_mappings:
            # Generate basic coordinates based on characters
            numeric_coords = [ord(c) % 10 for c in pillar_level if c.isalnum()]
            return {
                "algorithm": "KA-06",
                "pillar_level": pillar_level,
                "coordinates": numeric_coords,
                "note": "Using character-based coordinates for unknown pillar level",
                "success": True
            }
        
        # Get pillar level information
        pl_info = self.pillar_level_mappings[pillar_level]
        
        # Base coordinates from pillar level
        base_coordinates = pl_info["coordinates"].copy()
        
        # Process axes
        processed_axes = []
        for axis_num in axes:
            if axis_num in self.axis_mappings:
                axis_info = self.axis_mappings[axis_num]
                processed_axes.append({
                    "number": axis_num,
                    "name": axis_info["name"],
                    "coordinates": axis_info["coordinates"]
                })
        
        # Generate combined coordinates
        combined_coords = base_coordinates.copy()
        for axis in processed_axes:
            axis_coords = axis["coordinates"]
            for i in range(min(len(combined_coords), len(axis_coords))):
                combined_coords[i] += axis_coords[i]
        
        # Add domain influence
        domain_hash = sum(ord(c) for c in domain) % 100
        domain_coordinate = domain_hash / 100.0  # Normalize to 0-1 range
        
        # Add Z-coordinate for domain
        if len(combined_coords) >= 3:
            combined_coords[2] = domain_coordinate
        else:
            combined_coords.append(domain_coordinate)
        
        # Generate string representation
        coordinate_string = f"{pillar_level}.{'-'.join(map(str, axes))}.{domain}"
        
        return {
            "algorithm": "KA-06",
            "pillar_level": pillar_level,
            "axes": axes,
            "domain": domain,
            "base_coordinates": base_coordinates,
            "axis_coordinates": [a["coordinates"] for a in processed_axes],
            "combined_coordinates": combined_coords,
            "coordinate_string": coordinate_string,
            "pl_info": {
                "name": pl_info["name"],
                "description": pl_info["description"],
                "depth": pl_info["depth"]
            },
            "axis_info": [{
                "number": a["number"],
                "name": a["name"]
            } for a in processed_axes],
            "success": True
        }
    
    def parse_coordinate_string(self, coordinate_string: str) -> Dict[str, Any]:
        """
        Parse a coordinate string into its components.
        
        Args:
            coordinate_string: The coordinate string (e.g., "PL1.8-9.healthcare")
            
        Returns:
            Dictionary with parsed components
        """
        if not coordinate_string or not isinstance(coordinate_string, str):
            return {
                "algorithm": "KA-06",
                "error": "Invalid coordinate string provided",
                "success": False
            }
        
        # Parse using regex
        pattern = r"(?P<pl>PL\d+)\.(?P<axes>[\d\-]+)\.(?P<domain>[a-zA-Z_]+)"
        match = re.match(pattern, coordinate_string)
        
        if not match:
            # Try alternative format
            alt_pattern = r"(?P<pl>[A-Za-z\d]+)\.(?P<axes>[\d\-]+)\.(?P<domain>[a-zA-Z_]+)"
            match = re.match(alt_pattern, coordinate_string)
            
            if not match:
                return {
                    "algorithm": "KA-06",
                    "error": f"Could not parse coordinate string: {coordinate_string}",
                    "success": False
                }
        
        # Extract components
        pillar_level = match.group("pl").upper()
        if not pillar_level.startswith("PL"):
            pillar_level = "PL" + pillar_level
        
        axes_str = match.group("axes")
        domain = match.group("domain")
        
        # Parse axes
        axes = [int(axis) for axis in axes_str.split("-")]
        
        # Generate full coordinates
        return self.generate_coordinates(pillar_level, axes, domain)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Coordinate Projection Mapper (KA-06) on the provided data.
    
    Args:
        data: A dictionary containing pillar level, axes, and domain
        
    Returns:
        Dictionary with coordinate projections
    """
    # Initialize mapper
    mapper = CoordinateProjectionMapper()
    
    # Check if we have a coordinate string to parse
    if "coordinate_string" in data:
        return mapper.parse_coordinate_string(data["coordinate_string"])
    
    # Otherwise, generate coordinates from components
    pillar_level = data.get("pillar_level", "")
    axes = data.get("axes", [])
    domain = data.get("domain", "general")
    
    if not pillar_level:
        return {
            "algorithm": "KA-06",
            "error": "No pillar level or coordinate string provided",
            "success": False
        }
    
    return mapper.generate_coordinates(pillar_level, axes, domain)