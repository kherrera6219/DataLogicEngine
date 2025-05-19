
"""
UKG Axis System

This module provides the central coordination point for the 13-Axis Universal Knowledge Graph (UKG) system.
It handles cross-axis relationships, context resolution, and coordinates between different axes.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class AxisSystem:
    """
    Central coordinator for the 13-Axis Universal Knowledge Graph (UKG) system.
    
    The AxisSystem is responsible for:
    - Managing relationships between axes
    - Resolving multi-dimensional contexts
    - Coordinating cross-axis queries and operations
    - Maintaining high-level system integrity
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Axis System.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Track individual axis managers
        self.axis_managers = {}
        
        # Define the 13 axes
        self.axes = {
            1: {"name": "Pillar Levels", "description": "Hierarchical knowledge organization"},
            2: {"name": "Sectors", "description": "Industry sectors and market segments"},
            3: {"name": "Branches", "description": "Specialization branches within sectors"},
            4: {"name": "Methods", "description": "Methodologies and approaches"},
            5: {"name": "Tools", "description": "Tools, applications, and instruments"},
            6: {"name": "Regulatory Frameworks", "description": "Laws and regulations"},
            7: {"name": "Compliance Standards", "description": "Industry standards and best practices"},
            8: {"name": "Knowledge Experts", "description": "Domain expertise"},
            9: {"name": "Skill Experts", "description": "Skill-based expertise"},
            10: {"name": "Role Experts", "description": "Role-based expertise"},
            11: {"name": "Context Experts", "description": "Situational expertise"},
            12: {"name": "Locations", "description": "Geographic and jurisdictional locations"},
            13: {"name": "Time", "description": "Temporal dimensions"}
        }
    
    def register_axis_manager(self, axis_number: int, manager: Any) -> None:
        """
        Register an individual axis manager with the system.
        
        Args:
            axis_number: The axis number (1-13)
            manager: The axis manager instance
        """
        if 1 <= axis_number <= 13:
            self.axis_managers[axis_number] = manager
            self.logging.info(f"[{datetime.now()}] Registered axis manager for Axis {axis_number}: {self.axes[axis_number]['name']}")
        else:
            self.logging.error(f"[{datetime.now()}] Invalid axis number: {axis_number}")
    
    def resolve_multi_axis_context(self, query_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a multi-dimensional context across multiple axes.
        
        Args:
            query_context: Dictionary containing context elements for different axes
            
        Returns:
            Dict containing the resolved context
        """
        self.logging.info(f"[{datetime.now()}] Resolving multi-axis context")
        
        resolved_context = {
            'axes': {},
            'confidence': {},
            'cross_axis_relationships': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Process each axis in the query context
            for axis_num, axis_data in query_context.items():
                axis_num = int(axis_num) if isinstance(axis_num, str) and axis_num.isdigit() else axis_num
                
                if isinstance(axis_num, int) and 1 <= axis_num <= 13:
                    # If we have a manager for this axis, use it to resolve
                    if axis_num in self.axis_managers:
                        axis_manager = self.axis_managers[axis_num]
                        
                        # Call appropriate resolution method based on axis
                        if hasattr(axis_manager, 'resolve_context'):
                            axis_result = axis_manager.resolve_context(axis_data)
                            resolved_context['axes'][axis_num] = axis_result
                            
                            # Track confidence of this resolution
                            if 'confidence' in axis_result:
                                resolved_context['confidence'][axis_num] = axis_result['confidence']
                        else:
                            # Basic resolution if no specific method
                            resolved_context['axes'][axis_num] = {
                                'data': axis_data,
                                'status': 'basic_resolution',
                                'confidence': 0.7
                            }
                            resolved_context['confidence'][axis_num] = 0.7
                    else:
                        # No manager, just store the data
                        resolved_context['axes'][axis_num] = {
                            'data': axis_data,
                            'status': 'unmanaged',
                            'confidence': 0.5
                        }
                        resolved_context['confidence'][axis_num] = 0.5
            
            # Calculate overall context confidence (weighted average)
            if resolved_context['confidence']:
                resolved_context['overall_confidence'] = sum(resolved_context['confidence'].values()) / len(resolved_context['confidence'])
            else:
                resolved_context['overall_confidence'] = 0.0
            
            # Find cross-axis relationships when we have multiple axes
            if len(resolved_context['axes']) > 1 and self.graph_manager:
                resolved_context['cross_axis_relationships'] = self._find_cross_axis_relationships(resolved_context['axes'])
            
            resolved_context['status'] = 'success'
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error resolving multi-axis context: {str(e)}")
            resolved_context['status'] = 'error'
            resolved_context['error'] = str(e)
            resolved_context['overall_confidence'] = 0.0
        
        return resolved_context
    
    def _find_cross_axis_relationships(self, axes_data: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find relationships between nodes across different axes.
        
        Args:
            axes_data: Dictionary of resolved axis data
            
        Returns:
            List of cross-axis relationships
        """
        relationships = []
        
        try:
            # Get all node UIDs from the axes data
            node_uids_by_axis = {}
            for axis_num, axis_data in axes_data.items():
                if 'nodes' in axis_data:
                    node_uids_by_axis[axis_num] = [
                        node['uid'] for node in axis_data['nodes'] 
                        if 'uid' in node
                    ]
                elif 'node' in axis_data and 'uid' in axis_data['node']:
                    node_uids_by_axis[axis_num] = [axis_data['node']['uid']]
                elif 'uid' in axis_data.get('data', {}):
                    node_uids_by_axis[axis_num] = [axis_data['data']['uid']]
            
            # For each pair of axes, find relationships
            for axis1, uids1 in node_uids_by_axis.items():
                for axis2, uids2 in node_uids_by_axis.items():
                    if axis1 < axis2:  # Avoid duplicate checks
                        for uid1 in uids1:
                            for uid2 in uids2:
                                # Check for direct relationships
                                edges = self.graph_manager.get_edges_between(uid1, uid2)
                                for edge in edges:
                                    relationships.append({
                                        'type': 'direct',
                                        'source_axis': axis1,
                                        'target_axis': axis2,
                                        'source_uid': uid1,
                                        'target_uid': uid2,
                                        'edge': edge
                                    })
                                
                                # Check for common connections (nodes that relate to both)
                                if len(relationships) == 0:
                                    common_connections = self._find_common_connections(uid1, uid2)
                                    for conn in common_connections:
                                        relationships.append({
                                            'type': 'common_connection',
                                            'source_axis': axis1,
                                            'target_axis': axis2,
                                            'source_uid': uid1,
                                            'target_uid': uid2,
                                            'connecting_node': conn
                                        })
        
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding cross-axis relationships: {str(e)}")
        
        return relationships
    
    def _find_common_connections(self, uid1: str, uid2: str) -> List[Dict[str, Any]]:
        """
        Find nodes that are connected to both uid1 and uid2.
        
        Args:
            uid1: First node UID
            uid2: Second node UID
            
        Returns:
            List of common connections
        """
        common_connections = []
        
        try:
            # Get all nodes connected to uid1
            connected_to_uid1 = set()
            outgoing_edges1 = self.graph_manager.get_outgoing_edges(uid1)
            for edge in outgoing_edges1:
                connected_to_uid1.add(edge['target_id'])
            
            incoming_edges1 = self.graph_manager.get_incoming_edges(uid1)
            for edge in incoming_edges1:
                connected_to_uid1.add(edge['source_id'])
            
            # Get all nodes connected to uid2
            connected_to_uid2 = set()
            outgoing_edges2 = self.graph_manager.get_outgoing_edges(uid2)
            for edge in outgoing_edges2:
                connected_to_uid2.add(edge['target_id'])
            
            incoming_edges2 = self.graph_manager.get_incoming_edges(uid2)
            for edge in incoming_edges2:
                connected_to_uid2.add(edge['source_id'])
            
            # Find intersection
            common_uids = connected_to_uid1.intersection(connected_to_uid2)
            
            # Get node details for common connections
            for common_uid in common_uids:
                node = self.graph_manager.get_node(common_uid)
                if node:
                    common_connections.append(node)
        
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding common connections: {str(e)}")
        
        return common_connections
    
    def map_branch_to_classification(self, branch_id: str, 
                                  classification_system: str, 
                                  code: str) -> Dict[str, Any]:
        """
        Map a branch to a specific classification system code.
        
        Args:
            branch_id: Branch ID
            classification_system: Classification system (naics, sic, psc, nic)
            code: Classification code
            
        Returns:
            Dict containing mapping result
        """
        self.logging.info(f"[{datetime.now()}] Mapping branch {branch_id} to {classification_system} code {code}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get branch node
            branch_node = self.db_manager.get_node_by_id(branch_id)
            if not branch_node:
                return {
                    'status': 'error',
                    'message': f'Branch not found: {branch_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create classification node if it doesn't exist
            classification_id = f"{classification_system.upper()}_{code}"
            classification_node = self.db_manager.get_node_by_id(classification_id)
            
            if not classification_node:
                classification_node = self.db_manager.add_node({
                    'uid': f"{classification_system.upper()}_{code}_{uuid.uuid4().hex[:8]}",
                    'id': classification_id,
                    'node_type': 'classification_code',
                    'system': classification_system.upper(),
                    'code': code,
                    'axis_number': 3,  # Branch system is Axis 3
                    'created_at': datetime.now().isoformat()
                })
            
            # Create mapping relationship
            edge_id = f"EDGE_{branch_id}_TO_{classification_id}"
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'id': edge_id,
                'source_id': branch_node['uid'],
                'target_id': classification_node['uid'],
                'edge_type': 'mapped_to_classification',
                'attributes': {
                    'system': classification_system.upper(),
                    'confidence': 1.0
                }
            }
            
            # Check if mapping already exists
            existing_edges = self.db_manager.get_edges_between(
                branch_node['uid'], 
                classification_node['uid'], 
                ['mapped_to_classification']
            )
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Mapping already exists',
                    'edge': existing_edges[0],
                    'branch': branch_node,
                    'classification': classification_node,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add edge
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'branch': branch_node,
                'classification': classification_node,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error mapping branch to classification: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error mapping branch to classification: {str(e)}",
                'branch_id': branch_id,
                'classification': f"{classification_system}_{code}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_branch_by_classification(self, classification_system: str, 
                                  code: str) -> Dict[str, Any]:
        """
        Get branches mapped to a specific classification system code.
        
        Args:
            classification_system: Classification system (naics, sic, psc, nic)
            code: Classification code
            
        Returns:
            Dict containing branches mapped to the classification
        """
        self.logging.info(f"[{datetime.now()}] Getting branches for {classification_system} code {code}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find classification node
            classification_nodes = self.db_manager.get_nodes_by_properties({
                'node_type': 'classification_code',
                'system': classification_system.upper(),
                'code': code
            })
            
            if not classification_nodes:
                return {
                    'status': 'not_found',
                    'message': f'Classification not found: {classification_system} {code}',
                    'timestamp': datetime.now().isoformat()
                }
            
            classification_node = classification_nodes[0]
            
            # Find branches mapped to this classification
            incoming_edges = self.db_manager.get_incoming_edges(
                classification_node['uid'], 
                ['mapped_to_classification']
            )
            
            branches = []
            for edge in incoming_edges:
                branch_node = self.db_manager.get_node(edge['source_id'])
                if branch_node:
                    branches.append({
                        'branch': branch_node,
                        'edge': edge
                    })
            
            return {
                'status': 'success',
                'classification': classification_node,
                'branches': branches,
                'branch_count': len(branches),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting branches by classification: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting branches by classification: {str(e)}",
                'classification': f"{classification_system}_{code}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_pl_sector_branch_mapping(self, pillar_level_id: str) -> Dict[str, Any]:
        """
        Get the complete mapping between Pillar Level (Axis 1), Sectors (Axis 2),
        and Branches (Axis 3) for a specific Pillar Level.
        
        Args:
            pillar_level_id: Pillar Level ID
            
        Returns:
            Dict containing the mapping structure
        """
        self.logging.info(f"[{datetime.now()}] Getting PL-Sector-Branch mapping for PL: {pillar_level_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get pillar level
            pillar_level = self.db_manager.get_node_by_id(pillar_level_id)
            if not pillar_level:
                return {
                    'status': 'error',
                    'message': f'Pillar Level not found: {pillar_level_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find sectors related to this pillar level
            sector_mapping = {}
            
            # Get direct sector relationships
            pl_sector_edges = self.graph_manager.get_outgoing_edges(
                pillar_level['uid'], 
                ['applies_to_sector', 'knowledge_application']
            )
            
            for edge in pl_sector_edges:
                sector_uid = edge['target_id']
                sector_node = self.db_manager.get_node(sector_uid)
                
                if sector_node and sector_node.get('node_type') == 'sector':
                    sector_id = sector_node.get('id')
                    
                    if sector_id not in sector_mapping:
                        sector_mapping[sector_id] = {
                            'sector': sector_node,
                            'relation': edge,
                            'branches': {}
                        }
                    
                    # Get branches for this sector
                    self._populate_sector_branches(sector_uid, sector_mapping[sector_id]['branches'])
            
            # If no direct relationships, try to find sectors that implement this pillar level
            if not sector_mapping:
                # Look for sectors that implement knowledge from this pillar level
                pl_knowledge_edges = self.graph_manager.get_outgoing_edges(
                    pillar_level['uid'],
                    ['has_knowledge']
                )
                
                for edge in pl_knowledge_edges:
                    knowledge_uid = edge['target_id']
                    
                    # Find sectors that implement this knowledge
                    knowledge_sector_edges = self.graph_manager.get_outgoing_edges(
                        knowledge_uid,
                        ['implemented_by']
                    )
                    
                    for ks_edge in knowledge_sector_edges:
                        sector_uid = ks_edge['target_id']
                        sector_node = self.db_manager.get_node(sector_uid)
                        
                        if sector_node and sector_node.get('node_type') == 'sector':
                            sector_id = sector_node.get('id')
                            
                            if sector_id not in sector_mapping:
                                sector_mapping[sector_id] = {
                                    'sector': sector_node,
                                    'relation': ks_edge,
                                    'via_knowledge': knowledge_uid,
                                    'branches': {}
                                }
                            
                            # Get branches for this sector
                            self._populate_sector_branches(sector_uid, sector_mapping[sector_id]['branches'])
            
            return {
                'status': 'success',
                'pillar_level': pillar_level,
                'sector_count': len(sector_mapping),
                'sector_mappings': sector_mapping,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting PL-Sector-Branch mapping: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting PL-Sector-Branch mapping: {str(e)}",
                'pillar_level_id': pillar_level_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def _populate_sector_branches(self, sector_uid: str, branches_dict: Dict[str, Any]) -> None:
        """
        Populate the branches dictionary for a sector.
        
        Args:
            sector_uid: Sector UID
            branches_dict: Dictionary to populate with branches
        """
        # Get large branches for this sector
        large_branch_edges = self.graph_manager.get_outgoing_edges(
            sector_uid,
            ['has_branch']
        )
        
        for lb_edge in large_branch_edges:
            large_branch_uid = lb_edge['target_id']
            large_branch_node = self.db_manager.get_node(large_branch_uid)
            
            if large_branch_node and large_branch_node.get('branch_type') == 'large':
                large_branch_id = large_branch_node.get('id')
                
                if large_branch_id not in branches_dict:
                    branches_dict[large_branch_id] = {
                        'branch': large_branch_node,
                        'relation': lb_edge,
                        'medium_branches': {}
                    }
                
                # Get medium branches for this large branch
                medium_branch_edges = self.graph_manager.get_outgoing_edges(
                    large_branch_uid,
                    ['has_branch']
                )
                
                for mb_edge in medium_branch_edges:
                    medium_branch_uid = mb_edge['target_id']
                    medium_branch_node = self.db_manager.get_node(medium_branch_uid)
                    
                    if medium_branch_node and medium_branch_node.get('branch_type') == 'medium':
                        medium_branch_id = medium_branch_node.get('id')
                        
                        if medium_branch_id not in branches_dict[large_branch_id]['medium_branches']:
                            branches_dict[large_branch_id]['medium_branches'][medium_branch_id] = {
                                'branch': medium_branch_node,
                                'relation': mb_edge,
                                'small_branches': {}
                            }
                        
                        # Get small branches for this medium branch
                        small_branch_edges = self.graph_manager.get_outgoing_edges(
                            medium_branch_uid,
                            ['has_branch']
                        )
                        
                        for sb_edge in small_branch_edges:
                            small_branch_uid = sb_edge['target_id']
                            small_branch_node = self.db_manager.get_node(small_branch_uid)
                            
                            if small_branch_node and small_branch_node.get('branch_type') == 'small':
                                small_branch_id = small_branch_node.get('id')
                                
                                branches_dict[large_branch_id]['medium_branches'][medium_branch_id]['small_branches'][small_branch_id] = {
                                    'branch': small_branch_node,
                                    'relation': sb_edge,
                                    'granular_branches': {}
                                }
                                
                                # Get granular branches if they exist
                                granular_branch_edges = self.graph_manager.get_outgoing_edges(
                                    small_branch_uid,
                                    ['has_branch']
                                )
                                
                                for gb_edge in granular_branch_edges:
                                    granular_branch_uid = gb_edge['target_id']
                                    granular_branch_node = self.db_manager.get_node(granular_branch_uid)
                                    
                                    if granular_branch_node and granular_branch_node.get('branch_type') == 'granular':
                                        granular_branch_id = granular_branch_node.get('id')
                                        
                                        branches_dict[large_branch_id]['medium_branches'][medium_branch_id]['small_branches'][small_branch_id]['granular_branches'][granular_branch_id] = {
                                            'branch': granular_branch_node,
                                            'relation': gb_edge
                                        }
