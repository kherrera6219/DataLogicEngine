"""
UKG Axis 2: Sector

This module implements the Sector axis of the Universal Knowledge Graph (UKG) system.
The Sector axis manages industry sectors, classifications, and sector-specific knowledge
organization within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class SectorManager:
    """
    Sector Manager for the UKG System
    
    Responsible for managing Axis 2 (Sector) functionality, including:
    - Industry classification systems (NAICS, SIC, PSC, NACE, etc.)
    - Sector hierarchies and relationships
    - Cross-sector mappings and equivalences
    - Sector-specific knowledge organization
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Sector Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Common industry classification systems
        self.classification_systems = {
            "naics": "North American Industry Classification System",
            "sic": "Standard Industrial Classification",
            "psc": "Product and Service Codes",
            "nace": "Statistical Classification of Economic Activities in the European Community",
            "isic": "International Standard Industrial Classification",
            "gics": "Global Industry Classification Standard",
            "unspsc": "United Nations Standard Products and Services Code"
        }
    
    def register_sector(self, sector_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new sector in the system.
        
        Args:
            sector_data: Sector data dictionary
            
        Returns:
            Dict containing registration result
        """
        self.logging.info(f"[{datetime.now()}] Registering sector: {sector_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure sector has required fields
            required_fields = ['label', 'classification_system', 'code']
            for field in required_fields:
                if field not in sector_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Generate UID if not provided
            if 'uid' not in sector_data:
                # Create a structured sector ID
                classification = sector_data['classification_system'].lower()
                code = sector_data['code']
                sector_data['uid'] = f"sector_{classification}_{code}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Sector axis
            sector_data['axis_number'] = 2
            sector_data['node_type'] = 'sector'
            
            # Check if sector already exists
            existing_sector = self.db_manager.get_nodes_by_properties({
                'node_type': 'sector',
                'classification_system': sector_data['classification_system'],
                'code': sector_data['code']
            })
            
            if existing_sector:
                return {
                    'status': 'exists',
                    'message': 'Sector already exists',
                    'sector': existing_sector[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add sector to database
            new_sector = self.db_manager.add_node(sector_data)
            
            return {
                'status': 'success',
                'sector': new_sector,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error registering sector: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error registering sector: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_sector_by_code(self, classification_system: str, code: str) -> Dict[str, Any]:
        """
        Get a sector by its classification system and code.
        
        Args:
            classification_system: Classification system (e.g., naics, sic)
            code: Sector code
            
        Returns:
            Dict containing sector information
        """
        self.logging.info(f"[{datetime.now()}] Getting sector by code: {classification_system} {code}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Normalize classification system
            classification_system = classification_system.lower()
            
            # Check if classification system is valid
            if classification_system not in self.classification_systems:
                return {
                    'status': 'error',
                    'message': f'Invalid classification system: {classification_system}',
                    'valid_systems': list(self.classification_systems.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find sector by classification system and code
            sectors = self.db_manager.get_nodes_by_properties({
                'node_type': 'sector',
                'classification_system': classification_system,
                'code': code
            })
            
            if not sectors:
                return {
                    'status': 'not_found',
                    'message': f'Sector not found: {classification_system} {code}',
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'status': 'success',
                'sector': sectors[0],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting sector by code: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting sector by code: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def establish_sector_hierarchy(self, parent_uid: str, child_uid: str, 
                                 relation_type: str = 'parent_sector', 
                                 attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Establish a hierarchical relationship between sectors.
        
        Args:
            parent_uid: Parent sector UID
            child_uid: Child sector UID
            relation_type: Type of relationship (default: 'parent_sector')
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing result
        """
        self.logging.info(f"[{datetime.now()}] Establishing sector hierarchy: {parent_uid} -> {child_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify sectors exist
            parent_sector = self.db_manager.get_node(parent_uid)
            child_sector = self.db_manager.get_node(child_uid)
            
            if not parent_sector or not child_sector:
                return {
                    'status': 'error',
                    'message': 'Parent or child sector not found',
                    'parent_uid': parent_uid,
                    'child_uid': child_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if both nodes are sectors
            if parent_sector.get('node_type') != 'sector' or child_sector.get('node_type') != 'sector':
                return {
                    'status': 'error',
                    'message': 'Both nodes must be of type sector',
                    'parent_type': parent_sector.get('node_type'),
                    'child_type': child_sector.get('node_type'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if the relationship already exists
            existing_edges = self.db_manager.get_edges_between(parent_uid, child_uid, [relation_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Relationship already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare edge data
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': parent_uid,
                'target_id': child_uid,
                'edge_type': relation_type,
                'attributes': attributes or {}
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'parent': parent_sector,
                'child': child_sector,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error establishing sector hierarchy: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error establishing sector hierarchy: {str(e)}",
                'parent_uid': parent_uid,
                'child_uid': child_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def map_between_classifications(self, source_classification: str, source_code: str,
                                  target_classification: str, target_code: str,
                                  equivalence_type: str = 'approximate_equivalent',
                                  attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map between different classification systems.
        
        Args:
            source_classification: Source classification system
            source_code: Source code
            target_classification: Target classification system
            target_code: Target code
            equivalence_type: Type of equivalence (exact, approximate)
            attributes: Optional mapping attributes
            
        Returns:
            Dict containing mapping result
        """
        self.logging.info(f"[{datetime.now()}] Mapping between classifications: {source_classification} {source_code} -> {target_classification} {target_code}")
        
        try:
            # Get source and target sectors
            source_result = self.get_sector_by_code(source_classification, source_code)
            target_result = self.get_sector_by_code(target_classification, target_code)
            
            if source_result.get('status') != 'success' or target_result.get('status') != 'success':
                return {
                    'status': 'error',
                    'message': 'Source or target sector not found',
                    'source_status': source_result.get('status'),
                    'target_status': target_result.get('status'),
                    'timestamp': datetime.now().isoformat()
                }
            
            source_uid = source_result['sector']['uid']
            target_uid = target_result['sector']['uid']
            
            # Check if the mapping already exists
            existing_edges = self.db_manager.get_edges_between(source_uid, target_uid, [equivalence_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Mapping already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare edge data
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': source_uid,
                'target_id': target_uid,
                'edge_type': equivalence_type,
                'attributes': attributes or {
                    'mapping_type': 'cross_classification',
                    'source_system': source_classification,
                    'target_system': target_classification,
                    'confidence': 1.0  # Set to appropriate value
                }
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'source': source_result['sector'],
                'target': target_result['sector'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error mapping between classifications: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error mapping between classifications: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_sector_hierarchy(self, sector_uid: str, direction: str = 'up',
                           max_levels: int = 3) -> Dict[str, Any]:
        """
        Get the sector hierarchy (parents or children) for a given sector.
        
        Args:
            sector_uid: Sector UID
            direction: Direction of hierarchy ('up' for parents, 'down' for children)
            max_levels: Maximum levels to traverse
            
        Returns:
            Dict containing sector hierarchy
        """
        self.logging.info(f"[{datetime.now()}] Getting sector hierarchy for {sector_uid}, direction: {direction}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify sector exists
            sector = self.db_manager.get_node(sector_uid)
            
            if not sector:
                return {
                    'status': 'error',
                    'message': 'Sector not found',
                    'sector_uid': sector_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            hierarchy = []
            visited = set()
            current_level = [{'node': sector, 'level': 0}]
            
            for level in range(max_levels):
                next_level = []
                
                for item in current_level:
                    node = item['node']
                    node_uid = node['uid']
                    
                    if node_uid in visited:
                        continue
                    
                    visited.add(node_uid)
                    
                    # Get edges for traversal
                    if direction == 'up':
                        # For 'up', look at incoming edges
                        edges = self.db_manager.get_incoming_edges(node_uid, ['parent_sector'])
                        for edge in edges:
                            parent_uid = edge['source_id']
                            parent_node = self.db_manager.get_node(parent_uid)
                            if parent_node:
                                next_level.append({'node': parent_node, 'level': level + 1})
                                hierarchy.append({
                                    'node': parent_node,
                                    'relation': 'parent',
                                    'level': level + 1,
                                    'edge': edge
                                })
                    else:
                        # For 'down', look at outgoing edges
                        edges = self.db_manager.get_outgoing_edges(node_uid, ['parent_sector'])
                        for edge in edges:
                            child_uid = edge['target_id']
                            child_node = self.db_manager.get_node(child_uid)
                            if child_node:
                                next_level.append({'node': child_node, 'level': level + 1})
                                hierarchy.append({
                                    'node': child_node,
                                    'relation': 'child',
                                    'level': level + 1,
                                    'edge': edge
                                })
                
                if not next_level:
                    break
                
                current_level = next_level
            
            return {
                'status': 'success',
                'sector': sector,
                'hierarchy': hierarchy,
                'hierarchy_count': len(hierarchy),
                'direction': direction,
                'max_levels': max_levels,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting sector hierarchy: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting sector hierarchy: {str(e)}",
                'sector_uid': sector_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def find_related_sectors(self, sector_uid: str, relation_types: Optional[List[str]] = None,
                          max_distance: int = 2) -> Dict[str, Any]:
        """
        Find sectors related to a given sector.
        
        Args:
            sector_uid: Sector UID
            relation_types: Optional list of relation types
            max_distance: Maximum graph distance to search
            
        Returns:
            Dict containing related sectors
        """
        self.logging.info(f"[{datetime.now()}] Finding related sectors for {sector_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify sector exists
            sector = self.db_manager.get_node(sector_uid)
            
            if not sector:
                return {
                    'status': 'error',
                    'message': 'Sector not found',
                    'sector_uid': sector_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Default relation types if not provided
            if not relation_types:
                relation_types = ['parent_sector', 'related_sector', 'approximate_equivalent', 'exact_equivalent']
            
            related_sectors = []
            visited = set([sector_uid])
            current_level = [{'node_uid': sector_uid, 'distance': 0}]
            
            for distance in range(1, max_distance + 1):
                next_level = []
                
                for item in current_level:
                    node_uid = item['node_uid']
                    
                    # Get outgoing relationships
                    outgoing = self.db_manager.get_outgoing_edges(node_uid, relation_types)
                    for edge in outgoing:
                        target_uid = edge['target_id']
                        if target_uid not in visited:
                            target_node = self.db_manager.get_node(target_uid)
                            if target_node and target_node.get('node_type') == 'sector':
                                visited.add(target_uid)
                                next_level.append({'node_uid': target_uid, 'distance': distance})
                                related_sectors.append({
                                    'sector': target_node,
                                    'relation': edge['edge_type'],
                                    'direction': 'outgoing',
                                    'distance': distance,
                                    'edge': edge
                                })
                    
                    # Get incoming relationships
                    incoming = self.db_manager.get_incoming_edges(node_uid, relation_types)
                    for edge in incoming:
                        source_uid = edge['source_id']
                        if source_uid not in visited:
                            source_node = self.db_manager.get_node(source_uid)
                            if source_node and source_node.get('node_type') == 'sector':
                                visited.add(source_uid)
                                next_level.append({'node_uid': source_uid, 'distance': distance})
                                related_sectors.append({
                                    'sector': source_node,
                                    'relation': edge['edge_type'],
                                    'direction': 'incoming',
                                    'distance': distance,
                                    'edge': edge
                                })
                
                if not next_level:
                    break
                
                current_level = next_level
            
            return {
                'status': 'success',
                'sector': sector,
                'related_sectors': related_sectors,
                'related_count': len(related_sectors),
                'max_distance': max_distance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding related sectors: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding related sectors: {str(e)}",
                'sector_uid': sector_uid,
                'timestamp': datetime.now().isoformat()
            }