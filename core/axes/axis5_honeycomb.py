
"""
UKG Axis 5 Honeycomb System

This module implements the Honeycomb System for Axis 5 of the Universal Knowledge Graph (UKG).
The Honeycomb System enables multi-directional crosswalking between industry sectors,
pillar levels, and other axes within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

class HoneycombSystem:
    """
    Honeycomb System for the UKG
    
    Responsible for creating and managing multi-dimensional connections between:
    - Pillar Levels (Axis 1) and their sublevels
    - Industry Sectors (Axis 2)
    - Branches (Axis 3)
    - Methods (Axis 4)
    - Tools (Axis 5)
    
    The Honeycomb metaphor represents how connections extend outward in multiple 
    directions from any node, creating a rich network of interconnected knowledge.
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Honeycomb System.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Connection types for the honeycomb system
        self.connection_types = {
            "direct_application": "Direct application of knowledge/tool in sector",
            "enables": "Enables or facilitates another node",
            "implements": "Implements principles from another node",
            "specializes": "Specializes a more general concept",
            "extends": "Extends the capabilities of another node",
            "alternative_to": "Provides an alternative approach",
            "derived_from": "Derived or evolved from another node",
            "regulated_by": "Regulated or governed by another node",
            "certified_by": "Certified or validated by standards",
            "compatible_with": "Compatible or interoperable with",
            "prerequisite_for": "Prerequisite knowledge/skill",
            "crosswalks_to": "Explicitly maps to equivalent concept"
        }
    
    def create_honeycomb_connection(self, source_uid: str, target_uid: str, 
                                  connection_type: str,
                                  strength: float = 1.0,
                                  attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a honeycomb connection between two nodes.
        
        Args:
            source_uid: Source node UID
            target_uid: Target node UID
            connection_type: Type of connection (from self.connection_types)
            strength: Connection strength (0.0 to 1.0)
            attributes: Additional connection attributes
            
        Returns:
            Dict containing connection result
        """
        self.logging.info(f"[{datetime.now()}] Creating honeycomb connection: {connection_type} from {source_uid} to {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate connection type
            if connection_type not in self.connection_types:
                return {
                    'status': 'error',
                    'message': f'Invalid connection type: {connection_type}',
                    'valid_types': list(self.connection_types.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify nodes exist
            source_node = self.db_manager.get_node(source_uid)
            target_node = self.db_manager.get_node(target_uid)
            
            if not source_node or not target_node:
                return {
                    'status': 'error',
                    'message': 'Source or target node not found',
                    'source_exists': bool(source_node),
                    'target_exists': bool(target_node),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare edge attributes
            edge_attributes = attributes or {}
            edge_attributes.update({
                'connection_type': connection_type,
                'connection_description': self.connection_types[connection_type],
                'strength': max(0.0, min(1.0, strength)),  # Clamp between 0 and 1
                'created_at': datetime.now().isoformat(),
                'honeycomb': True  # Mark as a honeycomb connection
            })
            
            # Check if connection already exists
            existing_edges = self.db_manager.get_edges_between(
                source_uid, 
                target_uid, 
                [connection_type]
            )
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Connection already exists',
                    'edge': existing_edges[0],
                    'source': source_node,
                    'target': target_node,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create connection edge
            edge_data = {
                'uid': f"hc_edge_{uuid.uuid4()}",
                'source_id': source_uid,
                'target_id': target_uid,
                'edge_type': connection_type,
                'attributes': edge_attributes
            }
            
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'source': source_node,
                'target': target_node,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating honeycomb connection: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating honeycomb connection: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_sector_pillar_crosswalk(self, sector_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive crosswalk connections between a sector and all pillar levels.
        
        Args:
            sector_id: Sector ID to generate crosswalks for
            
        Returns:
            Dict containing crosswalk generation results
        """
        self.logging.info(f"[{datetime.now()}] Generating sector-pillar crosswalk for sector: {sector_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get sector node
            sector_node = self.db_manager.get_node_by_id(sector_id)
            if not sector_node:
                return {
                    'status': 'error',
                    'message': f'Sector not found: {sector_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get all pillar levels
            pillar_levels = self.db_manager.get_nodes_by_properties({
                'node_type': 'pillar_level'
            })
            
            connections_created = []
            
            # For each pillar level, analyze and create appropriate connections
            for pillar in pillar_levels:
                # Determine connection type and strength based on pillar and sector attributes
                connection_type, strength = self._determine_pillar_sector_connection(pillar, sector_node)
                
                if connection_type:
                    # Create honeycomb connection
                    result = self.create_honeycomb_connection(
                        sector_node['uid'],
                        pillar['uid'],
                        connection_type,
                        strength
                    )
                    
                    if result['status'] == 'success' or result['status'] == 'exists':
                        connections_created.append({
                            'pillar': pillar,
                            'connection_type': connection_type,
                            'strength': strength,
                            'edge': result.get('edge')
                        })
                        
                        # For strong connections, also connect to pillar sublevels
                        if strength > 0.7 and 'sublevels' in pillar:
                            sublevel_connections = self._connect_to_sublevels(
                                sector_node['uid'], 
                                pillar
                            )
                            connections_created.extend(sublevel_connections)
            
            return {
                'status': 'success',
                'sector': sector_node,
                'connections_created': connections_created,
                'connection_count': len(connections_created),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error generating sector-pillar crosswalk: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error generating sector-pillar crosswalk: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _determine_pillar_sector_connection(self, pillar: Dict[str, Any], 
                                          sector: Dict[str, Any]) -> tuple:
        """
        Determine the appropriate connection type and strength between a pillar and sector.
        
        Args:
            pillar: Pillar level node
            sector: Sector node
            
        Returns:
            Tuple of (connection_type, strength)
        """
        # This is a simplified version - in production, this would use more sophisticated
        # analysis of the pillar and sector attributes, possibly with ML/NLP
        
        pillar_id = pillar.get('pillar_id', '')
        sector_code = sector.get('code', '')
        
        # Default connection type and strength
        connection_type = "crosswalks_to"
        strength = 0.5
        
        # Check for specific pillar-sector affinities
        # These mappings should come from a configuration or be dynamically learned
        pillar_sector_affinities = {
            # Technology sector has strong connections to data, engineering pillars
            ("51", "PL03"): ("direct_application", 0.9),  # Technology -> Formal Sciences
            ("51", "PL06"): ("implements", 0.8),          # Technology -> Engineering
            ("51", "PL07"): ("implements", 0.9),          # Technology -> Data Privacy
            
            # Financial sector connections
            ("52", "PL08"): ("implements", 0.7),          # Finance -> Social Sciences
            ("52", "PL30"): ("direct_application", 0.9),  # Finance -> Business
            
            # Healthcare connections
            ("62", "PL02"): ("implements", 0.8),          # Healthcare -> Natural Sciences
            ("62", "PL05"): ("direct_application", 0.95), # Healthcare -> Healthcare Sciences
            
            # Government connections
            ("92", "PL20"): ("implements", 0.9),          # Government -> Legal Frameworks
            ("92", "PL48"): ("direct_application", 0.95), # Government -> Public Policy
            
            # Manufacturing connections
            ("31-33", "PL06"): ("implements", 0.85),      # Manufacturing -> Engineering
            
            # Energy sector connections
            ("21", "PL50"): ("direct_application", 0.9),  # Energy -> Energy Systems
        }
        
        # Look up affinity if it exists
        key = (sector_code, pillar_id)
        if key in pillar_sector_affinities:
            connection_type, strength = pillar_sector_affinities[key]
        else:
            # Calculate generic connection based on node properties
            # This is a placeholder for more sophisticated matching
            # In a real system, this would use semantic analysis, ML, etc.
            pillar_name = pillar.get('name', '').lower()
            sector_name = sector.get('name', '').lower()
            sector_desc = sector.get('description', '').lower()
            
            # Simple keyword matching - just an example
            if any(word in sector_name or word in sector_desc for word in pillar_name.split()):
                connection_type = "direct_application"
                strength = 0.8
            elif "universal" in pillar_name or "foundation" in pillar_name:
                connection_type = "implements"
                strength = 0.7
        
        return connection_type, strength
    
    def _connect_to_sublevels(self, sector_uid: str, pillar: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create connections between a sector and pillar sublevels.
        
        Args:
            sector_uid: Sector node UID
            pillar: Pillar level node with sublevels
            
        Returns:
            List of created connections
        """
        connections = []
        
        # Handle different sublevel structures
        sublevels = pillar.get('sublevels', {})
        if not sublevels:
            return connections
        
        # Process level 1 sublevels
        level1_sublevels = sublevels.get('level_1', [])
        for sublevel in level1_sublevels:
            sublevel_id = sublevel.get('id')
            if not sublevel_id:
                continue
                
            # Get sublevel node
            sublevel_node = self.db_manager.get_node_by_id(sublevel_id)
            if not sublevel_node:
                continue
            
            # Create connection to sublevel
            connection_type = "specializes"  # Sublevel specializes the parent pillar
            strength = 0.7
            
            result = self.create_honeycomb_connection(
                sector_uid,
                sublevel_node['uid'],
                connection_type,
                strength
            )
            
            if result['status'] == 'success' or result['status'] == 'exists':
                connections.append({
                    'sublevel': sublevel_node,
                    'connection_type': connection_type,
                    'strength': strength,
                    'edge': result.get('edge'),
                    'level': 1
                })
        
        # Process level 2 sublevels (if any)
        level2_sublevels = sublevels.get('level_2', [])
        for sublevel in level2_sublevels:
            sublevel_id = sublevel.get('id')
            parent_id = sublevel.get('parent')
            
            if not sublevel_id:
                continue
                
            # Get sublevel node
            sublevel_node = self.db_manager.get_node_by_id(sublevel_id)
            if not sublevel_node:
                continue
            
            # Create connection to sublevel with lower strength
            connection_type = "specializes"
            strength = 0.5  # Lower strength for deeper sublevel
            
            result = self.create_honeycomb_connection(
                sector_uid,
                sublevel_node['uid'],
                connection_type,
                strength
            )
            
            if result['status'] == 'success' or result['status'] == 'exists':
                connections.append({
                    'sublevel': sublevel_node,
                    'connection_type': connection_type,
                    'strength': strength,
                    'edge': result.get('edge'),
                    'level': 2,
                    'parent': parent_id
                })
        
        return connections
    
    def find_crosswalk_paths(self, source_uid: str, target_uid: str, 
                           max_depth: int = 3) -> Dict[str, Any]:
        """
        Find all possible crosswalk paths between two nodes through the honeycomb system.
        
        Args:
            source_uid: Source node UID
            target_uid: Target node UID
            max_depth: Maximum path length to search
            
        Returns:
            Dict containing path results
        """
        self.logging.info(f"[{datetime.now()}] Finding crosswalk paths between {source_uid} and {target_uid}")
        
        try:
            if not self.graph_manager:
                return {
                    'status': 'error',
                    'message': 'Graph manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify nodes exist
            source_node = self.db_manager.get_node(source_uid)
            target_node = self.db_manager.get_node(target_uid)
            
            if not source_node or not target_node:
                return {
                    'status': 'error',
                    'message': 'Source or target node not found',
                    'source_exists': bool(source_node),
                    'target_exists': bool(target_node),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find paths using breadth-first search
            paths = self._find_all_paths(source_uid, target_uid, max_depth)
            
            # Enrich paths with node and edge details
            enriched_paths = []
            for path in paths:
                enriched_path = []
                
                for i in range(len(path) - 1):
                    start_uid = path[i]
                    end_uid = path[i + 1]
                    
                    # Get node details
                    node = self.db_manager.get_node(start_uid)
                    
                    # Get edge details
                    edges = self.db_manager.get_edges_between(start_uid, end_uid)
                    edge = edges[0] if edges else None
                    
                    enriched_path.append({
                        'node': node,
                        'edge': edge
                    })
                
                # Add final node
                final_node = self.db_manager.get_node(path[-1])
                enriched_path.append({
                    'node': final_node,
                    'edge': None
                })
                
                # Calculate path strength (product of edge strengths)
                path_strength = 1.0
                for item in enriched_path:
                    if item['edge'] and 'attributes' in item['edge']:
                        edge_strength = item['edge']['attributes'].get('strength', 1.0)
                        path_strength *= edge_strength
                
                enriched_paths.append({
                    'path': enriched_path,
                    'length': len(path) - 1,
                    'strength': path_strength
                })
            
            # Sort paths by strength (strongest first)
            enriched_paths.sort(key=lambda p: p['strength'], reverse=True)
            
            return {
                'status': 'success',
                'source': source_node,
                'target': target_node,
                'paths': enriched_paths,
                'path_count': len(enriched_paths),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding crosswalk paths: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding crosswalk paths: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _find_all_paths(self, start_uid: str, end_uid: str, 
                       max_depth: int) -> List[List[str]]:
        """
        Find all paths between two nodes using breadth-first search.
        
        Args:
            start_uid: Starting node UID
            end_uid: Ending node UID
            max_depth: Maximum path length
            
        Returns:
            List of paths (each path is a list of node UIDs)
        """
        if start_uid == end_uid:
            return [[start_uid]]
        
        # Track visited nodes to avoid cycles
        visited = set()
        queue = [(start_uid, [start_uid])]
        all_paths = []
        
        while queue:
            (node, path) = queue.pop(0)
            
            # Skip if we've exceeded max depth
            if len(path) > max_depth + 1:
                continue
            
            # Get all connected nodes we haven't visited yet
            outgoing_edges = self.graph_manager.get_outgoing_edges(node)
            for edge in outgoing_edges:
                next_node = edge['target_id']
                
                # Found a path to the target
                if next_node == end_uid:
                    all_paths.append(path + [next_node])
                    continue
                
                # Avoid cycles in the path
                if next_node in path:
                    continue
                
                # Track this path for further exploration
                if len(path) < max_depth:
                    queue.append((next_node, path + [next_node]))
        
        return all_paths
    
    def generate_multi_axis_honeycomb(self, center_node_uid: str, 
                                    max_connections: int = 50) -> Dict[str, Any]:
        """
        Generate a multi-dimensional honeycomb network centered on a specific node,
        connecting across all axes.
        
        Args:
            center_node_uid: UID of the central node
            max_connections: Maximum number of connections to create
            
        Returns:
            Dict containing honeycomb generation results
        """
        self.logging.info(f"[{datetime.now()}] Generating multi-axis honeycomb for node: {center_node_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get center node
            center_node = self.db_manager.get_node(center_node_uid)
            if not center_node:
                return {
                    'status': 'error',
                    'message': f'Center node not found: {center_node_uid}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Track connections created
            connections_created = []
            
            # Determine node type and axis to customize connection strategy
            node_type = center_node.get('node_type', '')
            axis_number = center_node.get('axis_number')
            
            # Connect to nodes in each axis based on relevance
            axis_connections = {
                # axis_number: (num_connections, connection_strategies)
                1: (10, ["implements", "derived_from", "crosswalks_to"]),
                2: (8, ["direct_application", "crosswalks_to"]),
                3: (8, ["specializes", "alternative_to"]),
                4: (6, ["enables", "implements"]),
                5: (5, ["compatible_with", "extends"]),
                6: (4, ["regulated_by"]),
                7: (4, ["certified_by"]),
                8: (3, ["enables"]),
                9: (3, ["enables"]),
                10: (3, ["enables"]),
                11: (3, ["enables"]),
                12: (2, ["crosswalks_to"]),
                13: (2, ["crosswalks_to"])
            }
            
            # Modify connection strategy if center is a pillar level
            if node_type == 'pillar_level':
                # Connect more heavily to sectors and methods
                axis_connections[2] = (15, ["direct_application", "implements"])
                axis_connections[3] = (12, ["specializes"])
                axis_connections[4] = (10, ["enables", "implements"])
            
            # Modify connection strategy if center is a sector
            elif node_type == 'sector':
                # Connect more heavily to pillars and branches
                axis_connections[1] = (15, ["implements", "direct_application"])
                axis_connections[3] = (15, ["has_branch", "specializes"])
                axis_connections[4] = (8, ["enables", "implements"])
            
            # Process each axis
            for axis_num, (num_connections, strategies) in axis_connections.items():
                # Skip the center node's own axis
                if axis_number and axis_num == axis_number:
                    continue
                
                # Get candidate nodes from this axis
                candidates = self.db_manager.get_nodes_by_properties({
                    'axis_number': axis_num
                }, limit=50)  # Get a reasonable pool of candidates
                
                # Skip if no candidates
                if not candidates:
                    continue
                
                # Select most relevant candidates for connections
                selected_candidates = candidates[:min(len(candidates), num_connections)]
                
                # Create connections to selected candidates
                for candidate in selected_candidates:
                    # Skip if candidate is the center node
                    if candidate['uid'] == center_node_uid:
                        continue
                    
                    # Select connection type from available strategies
                    connection_type = strategies[0]  # Default to first strategy
                    if len(strategies) > 1:
                        # In a real system, this would use more sophisticated
                        # selection logic based on the specific nodes
                        connection_type = strategies[len(connections_created) % len(strategies)]
                    
                    # Assign a reasonable strength
                    strength = 0.7  # Default strength
                    
                    # Create connection
                    result = self.create_honeycomb_connection(
                        center_node_uid,
                        candidate['uid'],
                        connection_type,
                        strength
                    )
                    
                    if result['status'] == 'success' or result['status'] == 'exists':
                        connections_created.append({
                            'target': candidate,
                            'axis': axis_num,
                            'connection_type': connection_type,
                            'strength': strength,
                            'edge': result.get('edge')
                        })
                    
                    # Stop if we've reached the maximum connections
                    if len(connections_created) >= max_connections:
                        break
            
            return {
                'status': 'success',
                'center_node': center_node,
                'connections_created': connections_created,
                'connection_count': len(connections_created),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error generating multi-axis honeycomb: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error generating multi-axis honeycomb: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
