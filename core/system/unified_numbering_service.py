"""
Unified Numbering Service (UNS)

This module implements the central registry for hierarchical Nuremberg paths
across all 17 axes of the UKG. It ensures consistent path resolution and
expansion for any node in the knowledge graph.
"""

import logging
import json
from typing import Dict, List, Any, Optional

class UnifiedNumberingService:
    """
    Unified Numbering Service (UNS)
    
    Responsibilities:
    1. Manage a registry of axis / pillar hierarchy definitions.
    2. provide Nuremberg-style dot notation paths (e.g., A01.13.2.1).
    3. Resolve path expansions (parent/child relationships).
    4. Validate paths against the official system nomenclature.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.axes: Dict[str, Dict[str, Any]] = {}
        
        if registry_path:
            self.load_registry(registry_path)

    def load_registry(self, path: str):
        """Load the axis registry from a JSON file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.axes = data.get("axes", {})
            self.logger.info(f"Loaded {len(self.axes)} axes from {path}")
        except Exception as e:
            self.logger.error(f"Error loading axis registry: {str(e)}")

    def get_axis_info(self, axis_num: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific axis."""
        return self.axes.get(str(axis_num))

    def format_path(self, axis_num: int, levels: List[str]) -> str:
        """
        Format a list of hierarchy levels into a canonical Nuremberg path.
        
        Example: format_path(1, ["13", "2", "1"]) -> "A01.13.2.1"
        """
        axis_str = f"A{axis_num:02d}"
        path_suffix = ".".join(levels)
        return f"{axis_str}.{path_suffix}"

    def parse_path(self, path: str) -> Dict[str, Any]:
        """
        Parse a Nuremberg path into its components.
        
        Example: "A01.13.2.1" -> {axis: 1, levels: ["13", "2", "1"]}
        """
        parts = path.split(".")
        axis_part = parts[0]
        if not axis_part.startswith("A"):
            raise ValueError(f"Invalid path format: {path}")
            
        axis_num = int(axis_part[1:])
        levels = parts[1:]
        
        return {
            "axis": axis_num,
            "levels": levels,
            "axis_name": self.axes.get(str(axis_num), {}).get("name", "Unknown")
        }

    def get_parent_path(self, path: str) -> Optional[str]:
        """Get the parent path by stripping the last dot-element."""
        parts = path.split(".")
        if len(parts) <= 2:
            return None
        return ".".join(parts[:-1])

    def resolve_label(self, path: str) -> str:
        """
        Resolve a Nuremberg path into a human-readable label using the registry.
        
        Example: "A01.1" -> "Pillar Levels: Core Knowledge"
        """
        parsed = self.parse_path(path)
        axis_num = str(parsed["axis"])
        levels = parsed["levels"]
        
        axis_data = self.axes.get(axis_num, {})
        axis_name = axis_data.get("name", f"Axis {axis_num}")
        
        if not levels:
            return axis_name
            
        # Try to resolve sub-elements if available in registry
        # Current axis_registry supports 1-level for Pillar (A01) and Sector (A02)
        sub_elements = axis_data.get("sub_elements", {})
        top_level = levels[0]
        
        if top_level in sub_elements:
            element_name = sub_elements[top_level].get("name", top_level)
            return f"{axis_name}: {element_name}"
            
        return f"{axis_name}: {'.'.join(levels)}"

    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        return {
            "healthy": len(self.axes) > 0,
            "axis_count": len(self.axes)
        }
