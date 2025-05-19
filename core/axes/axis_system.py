"""
Universal Knowledge Graph (UKG) System - Axis System

This module provides the core functionality for the 13-axis system,
coordinating access to different dimensions of knowledge.
"""

import logging
from typing import Dict, Any, Optional, List

# Import axis handlers
try:
    from core.axes.axis1_knowledge import KnowledgeAxis
except ImportError:
    KnowledgeAxis = None

try:
    from core.axes.axis12_location import LocationAxis
except ImportError:
    LocationAxis = None

# Set up logging
logger = logging.getLogger(__name__)

class AxisSystem:
    """Manages the 13-axis system for the UKG."""
    
    def __init__(self):
        """Initialize the axis system."""
        self.axes = {}
        self._initialize_axes()
        
    def _initialize_axes(self):
        """Initialize available axes."""
        # Add Axis 1: Knowledge
        if KnowledgeAxis:
            self.axes[1] = KnowledgeAxis()
            logger.info("Initialized Axis 1: Knowledge")
        
        # Add Axis 12: Location
        if LocationAxis:
            self.axes[12] = LocationAxis()
            logger.info("Initialized Axis 12: Location")
        
        # Add other axes as they become available
    
    def get_axis(self, axis_id: int):
        """Get a specific axis by its ID."""
        if axis_id in self.axes:
            return self.axes[axis_id]
        return None
    
    def get_all_axes(self) -> Dict[int, Any]:
        """Get all available axes."""
        return self.axes
    
    def process_query(self, query: str, axis_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a query through the axis system.
        
        Args:
            query: The query to process
            axis_id: Optional specific axis to use
            
        Returns:
            Dict containing the processing results
        """
        results = {}
        
        # If specific axis requested
        if axis_id and axis_id in self.axes:
            axis = self.axes[axis_id]
            results[f"axis_{axis_id}"] = axis.process_query(query)
            return results
        
        # Otherwise, process through all available axes
        for axis_id, axis in self.axes.items():
            try:
                results[f"axis_{axis_id}"] = axis.process_query(query)
            except Exception as e:
                logger.error(f"Error processing query through Axis {axis_id}: {str(e)}")
                results[f"axis_{axis_id}"] = f"Error: {str(e)}"
        
        return results
    
    def get_related_knowledge(self, node_id: Any, across_axes: bool = False) -> Dict[str, Any]:
        """
        Get knowledge related to a specific node.
        
        Args:
            node_id: ID of the node to find related knowledge for
            across_axes: Whether to search across all axes
            
        Returns:
            Dict containing related knowledge
        """
        results = {}
        
        # Start with knowledge axis as primary
        if 1 in self.axes:
            results["primary"] = self.axes[1].get_related_knowledge(node_id)
        
        # If searching across axes, include others
        if across_axes:
            for axis_id, axis in self.axes.items():
                if axis_id != 1:  # Skip knowledge axis as it's already included
                    try:
                        results[f"axis_{axis_id}"] = axis.get_related_knowledge(node_id)
                    except Exception as e:
                        logger.error(f"Error getting related knowledge from Axis {axis_id}: {str(e)}")
        
        return results
    
    def coordinate_axis_interaction(self, source_axis_id: int, target_axis_id: int, 
                                   query: str) -> Dict[str, Any]:
        """
        Coordinate interaction between two axes.
        
        Args:
            source_axis_id: ID of the source axis
            target_axis_id: ID of the target axis
            query: The query to process
            
        Returns:
            Dict containing the interaction results
        """
        if source_axis_id not in self.axes or target_axis_id not in self.axes:
            return {"error": f"One or both axes ({source_axis_id}, {target_axis_id}) not available"}
        
        try:
            source_axis = self.axes[source_axis_id]
            target_axis = self.axes[target_axis_id]
            
            # Process query in source axis
            source_result = source_axis.process_query(query)
            
            # Use source results to query target axis
            target_result = target_axis.process_external_query(source_result)
            
            return {
                "source": source_result,
                "target": target_result,
                "integrated": self._integrate_results(source_result, target_result)
            }
        except Exception as e:
            logger.error(f"Error coordinating axis interaction: {str(e)}")
            return {"error": str(e)}
    
    def _integrate_results(self, source_result: Any, target_result: Any) -> Dict[str, Any]:
        """
        Integrate results from multiple axes.
        
        Args:
            source_result: Result from source axis
            target_result: Result from target axis
            
        Returns:
            Dict containing integrated results
        """
        # Simple integration for now - can be enhanced with more sophisticated algorithms
        return {
            "combined_knowledge": {
                "source": source_result,
                "target": target_result
            },
            "summary": "Integrated view across multiple knowledge axes"
        }