"""
Universal Knowledge Graph - Unified Mapping System

This module implements a unified coordinate system overlay for the 17-axis UKG,
using Nuremberg numbering system, SAM.gov naming conventions, and NASA-inspired 
spatial mapping to create a precise 17-dimensional coordinate system for data localization.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
import numpy as np
from core.coordinate_system import UnifiedCoordinate

class UnifiedMappingSystem:
    """
    Unified Mapping System for the 17-Axis Universal Knowledge Graph
    
    This system provides:
    1. Nuremberg numbering system overlay (UNS integration)
    2. SAM.gov naming conventions (UIDS integration)
    3. NASA-inspired spatial coordinate system for 17D data point mapping
    4. Precise data localization in simulated nested memory system (USKD)
    """
    
    def __init__(self, 
                 uids=None, 
                 uns=None, 
                 crosswalk=None,
                 graph_manager=None, 
                 memory_manager=None, 
                 united_system_manager=None):
        """
        Initialize the Unified Mapping System.
        
        Args:
            uids: Unified Identity Service
            uns: Unified Numbering Service
            crosswalk: Code Crosswalk Service
            graph_manager: Graph Manager for UKG
            memory_manager: Structured Memory Manager
            united_system_manager: United System Manager
        """
        self.logger = logging.getLogger(__name__)
        self.uids = uids
        self.uns = uns
        self.crosswalk = crosswalk
        self.graph_manager = graph_manager
        self.memory_manager = memory_manager
        self.united_system_manager = united_system_manager
        
        # 17D coordinate system basis vectors
        self.coordinate_basis = np.eye(17)
        
        self.logger.info("Initialized Unified Mapping System with 17D coordinate space")
    
    def get_unified_identifier(self, node_data: Dict[str, Any]) -> UnifiedCoordinate:
        """
        Create a UnifiedCoordinate object based on node data and core services.
        """
        coord = UnifiedCoordinate()
        
        # Resolve axis data
        axis_num = node_data.get('axis_number', 0)
        axis_value = node_data.get('axis_value', '')
        
        if 1 <= axis_num <= 17 and axis_value:
            coord.set_axis(
                axis_number=axis_num,
                value=axis_value,
                meta_tag=node_data.get('meta_tag'),
                description=node_data.get('description')
            )
            
        # Add cross-axis influences if available
        if 'cross_axis_relations' in node_data:
            for relation in node_data['cross_axis_relations']:
                rel_axis = relation.get('axis_number')
                rel_val = relation.get('value')
                if rel_axis and 1 <= int(rel_axis) <= 17 and rel_val:
                    coord.set_axis(int(rel_axis), str(rel_val))
                    
        return coord

    def map_external_entity(self, source_system: str, code: str) -> Optional[UnifiedCoordinate]:
        """Map an external entity to a UnifiedCoordinate using the Crosswalk service."""
        if not self.crosswalk:
            return None
            
        match = self.crosswalk.resolve_code(source_system, code)
        if not match:
            return None
            
        from core.coordinate_system import CoordinateParser
        return CoordinateParser.parse_full_coordinate(match['coord'])

    def calculate_17d_vector(self, coord: UnifiedCoordinate) -> np.ndarray:
        """
        Calculate a 17-dimensional vector representation for a coordinate.
        """
        vector = np.zeros(17)
        for axis_num, axis_coord in coord.coordinates.items():
            # Magnitude based on hierarchical depth (more specific = higher localized magnitude)
            magnitude = 1.0 + (axis_coord.depth * 0.1)
            vector[axis_num - 1] = magnitude
            
        # Normalize the vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector

    def register_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a node into the Unified System.
        """
        try:
            # 1. Identity Resolution
            ukgid = None
            if self.uids:
                aliases = node_data.get('aliases', {})
                # Try to resolve first
                for a_type, a_val in aliases.items():
                    ukgid = self.uids.resolve_ukgid(a_type, a_val)
                    if ukgid: break
                
                if not ukgid:
                    ukgid = self.uids.register_entity(
                        name=node_data.get('name', 'Unnamed Node'),
                        entity_type=node_data.get('entity_type', 'node'),
                        aliases=aliases,
                        metadata=node_data.get('metadata')
                    )
            
            # 2. Coordinate Mapping
            coord = self.get_unified_identifier(node_data)
            coord.node_id = ukgid or coord.node_id
            
            # 3. Numbering Resolution
            nuremberg_paths = []
            if self.uns:
                for axis_num, axis_coord in coord.coordinates.items():
                    path = self.uns.format_path(axis_num, axis_coord.levels)
                    nuremberg_paths.append(path)
            
            # 4. Graph Update
            if self.graph_manager and 'uid' in node_data:
                node_uid = node_data['uid']
                self.graph_manager.update_node_properties(
                    node_uid,
                    {
                        'ukgid': ukgid,
                        'coord17': coord.to_coordinate_string(),
                        'nuremberg_paths': nuremberg_paths,
                        'vector17': self.calculate_17d_vector(coord).tolist()
                    }
                )
            
            return {
                "status": "success",
                "ukgid": ukgid,
                "coord17": coord.to_coordinate_string(),
                "nuremberg_paths": nuremberg_paths,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error registering node: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_coordinate_context(self, axis: int, path: str) -> Dict[str, Any]:
        """
        Retrieve context and metadata for a specific coordinate on an axis.
        Used to seed personas with specific expertise traits.
        """
        self.logger.debug(f"Fetching context for Axis {axis}, Path {path}")
        
        # 1. Resolve label via UNS
        label = "Unknown Context"
        if self.uns:
            full_path = self.uns.format_path(axis, path.split("."))
            label = self.uns.resolve_label(full_path)
            
        # 2. Mock context logic (in production, this would hit the Knowledge Graph)
        context = {
            "axis": axis,
            "coordinate": path,
            "label": label,
            "description": f"Standard {label} domain expertise.",
            "meta_tags": ["hardened", "v7.4"],
            "pillar_name": label.split(" ")[0] if " " in label else label
        }
        
        # Axis-specific enrichments
        if axis == 1:
            context["pillar_type"] = "Knowledge Base"
        elif axis == 2:
            context["industry_sector"] = label
        elif axis == 6:
            context["links"] = [f"Regulatory_Framework_{path}"]
        elif axis == 7:
            context["crosswalks"] = [f"Standard_Mapping_{path}"]
            
        return context

    def locate_in_uskd(self, coord: UnifiedCoordinate, search_radius: float = 0.2) -> List[Dict[str, Any]]:
        """
        Find nearby nodes in the USKD simulated memory space.
        """
        target_vector = self.calculate_17d_vector(coord)
        
        if not self.graph_manager:
            return []
            
        results = []
        all_nodes = self.graph_manager.get_all_nodes()
        
        for node in all_nodes:
            if 'vector17' in node:
                node_vector = np.array(node['vector17'])
                distance = np.linalg.norm(target_vector - node_vector)
                if distance <= search_radius:
                    results.append({"node": node, "distance": float(distance)})
                    
        results.sort(key=lambda x: x['distance'])
        return results

    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the 17-axis mapping coverage."""
        stats = {
            'timestamp': datetime.now(UTC).isoformat(),
            'axis_count': 17,
            'status': 'active'
        }
        
        if self.graph_manager:
            all_nodes = self.graph_manager.get_all_nodes()
            mapped_count = sum(1 for n in all_nodes if 'coord17' in n)
            stats['node_stats'] = {
                'total': len(all_nodes),
                'mapped': mapped_count,
                'coverage': mapped_count / len(all_nodes) if all_nodes else 0
            }
            
        return stats
