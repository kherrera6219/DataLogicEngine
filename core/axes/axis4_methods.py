
"""
UKG Axis 4: Methods

This module implements the Methods axis of the Universal Knowledge Graph (UKG) system.
The Methods axis manages methodologies, approaches, and cross-sector techniques that
connect different pillars and sectors within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class MethodsManager:
    """
    Methods Manager for the UKG System
    
    Responsible for managing Axis 4 (Methods) functionality, including:
    - Hierarchical node structures (mega, large, medium, small)
    - Cross-cutting methodologies that span multiple sectors and pillars
    - Techniques and approaches for knowledge application
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Methods Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Node hierarchy types
        self.node_types = {
            "mega": "Mega methodology node (broadest classification)",
            "large": "Large methodology node (major methodological category)",
            "medium": "Medium methodology node (specific methodology group)",
            "small": "Small methodology node (concrete methodology)",
            "granular": "Granular methodology node (specific implementation or technique)"
        }
    
    def register_method_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new method node in the system.
        
        Args:
            node_data: Method node data dictionary
            
        Returns:
            Dict containing registration result
        """
        self.logging.info(f"[{datetime.now()}] Registering method node: {node_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate required fields
            required_fields = ['label', 'node_type', 'node_id']
            for field in required_fields:
                if field not in node_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Validate node type
            if node_data['node_type'] not in self.node_types:
                return {
                    'status': 'error',
                    'message': f'Invalid node type: {node_data["node_type"]}. Must be one of: {", ".join(self.node_types.keys())}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Set axis number for Methods axis
            node_data['axis_number'] = 4
            
            # Generate UID if not provided
            if 'uid' not in node_data:
                prefix = node_data['node_type'][:2].upper()  # ME, LA, ME, SM, GR
                node_data['uid'] = f"M4_{prefix}_{node_data['node_id']}_{uuid.uuid4().hex[:8]}"
            
            # Check if node already exists
            existing_node = self.db_manager.get_node_by_id(node_data['node_id'])
            if existing_node:
                return {
                    'status': 'exists',
                    'message': 'Method node already exists',
                    'node': existing_node,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add node to database
            new_node = self.db_manager.add_node(node_data)
            
            return {
                'status': 'success',
                'node': new_node,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error registering method node: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error registering method node: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def establish_node_hierarchy(self, parent_id: str, child_id: str) -> Dict[str, Any]:
        """
        Establish a hierarchical relationship between method nodes.
        
        Args:
            parent_id: Parent node ID
            child_id: Child node ID
            
        Returns:
            Dict containing result
        """
        self.logging.info(f"[{datetime.now()}] Establishing node hierarchy: {parent_id} -> {child_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get nodes
            parent_node = self.db_manager.get_node_by_id(parent_id)
            child_node = self.db_manager.get_node_by_id(child_id)
            
            if not parent_node or not child_node:
                return {
                    'status': 'error',
                    'message': 'Parent or child node not found',
                    'parent_id': parent_id,
                    'child_id': child_id,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate node types to ensure proper hierarchy
            parent_type = parent_node.get('node_type')
            child_type = child_node.get('node_type')
            
            # Define valid parent-child relationships
            valid_hierarchies = {
                'mega': ['large'],
                'large': ['medium'],
                'medium': ['small'],
                'small': ['granular']
            }
            
            if parent_type not in valid_hierarchies or child_type not in valid_hierarchies.get(parent_type, []):
                return {
                    'status': 'error',
                    'message': f'Invalid hierarchy: {parent_type} cannot be parent of {child_type}',
                    'valid_hierarchies': valid_hierarchies,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if relationship already exists
            existing_edges = self.db_manager.get_edges_between(
                parent_node['uid'], 
                child_node['uid'],
                ['has_method']
            )
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Relationship already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create edge
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': parent_node['uid'],
                'target_id': child_node['uid'],
                'edge_type': 'has_method',
                'attributes': {
                    'parent_type': parent_type,
                    'child_type': child_type
                }
            }
            
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'parent': parent_node,
                'child': child_node,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error establishing node hierarchy: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error establishing node hierarchy: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def link_method_to_pillar(self, method_id: str, pillar_id: str, 
                           strength: float = 1.0) -> Dict[str, Any]:
        """
        Link a method to a pillar level.
        
        Args:
            method_id: Method node ID
            pillar_id: Pillar level ID
            strength: Relationship strength (0.0-1.0)
            
        Returns:
            Dict containing result
        """
        self.logging.info(f"[{datetime.now()}] Linking method to pillar: {method_id} -> {pillar_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get nodes
            method_node = self.db_manager.get_node_by_id(method_id)
            pillar_node = self.db_manager.get_node_by_id(pillar_id)
            
            if not method_node or not pillar_node:
                return {
                    'status': 'error',
                    'message': 'Method or pillar not found',
                    'method_id': method_id,
                    'pillar_id': pillar_id,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check node types
            if method_node.get('axis_number') != 4 or pillar_node.get('axis_number') != 1:
                return {
                    'status': 'error',
                    'message': 'Invalid node types: must link Method (Axis 4) to Pillar (Axis 1)',
                    'method_axis': method_node.get('axis_number'),
                    'pillar_axis': pillar_node.get('axis_number'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if relationship already exists
            existing_edges = self.db_manager.get_edges_between(
                method_node['uid'], 
                pillar_node['uid'],
                ['applies_to_pillar']
            )
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Relationship already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create edge
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': method_node['uid'],
                'target_id': pillar_node['uid'],
                'edge_type': 'applies_to_pillar',
                'attributes': {
                    'strength': strength,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'method': method_node,
                'pillar': pillar_node,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking method to pillar: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking method to pillar: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def link_method_to_sector(self, method_id: str, sector_id: str, 
                           strength: float = 1.0) -> Dict[str, Any]:
        """
        Link a method to a sector.
        
        Args:
            method_id: Method node ID
            sector_id: Sector ID
            strength: Relationship strength (0.0-1.0)
            
        Returns:
            Dict containing result
        """
        self.logging.info(f"[{datetime.now()}] Linking method to sector: {method_id} -> {sector_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get nodes
            method_node = self.db_manager.get_node_by_id(method_id)
            sector_node = self.db_manager.get_node_by_id(sector_id)
            
            if not method_node or not sector_node:
                return {
                    'status': 'error',
                    'message': 'Method or sector not found',
                    'method_id': method_id,
                    'sector_id': sector_id,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check node types
            if method_node.get('axis_number') != 4 or sector_node.get('axis_number') != 2:
                return {
                    'status': 'error',
                    'message': 'Invalid node types: must link Method (Axis 4) to Sector (Axis 2)',
                    'method_axis': method_node.get('axis_number'),
                    'sector_axis': sector_node.get('axis_number'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if relationship already exists
            existing_edges = self.db_manager.get_edges_between(
                method_node['uid'], 
                sector_node['uid'],
                ['applied_in_sector']
            )
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Relationship already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create edge
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': method_node['uid'],
                'target_id': sector_node['uid'],
                'edge_type': 'applied_in_sector',
                'attributes': {
                    'strength': strength,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'method': method_node,
                'sector': sector_node,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking method to sector: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking method to sector: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_method_hierarchy(self, node_id: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Get the hierarchical structure for a method node.
        
        Args:
            node_id: Method node ID
            max_depth: Maximum hierarchy depth to retrieve
            
        Returns:
            Dict containing hierarchical structure
        """
        self.logging.info(f"[{datetime.now()}] Getting method hierarchy for: {node_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get the node
            node = self.db_manager.get_node_by_id(node_id)
            if not node:
                return {
                    'status': 'error',
                    'message': f'Method node not found: {node_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Build hierarchy downward (children)
            hierarchy = {
                'node': node,
                'children': self._get_child_nodes(node['uid'], 1, max_depth)
            }
            
            # Get parent nodes
            parent_nodes = self._get_parent_nodes(node['uid'])
            
            return {
                'status': 'success',
                'hierarchy': hierarchy,
                'parents': parent_nodes,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting method hierarchy: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting method hierarchy: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_child_nodes(self, node_uid: str, current_depth: int, max_depth: int) -> List[Dict[str, Any]]:
        """
        Recursively get child nodes.
        
        Args:
            node_uid: Parent node UID
            current_depth: Current depth in hierarchy
            max_depth: Maximum depth to traverse
            
        Returns:
            List of child nodes with their hierarchies
        """
        if current_depth > max_depth:
            return []
        
        # Get outgoing edges of type 'has_method'
        edges = self.db_manager.get_outgoing_edges(node_uid, ['has_method'])
        children = []
        
        for edge in edges:
            child_uid = edge['target_id']
            child_node = self.db_manager.get_node(child_uid)
            
            if child_node:
                # Recursive call to get next level
                child_hierarchy = {
                    'node': child_node,
                    'relation': edge,
                    'children': self._get_child_nodes(child_uid, current_depth + 1, max_depth)
                }
                children.append(child_hierarchy)
        
        return children
    
    def _get_parent_nodes(self, node_uid: str) -> List[Dict[str, Any]]:
        """
        Get parent nodes.
        
        Args:
            node_uid: Child node UID
            
        Returns:
            List of parent nodes
        """
        # Get incoming edges of type 'has_method'
        edges = self.db_manager.get_incoming_edges(node_uid, ['has_method'])
        parents = []
        
        for edge in edges:
            parent_uid = edge['source_id']
            parent_node = self.db_manager.get_node(parent_uid)
            
            if parent_node:
                parents.append({
                    'node': parent_node,
                    'relation': edge
                })
        
        return parents
    
    def find_cross_sector_methods(self, sector_ids: List[str]) -> Dict[str, Any]:
        """
        Find methods that are applied across multiple specified sectors.
        
        Args:
            sector_ids: List of sector IDs
            
        Returns:
            Dict containing cross-sector methods
        """
        self.logging.info(f"[{datetime.now()}] Finding cross-sector methods across {len(sector_ids)} sectors")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            if not sector_ids:
                return {
                    'status': 'error',
                    'message': 'No sector IDs provided',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get all sectors
            sectors = []
            for sector_id in sector_ids:
                sector = self.db_manager.get_node_by_id(sector_id)
                if sector:
                    sectors.append(sector)
            
            if not sectors:
                return {
                    'status': 'error',
                    'message': 'No valid sectors found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find methods that connect to all sectors
            all_methods = {}
            sector_method_map = {}
            
            # First, gather all methods for each sector
            for sector in sectors:
                sector_uid = sector['uid']
                incoming_edges = self.db_manager.get_incoming_edges(sector_uid, ['applied_in_sector'])
                
                sector_methods = []
                for edge in incoming_edges:
                    method_uid = edge['source_id']
                    method_node = self.db_manager.get_node(method_uid)
                    
                    if method_node and method_node.get('axis_number') == 4:
                        method_id = method_node.get('node_id')
                        
                        if method_id not in all_methods:
                            all_methods[method_id] = {
                                'node': method_node,
                                'sectors': [sector['node_id']],
                                'edges': [edge]
                            }
                        else:
                            all_methods[method_id]['sectors'].append(sector['node_id'])
                            all_methods[method_id]['edges'].append(edge)
                        
                        sector_methods.append(method_id)
                
                sector_method_map[sector['node_id']] = sector_methods
            
            # Find methods that exist in all specified sectors
            cross_sector_methods = []
            for method_id, method_data in all_methods.items():
                if len(method_data['sectors']) == len(sectors):
                    # This method applies to all specified sectors
                    cross_sector_methods.append(method_data)
            
            return {
                'status': 'success',
                'sectors': [s['node_id'] for s in sectors],
                'cross_sector_methods': cross_sector_methods,
                'method_count': len(cross_sector_methods),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding cross-sector methods: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding cross-sector methods: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def find_cross_pillar_methods(self, pillar_ids: List[str]) -> Dict[str, Any]:
        """
        Find methods that are applied across multiple specified pillar levels.
        
        Args:
            pillar_ids: List of pillar level IDs
            
        Returns:
            Dict containing cross-pillar methods
        """
        self.logging.info(f"[{datetime.now()}] Finding cross-pillar methods across {len(pillar_ids)} pillars")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            if not pillar_ids:
                return {
                    'status': 'error',
                    'message': 'No pillar IDs provided',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Similar logic to cross-sector methods, but with pillar levels
            # Get all pillars
            pillars = []
            for pillar_id in pillar_ids:
                pillar = self.db_manager.get_node_by_id(pillar_id)
                if pillar:
                    pillars.append(pillar)
            
            if not pillars:
                return {
                    'status': 'error',
                    'message': 'No valid pillars found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find methods that connect to all pillars
            all_methods = {}
            
            # First, gather all methods for each pillar
            for pillar in pillars:
                pillar_uid = pillar['uid']
                incoming_edges = self.db_manager.get_incoming_edges(pillar_uid, ['applies_to_pillar'])
                
                for edge in incoming_edges:
                    method_uid = edge['source_id']
                    method_node = self.db_manager.get_node(method_uid)
                    
                    if method_node and method_node.get('axis_number') == 4:
                        method_id = method_node.get('node_id')
                        
                        if method_id not in all_methods:
                            all_methods[method_id] = {
                                'node': method_node,
                                'pillars': [pillar['node_id']],
                                'edges': [edge]
                            }
                        else:
                            all_methods[method_id]['pillars'].append(pillar['node_id'])
                            all_methods[method_id]['edges'].append(edge)
            
            # Find methods that exist in all specified pillars
            cross_pillar_methods = []
            for method_id, method_data in all_methods.items():
                if len(method_data['pillars']) == len(pillars):
                    # This method applies to all specified pillars
                    cross_pillar_methods.append(method_data)
            
            return {
                'status': 'success',
                'pillars': [p['node_id'] for p in pillars],
                'cross_pillar_methods': cross_pillar_methods,
                'method_count': len(cross_pillar_methods),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding cross-pillar methods: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding cross-pillar methods: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
