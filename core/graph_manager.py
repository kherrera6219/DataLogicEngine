
"""
Universal Knowledge Graph (UKG) Graph Manager

This module manages the graph database operations for the UKG system,
providing a unified interface for accessing and modifying the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple

class GraphManager:
    """
    Graph Manager for the UKG System
    
    Responsible for:
    - Managing the knowledge graph structure
    - CRUD operations on nodes and edges
    - Graph traversal and query operations
    - Ontology management
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize the Graph Manager.
        
        Args:
            db_manager: Database Manager instance
        """
        self.db_manager = db_manager
        self.logging = logging.getLogger(__name__)
        
        # Define node types
        self.node_types = [
            "pillar_level", "sector", "branch", "domain", "method", "tool",
            "regulation", "compliance_standard", "knowledge_expert",
            "skill_expert", "role_expert", "context_expert", "location",
            "time_period", "knowledge_node", "classification_code"
        ]
        
        # Define edge types
        self.edge_types = [
            "parent_of", "child_of", "related_to", "influences", "implements",
            "regulates", "complies_with", "located_in", "occurred_during",
            "authored_by", "has_expertise_in", "applies_to_sector",
            "uses_method", "uses_tool", "has_branch", "mapped_to_classification",
            "equivalent_to", "part_of", "broader", "narrower"
        ]
    
    def add_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a node to the knowledge graph.
        
        Args:
            node_data: Node data dictionary
            
        Returns:
            Dict containing the added node
        """
        self.logging.info(f"[{datetime.now()}] Adding node: {node_data.get('label', 'Unlabeled')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in node_data:
                node_type = node_data.get('node_type', 'generic')
                node_data['uid'] = f"{node_type}_{uuid.uuid4()}"
            
            # Set creation timestamp
            if 'created_at' not in node_data:
                node_data['created_at'] = datetime.now().isoformat()
            
            # Add node to database
            new_node = self.db_manager.add_node(node_data)
            
            return {
                'status': 'success',
                'node': new_node,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error adding node: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error adding node: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def add_edge(self, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add an edge to the knowledge graph.
        
        Args:
            edge_data: Edge data dictionary
            
        Returns:
            Dict containing the added edge
        """
        self.logging.info(f"[{datetime.now()}] Adding edge: {edge_data.get('edge_type', 'Untyped')} from {edge_data.get('source_id', 'Unknown')} to {edge_data.get('target_id', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in edge_data:
                edge_data['uid'] = f"edge_{uuid.uuid4()}"
            
            # Set creation timestamp
            if 'created_at' not in edge_data:
                edge_data['created_at'] = datetime.now().isoformat()
            
            # Verify source and target nodes exist
            source_id = edge_data.get('source_id')
            target_id = edge_data.get('target_id')
            
            source_node = self.db_manager.get_node(source_id)
            target_node = self.db_manager.get_node(target_id)
            
            if not source_node:
                return {
                    'status': 'error',
                    'message': f'Source node not found: {source_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            if not target_node:
                return {
                    'status': 'error',
                    'message': f'Target node not found: {target_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error adding edge: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error adding edge: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Dict containing node data or None if not found
        """
        if not self.db_manager:
            return None
        
        return self.db_manager.get_node(node_id)
    
    def get_edges_between(self, source_id: str, target_id: str, 
                        edge_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get edges between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_types: Optional list of edge types to filter by
            
        Returns:
            List of edges
        """
        if not self.db_manager:
            return []
        
        return self.db_manager.get_edges_between(source_id, target_id, edge_types)
    
    def get_outgoing_edges(self, node_id: str, 
                         edge_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get outgoing edges from a node.
        
        Args:
            node_id: Node ID
            edge_types: Optional list of edge types to filter by
            
        Returns:
            List of edges
        """
        if not self.db_manager:
            return []
        
        return self.db_manager.get_outgoing_edges(node_id, edge_types)
    
    def get_incoming_edges(self, node_id: str, 
                         edge_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get incoming edges to a node.
        
        Args:
            node_id: Node ID
            edge_types: Optional list of edge types to filter by
            
        Returns:
            List of edges
        """
        if not self.db_manager:
            return []
        
        return self.db_manager.get_incoming_edges(node_id, edge_types)
    
    def find_paths(self, source_id: str, target_id: str, 
                 max_depth: int = 5, 
                 edge_types: Optional[List[str]] = None) -> List[List[Dict[str, Any]]]:
        """
        Find paths between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_depth: Maximum path depth
            edge_types: Optional list of edge types to traverse
            
        Returns:
            List of paths (each path is a list of edges)
        """
        if not self.db_manager:
            return []
        
        paths = []
        visited = set()
        current_path = []
        
        self._dfs_paths(source_id, target_id, visited, current_path, paths, max_depth, edge_types)
        
        return paths
    
    def _dfs_paths(self, current_id: str, target_id: str, 
                 visited: Set[str], current_path: List[Dict[str, Any]], 
                 paths: List[List[Dict[str, Any]]], depth_left: int,
                 edge_types: Optional[List[str]]) -> None:
        """
        Depth-first search to find paths between nodes.
        
        Args:
            current_id: Current node ID
            target_id: Target node ID
            visited: Set of visited node IDs
            current_path: Current path (list of edges)
            paths: List to store found paths
            depth_left: Remaining depth
            edge_types: Optional list of edge types to traverse
        """
        if current_id == target_id:
            paths.append(current_path.copy())
            return
        
        if depth_left <= 0:
            return
        
        visited.add(current_id)
        
        outgoing_edges = self.db_manager.get_outgoing_edges(current_id, edge_types)
        
        for edge in outgoing_edges:
            next_id = edge['target_id']
            
            if next_id not in visited:
                current_path.append(edge)
                self._dfs_paths(next_id, target_id, visited, current_path, paths, depth_left - 1, edge_types)
                current_path.pop()
        
        visited.remove(current_id)
    
    def find_nodes_by_properties(self, properties: Dict[str, Any], 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find nodes by properties.
        
        Args:
            properties: Dictionary of property keys and values
            limit: Maximum number of results
            
        Returns:
            List of matching nodes
        """
        if not self.db_manager:
            return []
        
        return self.db_manager.get_nodes_by_properties(properties, limit)
    
    def register_branch(self, branch_data: Dict[str, Any], 
                      parent_branch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a branch in the knowledge graph.
        
        Args:
            branch_data: Branch data dictionary
            parent_branch_id: Optional parent branch ID
            
        Returns:
            Dict containing registration result
        """
        self.logging.info(f"[{datetime.now()}] Registering branch: {branch_data.get('label', 'Unlabeled')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure branch has required fields
            required_fields = ['label', 'branch_type', 'sector_id']
            for field in required_fields:
                if field not in branch_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Verify branch type
            valid_branch_types = ['large', 'medium', 'small', 'granular']
            if branch_data['branch_type'] not in valid_branch_types:
                return {
                    'status': 'error',
                    'message': f'Invalid branch type: {branch_data["branch_type"]}. Must be one of {valid_branch_types}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify sector exists
            sector_id = branch_data['sector_id']
            sector_nodes = self.db_manager.get_nodes_by_properties({'id': sector_id, 'node_type': 'sector'})
            
            if not sector_nodes:
                return {
                    'status': 'error',
                    'message': f'Sector not found: {sector_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            sector_node = sector_nodes[0]
            
            # Generate UID if not provided
            if 'uid' not in branch_data:
                branch_type = branch_data['branch_type']
                label_part = branch_data['label'].lower().replace(' ', '_')[:10]
                branch_data['uid'] = f"branch_{branch_type}_{label_part}_{uuid.uuid4().hex[:8]}"
            
            # Set node type
            branch_data['node_type'] = 'branch'
            
            # Set axis number for Branch (Axis 3)
            branch_data['axis_number'] = 3
            
            # Set creation timestamp
            if 'created_at' not in branch_data:
                branch_data['created_at'] = datetime.now().isoformat()
            
            # Check if branch with same properties already exists
            existing_branches = self.db_manager.get_nodes_by_properties({
                'node_type': 'branch',
                'branch_type': branch_data['branch_type'],
                'label': branch_data['label'],
                'sector_id': branch_data['sector_id']
            })
            
            if existing_branches:
                return {
                    'status': 'exists',
                    'message': 'Branch already exists',
                    'branch': existing_branches[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add branch node
            new_branch = self.db_manager.add_node(branch_data)
            
            # Connect branch to sector
            sector_branch_edge = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': sector_node['uid'],
                'target_id': new_branch['uid'],
                'edge_type': 'has_branch',
                'attributes': {
                    'branch_type': branch_data['branch_type']
                }
            }
            
            self.db_manager.add_edge(sector_branch_edge)
            
            # Connect to parent branch if provided
            if parent_branch_id:
                parent_nodes = self.db_manager.get_nodes_by_properties({
                    'id': parent_branch_id,
                    'node_type': 'branch'
                })
                
                if not parent_nodes:
                    return {
                        'status': 'error',
                        'message': f'Parent branch not found: {parent_branch_id}',
                        'branch': new_branch,  # Still return the created branch
                        'timestamp': datetime.now().isoformat()
                    }
                
                parent_node = parent_nodes[0]
                
                # Check parent-child branch type relationship
                parent_type = parent_node['branch_type']
                child_type = branch_data['branch_type']
                
                valid_parent_child = {
                    'large': 'medium',
                    'medium': 'small',
                    'small': 'granular'
                }
                
                if parent_type in valid_parent_child and valid_parent_child[parent_type] == child_type:
                    # Valid parent-child relationship
                    parent_child_edge = {
                        'uid': f"edge_{uuid.uuid4()}",
                        'source_id': parent_node['uid'],
                        'target_id': new_branch['uid'],
                        'edge_type': 'has_branch',
                        'attributes': {
                            'parent_type': parent_type,
                            'child_type': child_type
                        }
                    }
                    
                    self.db_manager.add_edge(parent_child_edge)
                else:
                    return {
                        'status': 'error',
                        'message': f'Invalid parent-child branch type relationship. Parent {parent_type} cannot have child {child_type}',
                        'branch': new_branch,  # Still return the created branch
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {
                'status': 'success',
                'branch': new_branch,
                'sector': sector_node,
                'parent_branch_id': parent_branch_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error registering branch: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error registering branch: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_branch_hierarchy(self, sector_id: str) -> Dict[str, Any]:
        """
        Get the branch hierarchy for a sector.
        
        Args:
            sector_id: Sector ID
            
        Returns:
            Dict containing the branch hierarchy
        """
        self.logging.info(f"[{datetime.now()}] Getting branch hierarchy for sector: {sector_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get sector
            sector_nodes = self.db_manager.get_nodes_by_properties({'id': sector_id, 'node_type': 'sector'})
            
            if not sector_nodes:
                return {
                    'status': 'error',
                    'message': f'Sector not found: {sector_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            sector_node = sector_nodes[0]
            
            # Get large branches for sector
            large_branches = {}
            large_branch_nodes = self.db_manager.get_nodes_by_properties({
                'node_type': 'branch',
                'branch_type': 'large',
                'sector_id': sector_id
            })
            
            for large_branch in large_branch_nodes:
                large_branch_id = large_branch.get('id')
                
                if large_branch_id:
                    large_branches[large_branch_id] = {
                        'branch': large_branch,
                        'medium_branches': {}
                    }
                    
                    # Get medium branches for large branch
                    medium_branches = self._get_child_branches(large_branch['uid'], 'medium')
                    
                    for medium_branch_id, medium_branch_data in medium_branches.items():
                        large_branches[large_branch_id]['medium_branches'][medium_branch_id] = medium_branch_data
                        
                        # Get small branches for medium branch
                        small_branches = self._get_child_branches(medium_branch_data['branch']['uid'], 'small')
                        medium_branch_data['small_branches'] = small_branches
                        
                        # Get granular branches for each small branch
                        for small_branch_id, small_branch_data in small_branches.items():
                            granular_branches = self._get_child_branches(small_branch_data['branch']['uid'], 'granular')
                            small_branch_data['granular_branches'] = granular_branches
            
            return {
                'status': 'success',
                'sector': sector_node,
                'branch_hierarchy': large_branches,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting branch hierarchy: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting branch hierarchy: {str(e)}",
                'sector_id': sector_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_child_branches(self, parent_uid: str, branch_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get child branches of a specific type for a parent node.
        
        Args:
            parent_uid: Parent node UID
            branch_type: Branch type to retrieve
            
        Returns:
            Dict mapping branch IDs to branch data
        """
        child_branches = {}
        
        # Get outgoing edges of type 'has_branch'
        outgoing_edges = self.db_manager.get_outgoing_edges(parent_uid, ['has_branch'])
        
        for edge in outgoing_edges:
            target_uid = edge['target_id']
            target_node = self.db_manager.get_node(target_uid)
            
            if target_node and target_node.get('node_type') == 'branch' and target_node.get('branch_type') == branch_type:
                branch_id = target_node.get('id')
                
                if branch_id:
                    child_branches[branch_id] = {
                        'branch': target_node,
                        'edge': edge
                    }
        
        return child_branches
    
    def find_classification_codes(self, sector_id: str, 
                               classification_system: str) -> Dict[str, Any]:
        """
        Find classification codes for a sector in a specific classification system.
        
        Args:
            sector_id: Sector ID
            classification_system: Classification system (naics, sic, psc, nic)
            
        Returns:
            Dict containing the classification codes
        """
        self.logging.info(f"[{datetime.now()}] Finding {classification_system} codes for sector: {sector_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get sector
            sector_nodes = self.db_manager.get_nodes_by_properties({'id': sector_id, 'node_type': 'sector'})
            
            if not sector_nodes:
                return {
                    'status': 'error',
                    'message': f'Sector not found: {sector_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            sector_node = sector_nodes[0]
            
            # Find classification codes
            classification_codes = []
            
            # Method 1: Direct classification code properties
            if 'classification_systems' in sector_node and classification_system.lower() in sector_node['classification_systems']:
                code = sector_node['classification_systems'][classification_system.lower()]
                classification_codes.append({
                    'code': code,
                    'system': classification_system.upper(),
                    'source': 'direct_property',
                    'confidence': 1.0
                })
            
            # Method 2: Find branch mappings
            branch_nodes = self.db_manager.get_nodes_by_properties({
                'node_type': 'branch',
                'sector_id': sector_id
            })
            
            for branch in branch_nodes:
                # Find classification mappings for branch
                outgoing_edges = self.db_manager.get_outgoing_edges(branch['uid'], ['mapped_to_classification'])
                
                for edge in outgoing_edges:
                    target_uid = edge['target_id']
                    code_node = self.db_manager.get_node(target_uid)
                    
                    if code_node and code_node.get('node_type') == 'classification_code' and code_node.get('system', '').upper() == classification_system.upper():
                        classification_codes.append({
                            'code': code_node.get('code'),
                            'system': code_node.get('system'),
                            'source': 'branch_mapping',
                            'branch': branch,
                            'confidence': edge.get('attributes', {}).get('confidence', 0.9)
                        })
            
            return {
                'status': 'success',
                'sector': sector_node,
                'classification_system': classification_system.upper(),
                'codes': classification_codes,
                'code_count': len(classification_codes),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding classification codes: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding classification codes: {str(e)}",
                'sector_id': sector_id,
                'classification_system': classification_system,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Dict containing graph statistics
        """
        self.logging.info(f"[{datetime.now()}] Getting graph statistics")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get overall counts
            total_nodes = len(self.db_manager.get_all_nodes())
            total_edges = len(self.db_manager.get_all_edges())
            
            # Get counts by node type
            node_type_counts = {}
            for node_type in self.node_types:
                nodes = self.db_manager.get_nodes_by_properties({'node_type': node_type})
                if nodes:
                    node_type_counts[node_type] = len(nodes)
            
            # Get counts by edge type
            edge_type_counts = {}
            for edge_type in self.edge_types:
                edges = self.db_manager.get_edges_by_type(edge_type)
                if edges:
                    edge_type_counts[edge_type] = len(edges)
            
            # Get axis counts
            axis_counts = {}
            for axis_num in range(1, 14):
                nodes = self.db_manager.get_nodes_by_properties({'axis_number': axis_num})
                if nodes:
                    axis_counts[f"axis_{axis_num}"] = len(nodes)
            
            # Get branch type counts
            branch_type_counts = {}
            for branch_type in ['large', 'medium', 'small', 'granular']:
                branches = self.db_manager.get_nodes_by_properties({
                    'node_type': 'branch',
                    'branch_type': branch_type
                })
                if branches:
                    branch_type_counts[branch_type] = len(branches)
            
            return {
                'status': 'success',
                'total_nodes': total_nodes,
                'total_edges': total_edges,
                'node_type_counts': node_type_counts,
                'edge_type_counts': edge_type_counts,
                'axis_counts': axis_counts,
                'branch_type_counts': branch_type_counts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting graph statistics: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting graph statistics: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
