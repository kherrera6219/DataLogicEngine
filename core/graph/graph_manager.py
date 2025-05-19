import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import sys
import os
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class GraphManager:
    """
    Graph Manager
    
    This component manages all operations related to the knowledge graph,
    including node and edge creation, deletion, and querying. It provides
    a unified interface for graph operations across the UKG system.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Graph Manager.
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        logging.info(f"[{datetime.now()}] Initializing GraphManager...")
        self.config = config or {}
        
        # Configure graph manager settings
        self.graph_config = self.config.get('graph_manager', {})
        
        # Internal caching for performance
        self.node_cache = {}  # uid -> node
        self.edge_cache = {}  # uid -> edge
        self.node_type_index = {}  # node_type -> [uid]
        self.edge_type_index = {}  # edge_type -> [uid]
        
        # Track statistics
        self.stats = {
            'nodes_created': 0,
            'nodes_updated': 0,
            'nodes_deleted': 0,
            'edges_created': 0,
            'edges_updated': 0,
            'edges_deleted': 0,
            'queries_executed': 0
        }
        
        # Database manager reference (will be set by system initializer)
        self.db_manager = None
        
        logging.info(f"[{datetime.now()}] GraphManager initialized")
    
    def set_db_manager(self, db_manager):
        """
        Set the database manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logging.info(f"[{datetime.now()}] GM: Database manager set")
    
    def get_node_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get a node by its UID.
        
        Args:
            uid: Node UID
            
        Returns:
            dict: Node data or None if not found
        """
        # Check cache first
        if uid in self.node_cache:
            return self.node_cache[uid]
        
        # Query database
        if self.db_manager:
            node = self.db_manager.get_node_by_uid(uid)
            
            # Add to cache if found
            if node:
                self.node_cache[uid] = node
                
                # Update type index
                node_type = node.get('node_type')
                if node_type:
                    if node_type not in self.node_type_index:
                        self.node_type_index[node_type] = []
                    if uid not in self.node_type_index[node_type]:
                        self.node_type_index[node_type].append(uid)
                
            return node
        
        return None
    
    def get_edge_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get an edge by its UID.
        
        Args:
            uid: Edge UID
            
        Returns:
            dict: Edge data or None if not found
        """
        # Check cache first
        if uid in self.edge_cache:
            return self.edge_cache[uid]
        
        # Query database
        if self.db_manager:
            edge = self.db_manager.get_edge_by_uid(uid)
            
            # Add to cache if found
            if edge:
                self.edge_cache[uid] = edge
                
                # Update type index
                edge_type = edge.get('edge_type')
                if edge_type:
                    if edge_type not in self.edge_type_index:
                        self.edge_type_index[edge_type] = []
                    if uid not in self.edge_type_index[edge_type]:
                        self.edge_type_index[edge_type].append(uid)
                
            return edge
        
        return None
    
    def create_node(self, node_type: str, label: str, description: Optional[str] = None,
                  attributes: Optional[Dict] = None, uid: Optional[str] = None,
                  original_id: Optional[str] = None, axis_number: Optional[int] = None,
                  level: Optional[int] = None) -> Optional[Dict]:
        """
        Create a new node.
        
        Args:
            node_type: Type of node
            label: Human-readable label
            description: Optional description
            attributes: Optional attributes
            uid: Optional UID (auto-generated if None)
            original_id: Optional original ID from an external system
            axis_number: Optional axis number (1-13)
            level: Optional level within an axis
            
        Returns:
            dict: Created node data or None if creation failed
        """
        # Generate UID if not provided
        if not uid:
            uid = f"ND_{node_type.upper()}_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
        
        # Create node data
        node_data = {
            'uid': uid,
            'node_type': node_type,
            'label': label,
            'description': description,
            'attributes': attributes or {},
            'original_id': original_id,
            'axis_number': axis_number,
            'level': level,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Create in database
        if self.db_manager:
            created_node = self.db_manager.create_node(node_data)
            
            if created_node:
                # Add to cache
                self.node_cache[uid] = created_node
                
                # Update type index
                if node_type not in self.node_type_index:
                    self.node_type_index[node_type] = []
                if uid not in self.node_type_index[node_type]:
                    self.node_type_index[node_type].append(uid)
                
                # Update stats
                self.stats['nodes_created'] += 1
                
                return created_node
            
            return None
        
        # If no database manager, just return the node data
        # (this is for development/testing only)
        return node_data
    
    def update_node(self, uid: str, updates: Dict) -> Optional[Dict]:
        """
        Update a node.
        
        Args:
            uid: Node UID
            updates: Dictionary of updates
            
        Returns:
            dict: Updated node data or None if update failed
        """
        # Update in database
        if self.db_manager:
            updated_node = self.db_manager.update_node(uid, updates)
            
            if updated_node:
                # Update cache
                self.node_cache[uid] = updated_node
                
                # Update stats
                self.stats['nodes_updated'] += 1
                
                return updated_node
            
            return None
        
        # If no database manager, try to update the cached node
        if uid in self.node_cache:
            node = self.node_cache[uid].copy()
            node.update(updates)
            node['updated_at'] = datetime.now().isoformat()
            self.node_cache[uid] = node
            self.stats['nodes_updated'] += 1
            return node
        
        return None
    
    def delete_node(self, uid: str) -> bool:
        """
        Delete a node.
        
        Args:
            uid: Node UID
            
        Returns:
            bool: True if deletion was successful
        """
        # Delete from database
        if self.db_manager:
            success = self.db_manager.delete_node(uid)
            
            if success:
                # Remove from cache
                if uid in self.node_cache:
                    node = self.node_cache.pop(uid)
                    
                    # Update type index
                    node_type = node.get('node_type')
                    if node_type and node_type in self.node_type_index and uid in self.node_type_index[node_type]:
                        self.node_type_index[node_type].remove(uid)
                
                # Update stats
                self.stats['nodes_deleted'] += 1
                
                return True
            
            return False
        
        # If no database manager, try to remove from cache
        if uid in self.node_cache:
            node = self.node_cache.pop(uid)
            
            # Update type index
            node_type = node.get('node_type')
            if node_type and node_type in self.node_type_index and uid in self.node_type_index[node_type]:
                self.node_type_index[node_type].remove(uid)
            
            self.stats['nodes_deleted'] += 1
            return True
        
        return False
    
    def create_edge(self, edge_type: str, source_uid: str, target_uid: str,
                  label: Optional[str] = None, weight: float = 1.0,
                  attributes: Optional[Dict] = None, uid: Optional[str] = None) -> Optional[Dict]:
        """
        Create a new edge.
        
        Args:
            edge_type: Type of edge
            source_uid: Source node UID
            target_uid: Target node UID
            label: Optional human-readable label
            weight: Edge weight
            attributes: Optional attributes
            uid: Optional UID (auto-generated if None)
            
        Returns:
            dict: Created edge data or None if creation failed
        """
        # Generate UID if not provided
        if not uid:
            uid = f"ED_{edge_type.upper()}_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
        
        # Validate source and target nodes
        source_node = self.get_node_by_uid(source_uid)
        if not source_node:
            logging.error(f"[{datetime.now()}] GM: Cannot create edge: Source node {source_uid} not found")
            return None
        
        target_node = self.get_node_by_uid(target_uid)
        if not target_node:
            logging.error(f"[{datetime.now()}] GM: Cannot create edge: Target node {target_uid} not found")
            return None
        
        # Create edge data
        edge_data = {
            'uid': uid,
            'edge_type': edge_type,
            'source_uid': source_uid,
            'target_uid': target_uid,
            'label': label,
            'weight': weight,
            'attributes': attributes or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Create in database
        if self.db_manager:
            created_edge = self.db_manager.create_edge(edge_data)
            
            if created_edge:
                # Add to cache
                self.edge_cache[uid] = created_edge
                
                # Update type index
                if edge_type not in self.edge_type_index:
                    self.edge_type_index[edge_type] = []
                if uid not in self.edge_type_index[edge_type]:
                    self.edge_type_index[edge_type].append(uid)
                
                # Update stats
                self.stats['edges_created'] += 1
                
                return created_edge
            
            return None
        
        # If no database manager, just return the edge data
        # (this is for development/testing only)
        return edge_data
    
    def update_edge(self, uid: str, updates: Dict) -> Optional[Dict]:
        """
        Update an edge.
        
        Args:
            uid: Edge UID
            updates: Dictionary of updates
            
        Returns:
            dict: Updated edge data or None if update failed
        """
        # Update in database
        if self.db_manager:
            updated_edge = self.db_manager.update_edge(uid, updates)
            
            if updated_edge:
                # Update cache
                self.edge_cache[uid] = updated_edge
                
                # Update stats
                self.stats['edges_updated'] += 1
                
                return updated_edge
            
            return None
        
        # If no database manager, try to update the cached edge
        if uid in self.edge_cache:
            edge = self.edge_cache[uid].copy()
            edge.update(updates)
            edge['updated_at'] = datetime.now().isoformat()
            self.edge_cache[uid] = edge
            self.stats['edges_updated'] += 1
            return edge
        
        return None
    
    def delete_edge(self, uid: str) -> bool:
        """
        Delete an edge.
        
        Args:
            uid: Edge UID
            
        Returns:
            bool: True if deletion was successful
        """
        # Delete from database
        if self.db_manager:
            success = self.db_manager.delete_edge(uid)
            
            if success:
                # Remove from cache
                if uid in self.edge_cache:
                    edge = self.edge_cache.pop(uid)
                    
                    # Update type index
                    edge_type = edge.get('edge_type')
                    if edge_type and edge_type in self.edge_type_index and uid in self.edge_type_index[edge_type]:
                        self.edge_type_index[edge_type].remove(uid)
                
                # Update stats
                self.stats['edges_deleted'] += 1
                
                return True
            
            return False
        
        # If no database manager, try to remove from cache
        if uid in self.edge_cache:
            edge = self.edge_cache.pop(uid)
            
            # Update type index
            edge_type = edge.get('edge_type')
            if edge_type and edge_type in self.edge_type_index and uid in self.edge_type_index[edge_type]:
                self.edge_type_index[edge_type].remove(uid)
            
            self.stats['edges_deleted'] += 1
            return True
        
        return False
    
    def get_nodes_by_type(self, node_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """
        Get nodes by type.
        
        Args:
            node_type: Node type
            limit: Maximum number of nodes to return
            offset: Offset for pagination
            
        Returns:
            list: List of node dictionaries
        """
        # Query database
        if self.db_manager:
            nodes = self.db_manager.get_nodes_by_type(node_type, limit, offset)
            
            # Update cache
            for node in nodes:
                uid = node.get('uid')
                if uid:
                    self.node_cache[uid] = node
                    
                    # Update type index
                    if node_type not in self.node_type_index:
                        self.node_type_index[node_type] = []
                    if uid not in self.node_type_index[node_type]:
                        self.node_type_index[node_type].append(uid)
            
            return nodes
        
        # If no database manager, try to use cached nodes
        result = []
        
        if node_type in self.node_type_index:
            # Get UIDs from type index
            uids = self.node_type_index[node_type][offset:offset+limit]
            
            # Get nodes from cache
            for uid in uids:
                if uid in self.node_cache:
                    result.append(self.node_cache[uid])
        
        return result
    
    def get_edges_by_type(self, edge_type: str, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """
        Get edges by type.
        
        Args:
            edge_type: Edge type
            limit: Maximum number of edges to return
            offset: Offset for pagination
            
        Returns:
            list: List of edge dictionaries
        """
        # Query database
        if self.db_manager:
            edges = self.db_manager.get_edges_by_type(edge_type, limit, offset)
            
            # Update cache
            for edge in edges:
                uid = edge.get('uid')
                if uid:
                    self.edge_cache[uid] = edge
                    
                    # Update type index
                    if edge_type not in self.edge_type_index:
                        self.edge_type_index[edge_type] = []
                    if uid not in self.edge_type_index[edge_type]:
                        self.edge_type_index[edge_type].append(uid)
            
            return edges
        
        # If no database manager, try to use cached edges
        result = []
        
        if edge_type in self.edge_type_index:
            # Get UIDs from type index
            uids = self.edge_type_index[edge_type][offset:offset+limit]
            
            # Get edges from cache
            for uid in uids:
                if uid in self.edge_cache:
                    result.append(self.edge_cache[uid])
        
        return result
    
    def get_outgoing_edges(self, node_uid: str) -> List[Dict]:
        """
        Get outgoing edges from a node.
        
        Args:
            node_uid: Node UID
            
        Returns:
            list: List of edge dictionaries
        """
        # Query database
        if self.db_manager:
            edges = self.db_manager.get_outgoing_edges(node_uid)
            
            # Update cache
            for edge in edges:
                uid = edge.get('uid')
                if uid:
                    self.edge_cache[uid] = edge
                    
                    # Update type index
                    edge_type = edge.get('edge_type')
                    if edge_type:
                        if edge_type not in self.edge_type_index:
                            self.edge_type_index[edge_type] = []
                        if uid not in self.edge_type_index[edge_type]:
                            self.edge_type_index[edge_type].append(uid)
            
            return edges
        
        # If no database manager, this operation is not supported
        logging.warning(f"[{datetime.now()}] GM: Cannot get outgoing edges without database manager")
        return []
    
    def get_incoming_edges(self, node_uid: str) -> List[Dict]:
        """
        Get incoming edges to a node.
        
        Args:
            node_uid: Node UID
            
        Returns:
            list: List of edge dictionaries
        """
        # Query database
        if self.db_manager:
            edges = self.db_manager.get_incoming_edges(node_uid)
            
            # Update cache
            for edge in edges:
                uid = edge.get('uid')
                if uid:
                    self.edge_cache[uid] = edge
                    
                    # Update type index
                    edge_type = edge.get('edge_type')
                    if edge_type:
                        if edge_type not in self.edge_type_index:
                            self.edge_type_index[edge_type] = []
                        if uid not in self.edge_type_index[edge_type]:
                            self.edge_type_index[edge_type].append(uid)
            
            return edges
        
        # If no database manager, this operation is not supported
        logging.warning(f"[{datetime.now()}] GM: Cannot get incoming edges without database manager")
        return []
    
    def search_nodes(self, query: str, node_types: Optional[List[str]] = None, 
                  axis_numbers: Optional[List[int]] = None, limit: int = 100) -> List[Dict]:
        """
        Search for nodes matching a query.
        
        Args:
            query: Search query
            node_types: Optional list of node types to filter by
            axis_numbers: Optional list of axis numbers to filter by
            limit: Maximum number of nodes to return
            
        Returns:
            list: List of matching node dictionaries
        """
        # Query database
        if self.db_manager:
            nodes = self.db_manager.search_nodes(query, node_types, axis_numbers, limit)
            
            # Update cache
            for node in nodes:
                uid = node.get('uid')
                if uid:
                    self.node_cache[uid] = node
                    
                    # Update type index
                    node_type = node.get('node_type')
                    if node_type:
                        if node_type not in self.node_type_index:
                            self.node_type_index[node_type] = []
                        if uid not in self.node_type_index[node_type]:
                            self.node_type_index[node_type].append(uid)
            
            # Update stats
            self.stats['queries_executed'] += 1
            
            return nodes
        
        # If no database manager, this operation is not supported
        logging.warning(f"[{datetime.now()}] GM: Cannot search nodes without database manager")
        return []
    
    def get_neighbors(self, node_uid: str, edge_types: Optional[List[str]] = None,
                    direction: str = 'both', max_depth: int = 1) -> Dict:
        """
        Get neighboring nodes up to a specified depth.
        
        Args:
            node_uid: Starting node UID
            edge_types: Optional list of edge types to filter by
            direction: Direction of traversal ('outgoing', 'incoming', or 'both')
            max_depth: Maximum traversal depth
            
        Returns:
            dict: Dictionary with 'nodes' and 'edges' lists
        """
        # Query database
        if self.db_manager:
            result = self.db_manager.get_neighbors(node_uid, edge_types, direction, max_depth)
            
            # Update cache
            for node in result.get('nodes', []):
                uid = node.get('uid')
                if uid:
                    self.node_cache[uid] = node
                    
                    # Update type index
                    node_type = node.get('node_type')
                    if node_type:
                        if node_type not in self.node_type_index:
                            self.node_type_index[node_type] = []
                        if uid not in self.node_type_index[node_type]:
                            self.node_type_index[node_type].append(uid)
            
            for edge in result.get('edges', []):
                uid = edge.get('uid')
                if uid:
                    self.edge_cache[uid] = edge
                    
                    # Update type index
                    edge_type = edge.get('edge_type')
                    if edge_type:
                        if edge_type not in self.edge_type_index:
                            self.edge_type_index[edge_type] = []
                        if uid not in self.edge_type_index[edge_type]:
                            self.edge_type_index[edge_type].append(uid)
            
            return result
        
        # If no database manager, this operation is not supported
        logging.warning(f"[{datetime.now()}] GM: Cannot get neighbors without database manager")
        return {'nodes': [], 'edges': []}
    
    def get_stats(self) -> Dict:
        """
        Get graph manager statistics.
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            **self.stats,
            'cache_stats': {
                'nodes_cached': len(self.node_cache),
                'edges_cached': len(self.edge_cache),
                'node_types_indexed': len(self.node_type_index),
                'edge_types_indexed': len(self.edge_type_index)
            }
        }