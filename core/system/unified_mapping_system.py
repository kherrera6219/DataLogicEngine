
"""
Universal Knowledge Graph - Unified Mapping System

This module implements a unified coordinate system overlay for the 13-axis UKG,
using Nuremberg numbering system, SAM.gov naming conventions, and NASA space mapping
to create a precise 13-dimensional coordinate system for data localization.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np

class UnifiedMappingSystem:
    """
    Unified Mapping System for the 13-Axis Universal Knowledge Graph
    
    This system provides:
    1. Nuremberg numbering system overlay with metadata links to original numbering
    2. SAM.gov naming conventions with metadata links to original naming
    3. NASA-inspired spatial coordinate system for 13D data point mapping
    4. Precise data localization in simulated nested memory system
    """
    
    def __init__(self, axis_system=None, graph_manager=None, 
                 memory_manager=None, united_system_manager=None):
        """
        Initialize the Unified Mapping System.
        
        Args:
            axis_system: Reference to the 13-axis system
            graph_manager: Graph Manager for UKG
            memory_manager: Structured Memory Manager
            united_system_manager: United System Manager
        """
        self.logger = logging.getLogger(__name__)
        self.axis_system = axis_system
        self.graph_manager = graph_manager
        self.memory_manager = memory_manager
        self.united_system_manager = united_system_manager
        
        # Nuremberg numbering system mapping (axis -> nuremberg section)
        self.nuremberg_mapping = {
            1: "100",   # Pillar Levels -> Knowledge Organization
            2: "200",   # Sectors -> Industry Categorization
            3: "300",   # Branches -> Specialization Hierarchy
            4: "400",   # Methods -> Methodological Approaches
            5: "500",   # Tools -> Instrumental Resources
            6: "600",   # Regulatory -> Governance Frameworks
            7: "700",   # Compliance -> Standards & Requirements
            8: "800",   # Knowledge Experts -> Expertise Domain
            9: "900",   # Skill Experts -> Applied Capabilities
            10: "1000", # Role Experts -> Professional Functions
            11: "1100", # Context Experts -> Situational Wisdom
            12: "1200", # Locations -> Spatial Reference
            13: "1300"  # Time -> Temporal Dimension
        }
        
        # SAM.gov naming convention mapping
        self.samgov_naming = {
            1: "KNW",   # Knowledge
            2: "IND",   # Industry
            3: "SPC",   # Specialization
            4: "MTH",   # Methods
            5: "TLS",   # Tools
            6: "REG",   # Regulatory
            7: "CMP",   # Compliance
            8: "KEX",   # Knowledge Expert
            9: "SEX",   # Skill Expert
            10: "REX",  # Role Expert
            11: "CEX",  # Context Expert
            12: "LOC",  # Location
            13: "TMP"   # Temporal
        }
        
        # 13D coordinate system basis vectors (unit vectors in each dimension)
        # These define the "directions" in our 13D space
        self.coordinate_basis = np.eye(13)
        
        self.logger.info(f"[{datetime.now()}] Initialized Unified Mapping System with 13D coordinate space")
    
    def get_nuremberg_code(self, axis_num: int, node_id: str) -> str:
        """
        Generate a Nuremberg-style code for a node in a specific axis.
        
        Args:
            axis_num: The axis number (1-13)
            node_id: The original node ID
            
        Returns:
            str: Nuremberg-style code
        """
        if axis_num not in self.nuremberg_mapping:
            return f"000-{node_id}"
            
        prefix = self.nuremberg_mapping[axis_num]
        
        # Generate a deterministic suffix based on the node_id
        # This ensures the same node always gets the same code
        node_hash = abs(hash(node_id)) % 10000
        suffix = f"{node_hash:04d}"
        
        return f"{prefix}-{suffix}"
    
    def get_samgov_name(self, axis_num: int, original_name: str) -> str:
        """
        Generate a SAM.gov style name for a node.
        
        Args:
            axis_num: The axis number (1-13)
            original_name: The original node name
            
        Returns:
            str: SAM.gov style name
        """
        if axis_num not in self.samgov_naming:
            return original_name
            
        prefix = self.samgov_naming[axis_num]
        
        # Sanitize the original name to create a valid identifier
        # Remove special characters and convert spaces to underscores
        sanitized = ''.join(c if c.isalnum() else '_' for c in original_name)
        sanitized = sanitized.strip('_')
        
        # Truncate if necessary (SAM.gov names are typically shorter)
        if len(sanitized) > 30:
            sanitized = sanitized[:30]
            
        return f"{prefix}_{sanitized}"
    
    def calculate_13d_coordinates(self, node_data: Dict[str, Any]) -> np.ndarray:
        """
        Calculate the 13-dimensional coordinates for a node.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            np.ndarray: 13D coordinate vector
        """
        # Initialize the coordinate vector with zeros
        coordinates = np.zeros(13)
        
        # Set the primary axis component
        if 'axis_number' in node_data:
            primary_axis = int(node_data['axis_number'])
            if 1 <= primary_axis <= 13:
                coordinates[primary_axis-1] = 1.0
        
        # Include cross-axis influences if available
        if 'cross_axis_relations' in node_data:
            for relation in node_data['cross_axis_relations']:
                rel_axis = relation.get('axis_number')
                rel_weight = relation.get('weight', 0.5)
                
                if rel_axis and 1 <= int(rel_axis) <= 13:
                    coordinates[int(rel_axis)-1] += rel_weight
        
        # Normalize the vector
        norm = np.linalg.norm(coordinates)
        if norm > 0:
            coordinates = coordinates / norm
            
        return coordinates
    
    def create_unified_identifier(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a unified identifier for a node, incorporating Nuremberg numbering
        and SAM.gov naming conventions.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            Dict containing the unified identifier
        """
        # Extract base information
        node_id = node_data.get('id', str(uuid.uuid4()))
        node_name = node_data.get('name', 'Unnamed Node')
        axis_num = node_data.get('axis_number', 0)
        
        # Generate Nuremberg code
        nuremberg_code = self.get_nuremberg_code(axis_num, node_id)
        
        # Generate SAM.gov name
        samgov_name = self.get_samgov_name(axis_num, node_name)
        
        # Calculate 13D coordinates
        coordinates = self.calculate_13d_coordinates(node_data)
        
        # Create the unified ID package
        unified_id = {
            'original_id': node_id,
            'original_name': node_name,
            'nuremberg_code': nuremberg_code,
            'samgov_name': samgov_name,
            'coordinates_13d': coordinates.tolist(),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'axis_number': axis_num,
                'original_type': node_data.get('node_type', 'unknown')
            }
        }
        
        return unified_id
    
    def locate_data_in_memory_space(self, coordinates: np.ndarray, 
                                  precision: float = 0.1) -> Dict[str, Any]:
        """
        Locate data in the simulated memory space using 13D coordinates.
        
        Args:
            coordinates: 13D coordinate vector
            precision: Search precision threshold
            
        Returns:
            Dict containing located data cells
        """
        if self.memory_manager is None:
            return {
                'status': 'error',
                'message': 'Memory manager not available'
            }
            
        # Normalize input coordinates if needed
        norm = np.linalg.norm(coordinates)
        if norm > 0:
            coordinates = coordinates / norm
            
        # Query the memory manager for similar nodes
        # This is a conceptual implementation - the actual query would depend
        # on the memory manager's capabilities
        query_result = {
            'status': 'success',
            'coordinates': coordinates.tolist(),
            'precision': precision,
            'memory_cells': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Placeholder for memory query logic
        # In a real implementation, this would search through the USKD for nodes
        # with similar coordinate vectors
        
        return query_result
    
    def register_node_in_unified_system(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a node in the unified system.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            Dict containing registration result
        """
        try:
            # Create unified identifier
            unified_id = self.create_unified_identifier(node_data)
            
            # Calculate 13D coordinates
            coordinates = np.array(unified_id['coordinates_13d'])
            
            # If we have a graph manager, add unified metadata to the node
            if self.graph_manager and 'uid' in node_data:
                node_uid = node_data['uid']
                
                # Update node with unified system metadata
                self.graph_manager.update_node_properties(
                    node_uid,
                    {
                        'nuremberg_code': unified_id['nuremberg_code'],
                        'samgov_name': unified_id['samgov_name'],
                        'coordinates_13d': unified_id['coordinates_13d']
                    }
                )
            
            # Log the registration
            self.logger.info(f"[{datetime.now()}] Registered node in unified system: {unified_id['nuremberg_code']}")
            
            return {
                'status': 'success',
                'unified_id': unified_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error registering node in unified system: {str(e)}")
            
            return {
                'status': 'error',
                'message': f"Error registering node: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def find_nodes_by_nuremberg_code(self, nuremberg_code: str) -> List[Dict[str, Any]]:
        """
        Find nodes by Nuremberg code.
        
        Args:
            nuremberg_code: Nuremberg-style code
            
        Returns:
            List of matching nodes
        """
        if not self.graph_manager:
            return []
            
        # Query the graph manager for nodes with the specified Nuremberg code
        nodes = self.graph_manager.get_nodes_by_properties({
            'nuremberg_code': nuremberg_code
        })
        
        return nodes
    
    def find_nodes_by_samgov_name(self, samgov_name: str) -> List[Dict[str, Any]]:
        """
        Find nodes by SAM.gov name.
        
        Args:
            samgov_name: SAM.gov style name
            
        Returns:
            List of matching nodes
        """
        if not self.graph_manager:
            return []
            
        # Query the graph manager for nodes with the specified SAM.gov name
        nodes = self.graph_manager.get_nodes_by_properties({
            'samgov_name': samgov_name
        })
        
        return nodes
    
    def find_nodes_in_coordinate_vicinity(self, coordinates: np.ndarray, 
                                       distance_threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        Find nodes in the vicinity of specified 13D coordinates.
        
        Args:
            coordinates: 13D coordinate vector
            distance_threshold: Maximum Euclidean distance to consider "nearby"
            
        Returns:
            List of nearby nodes
        """
        if not self.graph_manager:
            return []
            
        # In a real implementation, this would need to be efficient
        # possibly using specialized spatial indexing for high-dimensional data
        # This is a conceptual implementation
        nearby_nodes = []
        
        # Get all nodes (in a real system, this would need optimization)
        all_nodes = self.graph_manager.get_all_nodes()
        
        for node in all_nodes:
            if 'coordinates_13d' in node:
                node_coords = np.array(node['coordinates_13d'])
                distance = np.linalg.norm(coordinates - node_coords)
                
                if distance <= distance_threshold:
                    nearby_nodes.append({
                        'node': node,
                        'distance': float(distance)
                    })
        
        # Sort by distance
        nearby_nodes.sort(key=lambda x: x['distance'])
        
        return nearby_nodes
    
    def get_unified_system_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the unified system.
        
        Returns:
            Dict containing system statistics
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            'nuremberg_mapping': self.nuremberg_mapping,
            'samgov_naming': self.samgov_naming,
            'system_status': 'active'
        }
        
        # If we have a graph manager, add node statistics
        if self.graph_manager:
            # Count nodes with unified mappings
            nuremberg_mapped_count = 0
            samgov_mapped_count = 0
            coordinates_mapped_count = 0
            
            all_nodes = self.graph_manager.get_all_nodes()
            
            for node in all_nodes:
                if 'nuremberg_code' in node:
                    nuremberg_mapped_count += 1
                if 'samgov_name' in node:
                    samgov_mapped_count += 1
                if 'coordinates_13d' in node:
                    coordinates_mapped_count += 1
            
            stats['node_stats'] = {
                'total_nodes': len(all_nodes),
                'nuremberg_mapped_nodes': nuremberg_mapped_count,
                'samgov_mapped_nodes': samgov_mapped_count,
                'coordinates_mapped_nodes': coordinates_mapped_count
            }
        
        return stats
