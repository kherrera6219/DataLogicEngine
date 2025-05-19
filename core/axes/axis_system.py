
"""
Universal Knowledge Graph (UKG) System - Axis System

This module provides the core functionality for the 13-axis system,
coordinating access to different dimensions of knowledge.
"""

import logging
from typing import Dict, Any, Optional, List

# Import all axis handlers
try:
    from core.axes.axis1_knowledge import KnowledgeAxis
except ImportError:
    KnowledgeAxis = None

try:
    from core.axes.axis2_sector import SectorAxis
except ImportError:
    SectorAxis = None

try:
    from core.axes.axis3_domain import DomainAxis
except ImportError:
    DomainAxis = None

try:
    from core.axes.axis4_knowledge import MethodAxis
except ImportError:
    MethodAxis = None

try:
    from core.axes.axis5_temporal import TemporalAxis
except ImportError:
    TemporalAxis = None

try:
    from core.axes.axis6_regulatory import RegulatoryAxis
except ImportError:
    RegulatoryAxis = None

try:
    from core.axes.axis7_compliance import ComplianceAxis
except ImportError:
    ComplianceAxis = None

# Knowledge expert personas (axes 8-11)
try:
    from core.persona.persona_system import PersonaSystem as ExpertAxis
except ImportError:
    ExpertAxis = None

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
        # Add Axis 1: Knowledge (Pillar Levels)
        if KnowledgeAxis:
            self.axes[1] = KnowledgeAxis()
            logger.info("Initialized Axis 1: Knowledge (Pillar Levels)")
        
        # Add Axis 2: Sectors
        if SectorAxis:
            self.axes[2] = SectorAxis()
            logger.info("Initialized Axis 2: Sectors")
            
        # Add Axis 3: Domains
        if DomainAxis:
            self.axes[3] = DomainAxis()
            logger.info("Initialized Axis 3: Domains")
            
        # Add Axis 4: Methods
        if MethodAxis:
            self.axes[4] = MethodAxis()
            logger.info("Initialized Axis 4: Methods")
            
        # Add Axis 5: Temporal
        if TemporalAxis:
            self.axes[5] = TemporalAxis()
            logger.info("Initialized Axis 5: Temporal")
            
        # Add Axis 6: Regulatory
        if RegulatoryAxis:
            self.axes[6] = RegulatoryAxis()
            logger.info("Initialized Axis 6: Regulatory Frameworks")
            
        # Add Axis 7: Compliance
        if ComplianceAxis:
            self.axes[7] = ComplianceAxis()
            logger.info("Initialized Axis 7: Compliance Standards")
            
        # Add Expert Axes (8-11)
        if ExpertAxis:
            # Knowledge Expert
            self.axes[8] = ExpertAxis(expert_type="knowledge")
            logger.info("Initialized Axis 8: Knowledge Expert")
            
            # Skill Expert
            self.axes[9] = ExpertAxis(expert_type="skill")
            logger.info("Initialized Axis 9: Skill Expert")
            
            # Role Expert
            self.axes[10] = ExpertAxis(expert_type="role")
            logger.info("Initialized Axis 10: Role Expert")
            
            # Context Expert
            self.axes[11] = ExpertAxis(expert_type="context")
            logger.info("Initialized Axis 11: Context Expert")
        
        # Add Axis 12: Location
        if LocationAxis:
            self.axes[12] = LocationAxis()
            logger.info("Initialized Axis 12: Location")
            
        # Add Axis 13: Time (currently using Temporal)
        if TemporalAxis:
            self.axes[13] = TemporalAxis(time_focused=True)
            logger.info("Initialized Axis 13: Time")
    
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
