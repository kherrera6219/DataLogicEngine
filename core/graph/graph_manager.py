import logging
import networkx as nx
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.ukg_db import UkgDatabaseManager

class GraphManager:
    """
    The GraphManager maintains the structure of the Universal Knowledge Graph (UKG)
    and provides methods for navigating, querying, and modifying the graph.
    It sits at the core of the 13-axis UKG system, handling interactions between
    nodes, edges, and their relationships across the entire knowledge space.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the GraphManager with configuration.
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize the graph
        self.graph = nx.MultiDiGraph()
        
        # Initialize database manager
        self.db_manager = UkgDatabaseManager()
        
        # Define axis mappings
        self.axis_labels = {
            1: "Pillar Levels",
            2: "Principles",
            3: "Perspective Categories",
            4: "Critical Dimensions",
            5: "Decision Elements",
            6: "Influence Factors", 
            7: "Points of View",
            8: "Paradigm Cases",
            9: "Engagement Models",
            10: "Epistemological Constraints",
            11: "Ethical Considerations",
            12: "Location Context",
            13: "Temporal Dynamics"
        }
        
        # Caches for better performance
        self._node_uid_to_id_cache = {}  # Cache UIDs to DB IDs
        self._original_id_to_uid_cache = {}  # Cache external IDs to UIDs
        
        # Load the UKG structure from the database
        self._sync_graph_from_db()
        
        logging.info(f"[{datetime.now()}] GraphManager initialized with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
    
    def _sync_graph_from_db(self):
        """
        Synchronize the NetworkX graph with the node and edge data from the database.
        This is called during initialization to load the UKG structure.
        """
        logging.info(f"[{datetime.now()}] GM: Syncing graph from database...")
        
        # Clear current graph and caches
        self.graph.clear()
        self._node_uid_to_id_cache.clear()
        self._original_id_to_uid_cache.clear()
        
        # Step 1: Load all nodes
        # We'll do this in batches to avoid loading the entire graph at once for large graphs
        node_count = 0
        offset = 0
        batch_size = 1000
        
        while True:
            # Get a batch of nodes
            nodes_batch = []
            for axis_num in range(1, 14):  # For each of the 13 axes
                axis_nodes = self.db_manager.get_nodes_by_axis(axis_num, limit=batch_size, offset=offset)
                nodes_batch.extend(axis_nodes)
            
            if not nodes_batch:
                break  # No more nodes to load
            
            # Add nodes to the graph
            for node_data in nodes_batch:
                node_uid = node_data.get('uid')
                
                if not node_uid:
                    continue  # Skip nodes without a UID
                
                # Add to NetworkX graph
                self.graph.add_node(
                    node_uid,
                    **{
                        'node_type': node_data.get('node_type', 'GenericNode'),
                        'label': node_data.get('label', ''),
                        'description': node_data.get('description', ''),
                        'original_id': node_data.get('original_id'),
                        'axis_number': node_data.get('axis_number'),
                        'level': node_data.get('level'),
                        'attributes': node_data.get('attributes', {})
                    }
                )
                
                # Update caches
                self._node_uid_to_id_cache[node_uid] = node_data.get('id')
                if node_data.get('original_id'):
                    self._original_id_to_uid_cache[node_data['original_id']] = node_uid
                
                node_count += 1
            
            offset += batch_size
            logging.info(f"[{datetime.now()}] GM: Loaded {node_count} nodes so far...")
        
        # Step 2: Load all edges
        # We'll need to implement a batch method for edges or get all connected edges for each node
        # This is a conceptual implementation - in practice, you'd need a way to efficiently query edges
        edge_count = 0
        
        # For each node, get its connections
        for node_uid in self.graph.nodes:
            if node_uid not in self._node_uid_to_id_cache:
                continue  # Skip if node isn't in the cache
            
            outgoing_connections = self.db_manager.get_connected_nodes(node_uid, direction="outgoing")
            
            for connection in outgoing_connections:
                target_node = connection.get('node', {})
                edge_data = connection.get('edge', {})
                
                target_uid = target_node.get('uid')
                edge_uid = edge_data.get('uid')
                
                if not target_uid or not edge_uid:
                    continue  # Skip if missing UIDs
                
                # Add edge to the graph
                self.graph.add_edge(
                    node_uid,
                    target_uid,
                    key=edge_uid,  # Each edge needs a unique key in a MultiDiGraph
                    edge_type=edge_data.get('edge_type', 'GenericRelation'),
                    label=edge_data.get('label', ''),
                    weight=edge_data.get('weight', 1.0),
                    attributes=edge_data.get('attributes', {})
                )
                
                edge_count += 1
        
        logging.info(f"[{datetime.now()}] GM: Graph sync complete. Loaded {node_count} nodes and {edge_count} edges.")
    
    # Node Management Methods
    def add_node(self, uid: Optional[str] = None, node_type: str = "GenericNode", 
                label: str = "", description: Optional[str] = None, 
                original_id: Optional[str] = None, axis_number: Optional[int] = None,
                level: Optional[int] = None, attributes: Optional[Dict] = None) -> Optional[str]:
        """
        Add a new node to the UKG.
        
        Args:
            uid: Unique identifier (auto-generated if None)
            node_type: Type of node (e.g., "ConceptNode", "EntityNode")
            label: Human-readable name for the node
            description: Optional text description
            original_id: External identifier reference
            axis_number: UKG axis number (1-13)
            level: Hierarchical level within the axis
            attributes: Additional attributes as a dictionary
            
        Returns:
            str: The UID of the created node or None if creation failed
        """
        if axis_number is not None and (axis_number < 1 or axis_number > 13):
            logging.error(f"[{datetime.now()}] GM: Invalid axis number {axis_number}. Must be 1-13.")
            return None
        
        # Create the node in the database first
        node_data = self.db_manager.add_node(
            uid=uid,
            node_type=node_type,
            label=label,
            description=description,
            original_id=original_id,
            axis_number=axis_number,
            level=level,
            attributes=attributes
        )
        
        if not node_data:
            logging.error(f"[{datetime.now()}] GM: Failed to create node in database")
            return None
        
        node_uid = node_data.get('uid')
        
        # Add to NetworkX graph
        self.graph.add_node(
            node_uid,
            node_type=node_type,
            label=label,
            description=description,
            original_id=original_id,
            axis_number=axis_number,
            level=level,
            attributes=attributes
        )
        
        # Update caches
        self._node_uid_to_id_cache[node_uid] = node_data.get('id')
        if original_id:
            self._original_id_to_uid_cache[original_id] = node_uid
        
        logging.info(f"[{datetime.now()}] GM: Added node {node_uid} of type {node_type}")
        return node_uid
    
    def get_node_data_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get a node's data by its UID.
        
        Args:
            uid: Node's unique identifier
            
        Returns:
            dict: Node data or None if not found
        """
        if not self.graph.has_node(uid):
            return None
        
        node_attrs = self.graph.nodes[uid]
        return {**node_attrs, 'uid': uid}
    
    def get_node_data_by_attribute(self, attr_name: str, attr_value: Any, node_type: Optional[str] = None) -> Optional[str]:
        """
        Find a node by a specific attribute value.
        
        Args:
            attr_name: Name of the attribute to match
            attr_value: Value of the attribute to match
            node_type: Optional node type filter
            
        Returns:
            str: UID of the matching node or None if not found
        """
        # Optimize original_id lookup using cache
        if attr_name == 'original_id' and attr_value in self._original_id_to_uid_cache:
            uid = self._original_id_to_uid_cache[attr_value]
            # If node_type is specified, verify the node type matches
            if node_type and self.graph.nodes[uid].get('node_type') != node_type:
                return None
            return uid
        
        # Search through graph nodes
        for node_uid, node_attrs in self.graph.nodes(data=True):
            if node_type and node_attrs.get('node_type') != node_type:
                continue
                
            if node_attrs.get(attr_name) == attr_value:
                return node_uid
                
            # Check in attributes dict if the attribute might be nested
            if 'attributes' in node_attrs and attr_name in node_attrs['attributes']:
                if node_attrs['attributes'][attr_name] == attr_value:
                    return node_uid
        
        return None
    
    def update_node(self, uid: str, **kwargs) -> bool:
        """
        Update a node's attributes.
        
        Args:
            uid: Node's unique identifier
            **kwargs: Attributes to update
            
        Returns:
            bool: True if successful, False if node not found
        """
        if not self.graph.has_node(uid):
            logging.warning(f"[{datetime.now()}] GM: Update failed. Node {uid} not found in graph")
            return False
        
        # Update in the database first
        db_result = self.db_manager.update_node(uid, **kwargs)
        
        if not db_result:
            logging.error(f"[{datetime.now()}] GM: Failed to update node {uid} in database")
            return False
        
        # Update in the NetworkX graph
        for key, value in kwargs.items():
            self.graph.nodes[uid][key] = value
        
        # If original_id was updated, update the cache
        if 'original_id' in kwargs and kwargs['original_id']:
            self._original_id_to_uid_cache[kwargs['original_id']] = uid
        
        logging.info(f"[{datetime.now()}] GM: Updated node {uid}")
        return True
    
    def delete_node(self, uid: str) -> bool:
        """
        Delete a node and all its connected edges.
        
        Args:
            uid: Node's unique identifier
            
        Returns:
            bool: True if successful, False if node not found
        """
        if not self.graph.has_node(uid):
            logging.warning(f"[{datetime.now()}] GM: Delete failed. Node {uid} not found in graph")
            return False
        
        # Delete from the database first
        db_result = self.db_manager.delete_node(uid)
        
        if not db_result:
            logging.error(f"[{datetime.now()}] GM: Failed to delete node {uid} from database")
            return False
        
        # Remove from caches
        if uid in self._node_uid_to_id_cache:
            del self._node_uid_to_id_cache[uid]
        
        # Find and remove from original_id cache
        orig_id_to_remove = None
        for orig_id, node_uid in self._original_id_to_uid_cache.items():
            if node_uid == uid:
                orig_id_to_remove = orig_id
                break
        
        if orig_id_to_remove:
            del self._original_id_to_uid_cache[orig_id_to_remove]
        
        # Remove from the NetworkX graph
        self.graph.remove_node(uid)  # This also removes all connected edges
        
        logging.info(f"[{datetime.now()}] GM: Deleted node {uid} and its connected edges")
        return True
    
    # Edge Management Methods
    def add_edge(self, source_uid: str, target_uid: str, edge_type: str = "GenericRelation",
                label: Optional[str] = None, weight: float = 1.0, 
                attributes: Optional[Dict] = None, uid: Optional[str] = None) -> Optional[str]:
        """
        Add a new edge between two nodes.
        
        Args:
            source_uid: UID of the source node
            target_uid: UID of the target node
            edge_type: Type of edge (e.g., "IsA", "HasPart")
            label: Optional human-readable label
            weight: Edge weight/importance (default 1.0)
            attributes: Additional attributes as dictionary
            uid: Optional edge UID (auto-generated if None)
            
        Returns:
            str: The UID of the created edge or None if creation failed
        """
        if not self.graph.has_node(source_uid) or not self.graph.has_node(target_uid):
            logging.warning(f"[{datetime.now()}] GM: Edge creation failed. Source or target node not found")
            return None
        
        # Create the edge in the database first
        edge_data = self.db_manager.add_edge(
            source_uid=source_uid,
            target_uid=target_uid,
            edge_type=edge_type,
            label=label,
            weight=weight,
            attributes=attributes,
            uid=uid
        )
        
        if not edge_data:
            logging.error(f"[{datetime.now()}] GM: Failed to create edge in database")
            return None
        
        edge_uid = edge_data.get('uid')
        
        # Add to NetworkX graph
        self.graph.add_edge(
            source_uid,
            target_uid,
            key=edge_uid,  # Each edge needs a unique key in a MultiDiGraph
            edge_type=edge_type,
            label=label,
            weight=weight,
            attributes=attributes
        )
        
        logging.info(f"[{datetime.now()}] GM: Added edge {edge_uid} from {source_uid} to {target_uid}")
        return edge_uid
    
    def get_pillar_level_uid(self, pl_identifier: str) -> Optional[str]:
        """
        Get the UID of a Pillar Level node by its identifier.
        
        Args:
            pl_identifier: Pillar Level ID (e.g., "PL01", "PL25", "PL99")
            
        Returns:
            str: UID of the Pillar Level node or None if not found
        """
        # Normalize to uppercase PL format
        if pl_identifier.lower().startswith("pl"):
            pl_id = pl_identifier.upper()
        else:
            # Assume it's just the number
            try:
                pl_num = int(pl_identifier)
                pl_id = f"PL{pl_num:02d}"  # Format as PL01, PL02, etc.
            except ValueError:
                return None
        
        # First check cache
        if pl_id in self._original_id_to_uid_cache:
            return self._original_id_to_uid_cache[pl_id]
        
        # Look for node with this original_id
        return self.get_node_data_by_attribute("original_id", pl_id, "PillarLevelNode")
    
    def search_nodes(self, query: str, node_types: Optional[List[str]] = None, 
                   axis_numbers: Optional[List[int]] = None, limit: int = 10) -> List[Dict]:
        """
        Search for nodes matching a query.
        
        Args:
            query: Search query
            node_types: Optional list of node types to filter on
            axis_numbers: Optional list of axis numbers to filter on
            limit: Maximum number of results to return
            
        Returns:
            list: Matching nodes
        """
        results = []
        query_lower = query.lower()
        
        # Search through graph nodes
        for node_uid, node_attrs in self.graph.nodes(data=True):
            # Apply filters
            if node_types and node_attrs.get('node_type') not in node_types:
                continue
                
            if axis_numbers and node_attrs.get('axis_number') not in axis_numbers:
                continue
                
            # Check if query matches label or description
            label = str(node_attrs.get('label', '')).lower()
            description = str(node_attrs.get('description', '')).lower()
            
            if query_lower in label or query_lower in description:
                node_data = {**node_attrs, 'uid': node_uid}
                results.append(node_data)
                
                if len(results) >= limit:
                    break
        
        return results