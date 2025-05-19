
"""
Universal Knowledge Graph (UKG) System - Layer 2: Nested Simulated Knowledge Database

This module implements Layer 2 of the UKG system, which contains the structured
Pillar Levels, 13-axis coordination system, and Quad Persona Simulation Engine.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Union, Tuple
import uuid
from datetime import datetime
import networkx as nx

from quad_persona.quad_engine import QuadPersonaEngine, QueryState
from simulation.refinement_workflow import RefinementWorkflow

logger = logging.getLogger(__name__)

class AxisNode:
    """Represents a node in the 13-axis coordinate system."""
    
    def __init__(self, node_id: str, axis_number: int, level: int, 
                 label: str, description: str = None, attributes: Dict = None):
        """Initialize an axis node."""
        self.node_id = node_id
        self.axis_number = axis_number
        self.level = level
        self.label = label
        self.description = description
        self.attributes = attributes or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "node_id": self.node_id,
            "axis_number": self.axis_number,
            "level": self.level,
            "label": self.label,
            "description": self.description,
            "attributes": self.attributes,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AxisNode':
        """Create an AxisNode from a dictionary."""
        node = cls(
            node_id=data.get("node_id"),
            axis_number=data.get("axis_number"),
            level=data.get("level"),
            label=data.get("label"),
            description=data.get("description"),
            attributes=data.get("attributes", {})
        )
        node.created_at = data.get("created_at", datetime.now().isoformat())
        return node


class AxisRelationship:
    """Represents a relationship between nodes in the 13-axis system."""
    
    def __init__(self, rel_id: str, source_id: str, target_id: str, 
                 rel_type: str, weight: float = 1.0, attributes: Dict = None):
        """Initialize an axis relationship."""
        self.rel_id = rel_id
        self.source_id = source_id
        self.target_id = target_id
        self.rel_type = rel_type
        self.weight = weight
        self.attributes = attributes or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "rel_id": self.rel_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": self.rel_type,
            "weight": self.weight,
            "attributes": self.attributes,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AxisRelationship':
        """Create an AxisRelationship from a dictionary."""
        rel = cls(
            rel_id=data.get("rel_id"),
            source_id=data.get("source_id"),
            target_id=data.get("target_id"),
            rel_type=data.get("rel_type"),
            weight=data.get("weight", 1.0),
            attributes=data.get("attributes", {})
        )
        rel.created_at = data.get("created_at", datetime.now().isoformat())
        return rel


class ThirteenAxisSystem:
    """Implements the 13-axis coordinate system for the UKG."""
    
    def __init__(self):
        """Initialize the 13-axis system."""
        self.axes = {
            1: {"name": "Pillar Levels", "description": "Levels of knowledge from universal to specific"},
            2: {"name": "Sectors", "description": "Industry sectors and market areas"},
            3: {"name": "Topics", "description": "Subject matters and concepts"},
            4: {"name": "Methods", "description": "Methodologies, approaches, and techniques"},
            5: {"name": "Tools", "description": "Software, hardware, and resources"},
            6: {"name": "Regulatory Frameworks", "description": "Laws, regulations, and policies"},
            7: {"name": "Compliance Standards", "description": "Standards, best practices, and requirements"},
            8: {"name": "Knowledge Expert", "description": "Domain knowledge expertise perspective"},
            9: {"name": "Sector Expert", "description": "Industry-specific expertise perspective"},
            10: {"name": "Regulatory Expert", "description": "Regulatory expertise perspective"},
            11: {"name": "Compliance Expert", "description": "Compliance expertise perspective"},
            12: {"name": "Locations", "description": "Geographic and spatial context"},
            13: {"name": "Time", "description": "Temporal and historical context"}
        }
        
        # Create a directed graph for axis relationships
        self.graph = nx.DiGraph()
        
        # Initialize the graph with the 13 axes as nodes
        for axis_num, axis_info in self.axes.items():
            self.graph.add_node(axis_num, **axis_info)
        
        # Define relationships between axes
        self._initialize_axis_relationships()
        
        logger.info("13-Axis System initialized")
    
    def _initialize_axis_relationships(self):
        """Initialize the relationships between axes."""
        # Pillar Levels (Axis 1) influences all other axes
        for i in range(2, 14):
            self.graph.add_edge(1, i, weight=1.0, rel_type="influences")
        
        # Sector-Topic relationships (Axis 2 -> Axis 3)
        self.graph.add_edge(2, 3, weight=0.9, rel_type="contains")
        
        # Topic-Method relationships (Axis 3 -> Axis 4)
        self.graph.add_edge(3, 4, weight=0.8, rel_type="uses")
        
        # Method-Tool relationships (Axis 4 -> Axis 5)
        self.graph.add_edge(4, 5, weight=0.7, rel_type="employs")
        
        # Regulatory-Compliance relationships (Axis 6 -> Axis 7)
        self.graph.add_edge(6, 7, weight=0.9, rel_type="enforces")
        
        # Expert perspective relationships (Axes 8-11 form a cycle)
        self.graph.add_edge(8, 9, weight=0.8, rel_type="informs")
        self.graph.add_edge(9, 10, weight=0.8, rel_type="informs")
        self.graph.add_edge(10, 11, weight=0.8, rel_type="informs")
        self.graph.add_edge(11, 8, weight=0.8, rel_type="informs")
        
        # Location-Time relationships (Axis 12 -> Axis 13)
        self.graph.add_edge(12, 13, weight=0.7, rel_type="contextualized_by")
        
        # Other cross-axis relationships
        self.graph.add_edge(2, 6, weight=0.7, rel_type="regulated_by")  # Sectors are regulated
        self.graph.add_edge(3, 8, weight=0.8, rel_type="expertise_in")  # Topics have knowledge experts
        self.graph.add_edge(4, 9, weight=0.7, rel_type="practiced_by")  # Methods practiced by sector experts
        self.graph.add_edge(6, 10, weight=0.9, rel_type="expertise_in")  # Regulatory experts study frameworks
        self.graph.add_edge(7, 11, weight=0.9, rel_type="expertise_in")  # Compliance experts enforce standards
    
    def get_axis_info(self, axis_num: int) -> Dict[str, Any]:
        """
        Get information about a specific axis.
        
        Args:
            axis_num: The axis number (1-13)
            
        Returns:
            Dictionary with axis information
        """
        if axis_num in self.axes:
            return self.axes[axis_num]
        return {"error": f"Axis {axis_num} not found"}
    
    def get_related_axes(self, axis_num: int) -> List[Dict[str, Any]]:
        """
        Get axes that are directly related to the specified axis.
        
        Args:
            axis_num: The axis number (1-13)
            
        Returns:
            List of related axis information
        """
        if axis_num not in self.graph:
            return []
        
        related_axes = []
        
        # Get outgoing connections
        for target in self.graph.successors(axis_num):
            edge_data = self.graph.get_edge_data(axis_num, target)
            related_axes.append({
                "axis_num": target,
                "name": self.axes[target]["name"],
                "description": self.axes[target]["description"],
                "relationship": "outgoing",
                "rel_type": edge_data.get("rel_type", "related"),
                "weight": edge_data.get("weight", 1.0)
            })
        
        # Get incoming connections
        for source in self.graph.predecessors(axis_num):
            edge_data = self.graph.get_edge_data(source, axis_num)
            related_axes.append({
                "axis_num": source,
                "name": self.axes[source]["name"],
                "description": self.axes[source]["description"],
                "relationship": "incoming",
                "rel_type": edge_data.get("rel_type", "related"),
                "weight": edge_data.get("weight", 1.0)
            })
        
        return related_axes
    
    def find_path(self, source_axis: int, target_axis: int) -> List[Dict[str, Any]]:
        """
        Find a path between two axes.
        
        Args:
            source_axis: Source axis number
            target_axis: Target axis number
            
        Returns:
            List of axes along the path, including edge information
        """
        if source_axis not in self.graph or target_axis not in self.graph:
            return []
        
        try:
            # Find shortest path between axes
            path_nodes = nx.shortest_path(self.graph, source_axis, target_axis)
            
            if not path_nodes or len(path_nodes) < 2:
                return []
            
            # Construct path with edge information
            path = []
            for i in range(len(path_nodes) - 1):
                curr = path_nodes[i]
                next_node = path_nodes[i + 1]
                edge_data = self.graph.get_edge_data(curr, next_node)
                
                path.append({
                    "source": {
                        "axis_num": curr,
                        "name": self.axes[curr]["name"],
                        "description": self.axes[curr]["description"]
                    },
                    "target": {
                        "axis_num": next_node,
                        "name": self.axes[next_node]["name"],
                        "description": self.axes[next_node]["description"]
                    },
                    "rel_type": edge_data.get("rel_type", "related"),
                    "weight": edge_data.get("weight", 1.0)
                })
            
            return path
            
        except nx.NetworkXNoPath:
            return []
    
    def get_all_axes(self) -> Dict[int, Dict[str, Any]]:
        """
        Get information about all axes.
        
        Returns:
            Dictionary mapping axis numbers to axis information
        """
        return self.axes


class NestedLayerDatabase:
    """Implements the in-memory nested layer database for the UKG system."""
    
    def __init__(self):
        """Initialize the nested layer database."""
        self.nodes = {}  # node_id -> AxisNode
        self.relationships = {}  # rel_id -> AxisRelationship
        
        # Indexes for faster lookup
        self.axis_index = {}  # axis_number -> [node_id]
        self.level_index = {}  # (axis_number, level) -> [node_id]
        self.label_index = {}  # label -> [node_id]
        self.source_index = {}  # source_id -> [rel_id]
        self.target_index = {}  # target_id -> [rel_id]
        self.rel_type_index = {}  # rel_type -> [rel_id]
        
        # The 13-axis system
        self.axis_system = ThirteenAxisSystem()
        
        # Graph representation for efficient traversal
        self.graph = nx.DiGraph()
        
        logger.info("NestedLayerDatabase initialized")
    
    def add_node(self, axis_number: int, level: int, label: str, 
                description: str = None, attributes: Dict = None, 
                node_id: str = None) -> str:
        """
        Add a node to the database.
        
        Args:
            axis_number: Axis number (1-13)
            level: Level within the axis
            label: Node label
            description: Node description
            attributes: Additional attributes
            node_id: Optional custom node ID
            
        Returns:
            The node ID
        """
        # Validate axis number
        if axis_number < 1 or axis_number > 13:
            raise ValueError(f"Invalid axis number: {axis_number}. Must be between 1 and 13.")
        
        # Generate node ID if not provided
        if not node_id:
            node_id = f"node_{axis_number}_{level}_{uuid.uuid4().hex[:8]}"
        
        # Create node
        node = AxisNode(
            node_id=node_id,
            axis_number=axis_number,
            level=level,
            label=label,
            description=description,
            attributes=attributes
        )
        
        # Add to main storage
        self.nodes[node_id] = node
        
        # Update indexes
        if axis_number not in self.axis_index:
            self.axis_index[axis_number] = []
        self.axis_index[axis_number].append(node_id)
        
        level_key = (axis_number, level)
        if level_key not in self.level_index:
            self.level_index[level_key] = []
        self.level_index[level_key].append(node_id)
        
        if label not in self.label_index:
            self.label_index[label] = []
        self.label_index[label].append(node_id)
        
        # Add to graph
        self.graph.add_node(node_id, **node.to_dict())
        
        logger.debug(f"Added node: {node_id} to axis {axis_number}, level {level}: {label}")
        return node_id
    
    def add_relationship(self, source_id: str, target_id: str, rel_type: str,
                        weight: float = 1.0, attributes: Dict = None,
                        rel_id: str = None) -> str:
        """
        Add a relationship between nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_type: Relationship type
            weight: Relationship weight
            attributes: Additional attributes
            rel_id: Optional custom relationship ID
            
        Returns:
            The relationship ID
        """
        # Verify nodes exist
        if source_id not in self.nodes:
            raise ValueError(f"Source node not found: {source_id}")
        if target_id not in self.nodes:
            raise ValueError(f"Target node not found: {target_id}")
        
        # Generate relationship ID if not provided
        if not rel_id:
            rel_id = f"rel_{rel_type}_{uuid.uuid4().hex[:8]}"
        
        # Create relationship
        relationship = AxisRelationship(
            rel_id=rel_id,
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            weight=weight,
            attributes=attributes
        )
        
        # Add to main storage
        self.relationships[rel_id] = relationship
        
        # Update indexes
        if source_id not in self.source_index:
            self.source_index[source_id] = []
        self.source_index[source_id].append(rel_id)
        
        if target_id not in self.target_index:
            self.target_index[target_id] = []
        self.target_index[target_id].append(rel_id)
        
        if rel_type not in self.rel_type_index:
            self.rel_type_index[rel_type] = []
        self.rel_type_index[rel_type].append(rel_id)
        
        # Add to graph
        self.graph.add_edge(
            source_id, 
            target_id, 
            rel_id=rel_id,
            rel_type=rel_type,
            weight=weight,
            **relationship.to_dict()
        )
        
        logger.debug(f"Added relationship: {rel_id} from {source_id} to {target_id} of type {rel_type}")
        return rel_id
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node data dictionary or None if not found
        """
        node = self.nodes.get(node_id)
        if node:
            return node.to_dict()
        return None
    
    def get_relationship(self, rel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by its ID.
        
        Args:
            rel_id: Relationship ID
            
        Returns:
            Relationship data dictionary or None if not found
        """
        rel = self.relationships.get(rel_id)
        if rel:
            return rel.to_dict()
        return None
    
    def get_nodes_by_axis(self, axis_number: int) -> List[Dict[str, Any]]:
        """
        Get all nodes for a specific axis.
        
        Args:
            axis_number: Axis number (1-13)
            
        Returns:
            List of node data dictionaries
        """
        node_ids = self.axis_index.get(axis_number, [])
        return [self.nodes[node_id].to_dict() for node_id in node_ids if node_id in self.nodes]
    
    def get_nodes_by_level(self, axis_number: int, level: int) -> List[Dict[str, Any]]:
        """
        Get all nodes for a specific axis and level.
        
        Args:
            axis_number: Axis number (1-13)
            level: Level within the axis
            
        Returns:
            List of node data dictionaries
        """
        level_key = (axis_number, level)
        node_ids = self.level_index.get(level_key, [])
        return [self.nodes[node_id].to_dict() for node_id in node_ids if node_id in self.nodes]
    
    def search_nodes(self, query: str, axis_numbers: List[int] = None) -> List[Dict[str, Any]]:
        """
        Search for nodes by label or description.
        
        Args:
            query: Search query
            axis_numbers: Optional list of axis numbers to search within
            
        Returns:
            List of matching node data dictionaries
        """
        results = []
        query = query.lower()
        
        for node_id, node in self.nodes.items():
            # Skip if not in specified axes
            if axis_numbers and node.axis_number not in axis_numbers:
                continue
            
            # Check for matches in label or description
            if (query in node.label.lower() or 
                (node.description and query in node.description.lower())):
                results.append(node.to_dict())
        
        return results
    
    def get_outgoing_relationships(self, node_id: str, rel_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get outgoing relationships from a node.
        
        Args:
            node_id: Node ID
            rel_types: Optional list of relationship types to filter by
            
        Returns:
            List of relationship data dictionaries
        """
        if node_id not in self.nodes:
            return []
        
        rel_ids = self.source_index.get(node_id, [])
        relationships = []
        
        for rel_id in rel_ids:
            rel = self.relationships.get(rel_id)
            if rel and (not rel_types or rel.rel_type in rel_types):
                relationships.append(rel.to_dict())
        
        return relationships
    
    def get_incoming_relationships(self, node_id: str, rel_types: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get incoming relationships to a node.
        
        Args:
            node_id: Node ID
            rel_types: Optional list of relationship types to filter by
            
        Returns:
            List of relationship data dictionaries
        """
        if node_id not in self.nodes:
            return []
        
        rel_ids = self.target_index.get(node_id, [])
        relationships = []
        
        for rel_id in rel_ids:
            rel = self.relationships.get(rel_id)
            if rel and (not rel_types or rel.rel_type in rel_types):
                relationships.append(rel.to_dict())
        
        return relationships
    
    def get_neighborhood(self, node_id: str, depth: int = 1, 
                        rel_types: List[str] = None, 
                        direction: str = "both") -> Dict[str, Any]:
        """
        Get the neighborhood of a node.
        
        Args:
            node_id: Node ID
            depth: Traversal depth
            rel_types: Optional list of relationship types to filter by
            direction: Direction of traversal ("outgoing", "incoming", or "both")
            
        Returns:
            Dictionary with "nodes" and "relationships" lists
        """
        if node_id not in self.nodes:
            return {"nodes": [], "relationships": []}
        
        # BFS traversal
        visited_nodes = set([node_id])
        visited_rels = set()
        queue = [(node_id, 0)]  # (node_id, current_depth)
        
        result_nodes = [self.nodes[node_id].to_dict()]
        result_rels = []
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_depth >= depth:
                continue
            
            # Process outgoing relationships
            if direction in ["outgoing", "both"]:
                for rel_id in self.source_index.get(current_id, []):
                    rel = self.relationships.get(rel_id)
                    
                    if not rel or rel_id in visited_rels:
                        continue
                    
                    if rel_types and rel.rel_type not in rel_types:
                        continue
                    
                    target_id = rel.target_id
                    visited_rels.add(rel_id)
                    result_rels.append(rel.to_dict())
                    
                    if target_id not in visited_nodes:
                        visited_nodes.add(target_id)
                        result_nodes.append(self.nodes[target_id].to_dict())
                        queue.append((target_id, current_depth + 1))
            
            # Process incoming relationships
            if direction in ["incoming", "both"]:
                for rel_id in self.target_index.get(current_id, []):
                    rel = self.relationships.get(rel_id)
                    
                    if not rel or rel_id in visited_rels:
                        continue
                    
                    if rel_types and rel.rel_type not in rel_types:
                        continue
                    
                    source_id = rel.source_id
                    visited_rels.add(rel_id)
                    result_rels.append(rel.to_dict())
                    
                    if source_id not in visited_nodes:
                        visited_nodes.add(source_id)
                        result_nodes.append(self.nodes[source_id].to_dict())
                        queue.append((source_id, current_depth + 1))
        
        return {
            "nodes": result_nodes,
            "relationships": result_rels
        }
    
    def find_paths(self, source_id: str, target_id: str, 
                 max_depth: int = 3,
                 rel_types: List[str] = None) -> List[List[Dict[str, Any]]]:
        """
        Find paths between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_depth: Maximum path length
            rel_types: Optional list of relationship types to filter by
            
        Returns:
            List of paths, where each path is a list of relationships
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        
        # Create a filtered graph if relationship types are specified
        if rel_types:
            filtered_graph = nx.DiGraph()
            for u, v, data in self.graph.edges(data=True):
                if data.get("rel_type") in rel_types:
                    filtered_graph.add_edge(u, v, **data)
            graph = filtered_graph
        else:
            graph = self.graph
        
        # Find simple paths
        try:
            paths = list(nx.all_simple_paths(graph, source_id, target_id, max_depth))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
        
        # Convert paths to relationship data
        result_paths = []
        for path in paths:
            path_rels = []
            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]
                for _, _, edge_data in self.graph.edges(data=True):
                    if (edge_data.get("source_id") == source and 
                        edge_data.get("target_id") == target):
                        rel_id = edge_data.get("rel_id")
                        if rel_id and rel_id in self.relationships:
                            path_rels.append(self.relationships[rel_id].to_dict())
                            break
            result_paths.append(path_rels)
        
        return result_paths
    
    def load_from_yaml(self, file_path: str, axis_number: int) -> int:
        """
        Load data from a YAML file into a specific axis.
        
        Args:
            file_path: Path to YAML file
            axis_number: Axis number to load into
            
        Returns:
            Number of nodes loaded
        """
        try:
            import yaml
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return 0
            
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            nodes_added = 0
            
            # Handle different file formats
            # Example: 'Axes' list for axis definitions
            if 'Axes' in data:
                for axis_def in data['Axes']:
                    if 'number' in axis_def and axis_def['number'] == axis_number:
                        node_id = self.add_node(
                            axis_number=axis_number,
                            level=1,
                            label=axis_def.get('label', f"Axis {axis_number}"),
                            description=axis_def.get('description', ''),
                            attributes={
                                'original_id': axis_def.get('original_id', '')
                            }
                        )
                        nodes_added += 1
            
            # Example: 'Locations' list for location data
            elif 'Locations' in data and axis_number == 12:
                level = 1
                for location in data['Locations']:
                    node_id = self.add_node(
                        axis_number=12,
                        level=level,
                        label=location.get('name', ''),
                        description=location.get('description', ''),
                        attributes={
                            'type': location.get('type', ''),
                            'coordinates': location.get('coordinates', ''),
                            'country_code': location.get('country_code', '')
                        }
                    )
                    nodes_added += 1
                    level += 1
            
            # Example: 'TimePeriods' list for temporal data
            elif 'TimePeriods' in data and axis_number == 13:
                level = 1
                for period in data['TimePeriods']:
                    node_id = self.add_node(
                        axis_number=13,
                        level=level,
                        label=period.get('name', ''),
                        description=period.get('description', ''),
                        attributes={
                            'start_date': period.get('start_date', ''),
                            'end_date': period.get('end_date', ''),
                            'era': period.get('era', '')
                        }
                    )
                    nodes_added += 1
                    level += 1
            
            # Example: 'PillarLevels' for axis 1
            elif 'PillarLevels' in data and axis_number == 1:
                for pillar in data['PillarLevels']:
                    level = pillar.get('level', 1)
                    node_id = self.add_node(
                        axis_number=1,
                        level=level,
                        label=pillar.get('name', ''),
                        description=pillar.get('description', ''),
                        attributes={
                            'key_concepts': pillar.get('key_concepts', []),
                            'universal_code': pillar.get('universal_code', '')
                        }
                    )
                    nodes_added += 1
            
            # General purpose handler
            else:
                main_key = list(data.keys())[0] if data else None
                if main_key and isinstance(data[main_key], list):
                    level = 1
                    for item in data[main_key]:
                        if isinstance(item, dict):
                            label = item.get('name', item.get('label', f"Item {level}"))
                            description = item.get('description', '')
                            node_id = self.add_node(
                                axis_number=axis_number,
                                level=level,
                                label=label,
                                description=description,
                                attributes=item
                            )
                            nodes_added += 1
                            level += 1
            
            logger.info(f"Loaded {nodes_added} nodes for axis {axis_number} from {file_path}")
            return nodes_added
            
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            return 0
    
    def load_all_data(self, data_dir: str = "data/ukg") -> Dict[str, int]:
        """
        Load all data from the UKG data directory.
        
        Args:
            data_dir: Path to data directory
            
        Returns:
            Dictionary with number of nodes loaded per axis
        """
        axis_files = {
            1: "pillar_levels.yaml",
            2: "sectors.yaml",
            3: "topics.yaml",
            4: "methods.yaml",
            5: "tools.yaml",
            6: "regulatory_frameworks.yaml",
            7: "compliance_standards.yaml",
            8: "personas.yaml",  # Knowledge experts
            9: "personas.yaml",  # Sector experts
            10: "personas.yaml", # Regulatory experts
            11: "personas.yaml", # Compliance experts
            12: "locations_gazetteer.yaml",
            13: "time_periods.yaml"
        }
        
        results = {}
        
        for axis_num, file_name in axis_files.items():
            file_path = os.path.join(data_dir, file_name)
            if os.path.exists(file_path):
                count = self.load_from_yaml(file_path, axis_num)
                results[axis_num] = count
        
        # Create default relationships based on the 13-axis system
        self._create_default_relationships()
        
        return results
    
    def _create_default_relationships(self):
        """Create default relationships between nodes based on the 13-axis system."""
        # Connect pillar levels (Axis 1) hierarchically
        pillar_nodes = self.get_nodes_by_axis(1)
        pillar_nodes_by_level = {}
        
        for node in pillar_nodes:
            level = node.get('level', 0)
            if level not in pillar_nodes_by_level:
                pillar_nodes_by_level[level] = []
            pillar_nodes_by_level[level].append(node)
        
        # Connect each level to the next level
        levels = sorted(pillar_nodes_by_level.keys())
        for i in range(len(levels) - 1):
            for parent_node in pillar_nodes_by_level[levels[i]]:
                for child_node in pillar_nodes_by_level[levels[i + 1]]:
                    self.add_relationship(
                        source_id=parent_node['node_id'],
                        target_id=child_node['node_id'],
                        rel_type="contains",
                        weight=0.9
                    )
        
        # Connect sectors (Axis 2) to topics (Axis 3)
        sector_nodes = self.get_nodes_by_axis(2)
        topic_nodes = self.get_nodes_by_axis(3)
        
        for sector_node in sector_nodes:
            for topic_node in topic_nodes:
                # Check if topic is relevant to sector based on attributes
                sector_name = sector_node.get('label', '').lower()
                topic_desc = topic_node.get('description', '').lower()
                
                if sector_name in topic_desc or any(sector_name in attr.lower() for attr in topic_node.get('attributes', {}).values() if isinstance(attr, str)):
                    self.add_relationship(
                        source_id=sector_node['node_id'],
                        target_id=topic_node['node_id'],
                        rel_type="contains",
                        weight=0.8
                    )
        
        # Connect regulatory frameworks (Axis 6) to compliance standards (Axis 7)
        reg_nodes = self.get_nodes_by_axis(6)
        comp_nodes = self.get_nodes_by_axis(7)
        
        for reg_node in reg_nodes:
            for comp_node in comp_nodes:
                # Check if compliance standard is related to regulatory framework
                reg_name = reg_node.get('label', '').lower()
                comp_desc = comp_node.get('description', '').lower()
                
                if reg_name in comp_desc or any(reg_name in attr.lower() for attr in comp_node.get('attributes', {}).values() if isinstance(attr, str)):
                    self.add_relationship(
                        source_id=reg_node['node_id'],
                        target_id=comp_node['node_id'],
                        rel_type="enforces",
                        weight=0.9
                    )


class Layer2KnowledgeSimulator:
    """
    Implements Layer 2 of the UKG system, which contains the structured
    Pillar Levels, 13-axis coordination system, and Quad Persona Simulation Engine.
    """
    
    def __init__(self, layer3_handler=None):
        """
        Initialize the Layer 2 Knowledge Simulator.
        
        Args:
            layer3_handler: Optional handler for Layer 3 operations
        """
        self.nested_db = NestedLayerDatabase()
        self.quad_persona = QuadPersonaEngine()
        self.refiner = RefinementWorkflow()
        self.layer3_handler = layer3_handler
        
        # Minimum confidence threshold before escalating to Layer 3
        self.confidence_threshold = 0.95
        
        # Load all data into the nested database
        self.load_database()
        
        logger.info("Layer2KnowledgeSimulator initialized")
    
    def load_database(self):
        """Load all data into the nested database."""
        logger.info("Loading data into the nested database...")
        results = self.nested_db.load_all_data()
        
        total_nodes = sum(results.values())
        logger.info(f"Loaded {total_nodes} nodes across {len(results)} axes")
        
        # Log details per axis
        for axis_num, count in results.items():
            axis_name = self.nested_db.axis_system.get_axis_info(axis_num).get('name', f"Axis {axis_num}")
            logger.info(f"  Axis {axis_num} ({axis_name}): {count} nodes")
    
    def configure_layer3(self, layer3_handler):
        """Configure the connection to Layer 3."""
        self.layer3_handler = layer3_handler
        logger.info("Layer2KnowledgeSimulator configured with Layer 3 handler")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the nested database.
        
        Returns:
            Dictionary with database statistics
        """
        stats = {
            "total_nodes": len(self.nested_db.nodes),
            "total_relationships": len(self.nested_db.relationships),
            "nodes_per_axis": {},
            "relationships_per_type": {}
        }
        
        # Count nodes per axis
        for axis_num in range(1, 14):
            count = len(self.nested_db.get_nodes_by_axis(axis_num))
            stats["nodes_per_axis"][axis_num] = count
        
        # Count relationships per type
        for rel_type, rel_ids in self.nested_db.rel_type_index.items():
            stats["relationships_per_type"][rel_type] = len(rel_ids)
        
        return stats
    
    def query_knowledge_graph(self, query_text: str, axis_filter: List[int] = None) -> Dict[str, Any]:
        """
        Query the knowledge graph based on text.
        
        Args:
            query_text: The query text
            axis_filter: Optional list of axes to filter the search
            
        Returns:
            Dictionary with search results
        """
        # Search for nodes matching the query
        matching_nodes = self.nested_db.search_nodes(query_text, axis_filter)
        
        # For each matching node, get its immediate neighborhood
        results = []
        for node in matching_nodes:
            node_id = node.get('node_id')
            neighborhood = self.nested_db.get_neighborhood(node_id, depth=1)
            
            results.append({
                "node": node,
                "neighborhood": neighborhood
            })
        
        return {
            "query": query_text,
            "count": len(matching_nodes),
            "results": results
        }
    
    def simulate(self, query_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate knowledge processing for a query using the UKG and Quad Persona Engine.
        
        Args:
            query_payload: The query payload to process
            
        Returns:
            The processed result
        """
        query_id = query_payload.get("query_id", f"q_{uuid.uuid4().hex[:8]}")
        query_text = query_payload.get("query", "")
        context = query_payload.get("context", {})
        
        logger.info(f"Layer 2 simulating query: {query_id} - '{query_text}'")
        
        # Step 1: Query the knowledge graph
        kg_result = self.query_knowledge_graph(query_text)
        
        # Step 2: Enhance context with knowledge graph information
        enhanced_context = context.copy()
        enhanced_context["knowledge_graph"] = kg_result
        
        # Step 3: Create a query state for the quad persona engine
        query_state = QueryState(query_id=query_id, query_text=query_text, context=enhanced_context)
        
        # Step 4: Execute quad persona simulation
        self.quad_persona._process_with_all_personas(query_state)
        
        # Step 5: Execute refinement workflow
        refined_result = self.refiner.execute_workflow(query_state)
        
        # Step 6: Check confidence and escalate to Layer 3 if needed
        final_result = refined_result
        
        confidence = refined_result.get("confidence", 0)
        if confidence < self.confidence_threshold and self.layer3_handler:
            logger.info(f"Confidence {confidence} below threshold {self.confidence_threshold}, escalating to Layer 3")
            # Escalate to Layer 3 for further processing
            layer3_payload = {
                "query_id": query_id,
                "query": query_text,
                "context": enhanced_context,
                "layer2_result": refined_result
            }
            final_result = self.layer3_handler.process(layer3_payload)
        
        # Add database statistics to the result
        final_result["database_stats"] = self.get_database_stats()
        
        # Log completion
        logger.info(f"Layer 2 simulation complete for query: {query_id} with confidence {final_result.get('confidence', 0)}")
        
        return final_result
    
    def get_all_axes_info(self) -> Dict[str, Any]:
        """
        Get information about all 13 axes.
        
        Returns:
            Dictionary with axis information
        """
        return {
            "axes": self.nested_db.axis_system.get_all_axes(),
            "axis_relationships": [
                {
                    "source": source,
                    "target": target,
                    "relationship": data.get("rel_type", "related"),
                    "weight": data.get("weight", 1.0)
                }
                for source, target, data in self.nested_db.axis_system.graph.edges(data=True)
            ]
        }


def create_layer2_simulator(layer3_handler=None) -> Layer2KnowledgeSimulator:
    """
    Create and initialize a Layer 2 Knowledge Simulator.
    
    Args:
        layer3_handler: Optional handler for Layer 3 operations
        
    Returns:
        A configured Layer2KnowledgeSimulator
    """
    simulator = Layer2KnowledgeSimulator(layer3_handler)
    return simulator
"""
Layer 2 Knowledge Graph Database Module

This module implements the Layer 2 database that parses and processes
the 13-axis knowledge graph into a simulated in-memory database.
"""

import logging
import json
import os
import networkx as nx
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Layer2KnowledgeGraph:
    """
    Layer 2 Knowledge Graph Database that processes and indexes the 13-axis
    knowledge graph for efficient querying and knowledge extraction.
    """
    
    def __init__(self, layer1_db=None, data_dir: str = "data/ukg"):
        """
        Initialize the Layer 2 Knowledge Graph Database.
        
        Args:
            layer1_db: Optional Layer1Database instance to build upon
            data_dir: Directory containing UKG data files
        """
        self.data_dir = data_dir
        self.layer1_db = layer1_db
        self.graph = nx.MultiDiGraph()
        self.axis_data = {}
        self.indexes = {}
        self.metadata = {
            "creation_time": datetime.now().isoformat(),
            "version": "1.0.0",
            "axes_loaded": [],
            "node_count": 0,
            "edge_count": 0,
            "last_modified": datetime.now().isoformat()
        }
        logger.info("Layer2KnowledgeGraph initialized")
    
    def load_axis_data(self, axis_id: int, filename: str) -> Dict:
        """
        Load data for a specific knowledge axis from YAML file.
        
        Args:
            axis_id: The axis ID (1-13)
            filename: YAML file containing axis data
            
        Returns:
            Dictionary containing the loaded axis data
        """
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Axis {axis_id} data file {filepath} not found")
            return {}
            
        try:
            with open(filepath, 'r') as file:
                data = yaml.safe_load(file)
                logger.info(f"Loaded axis {axis_id} data from {filepath}")
                return data
        except Exception as e:
            logger.error(f"Error loading axis {axis_id} data: {str(e)}")
            return {}
    
    def build_from_layer1(self):
        """
        Build the Layer 2 knowledge graph using data from Layer 1.
        """
        if not self.layer1_db:
            logger.error("No Layer 1 database provided for building Layer 2")
            return False
        
        # Copy nodes from Layer 1, enhancing with knowledge graph properties
        for node_id, node_data in self.layer1_db.nodes.items():
            axis_id = node_data.get('axis_id')
            enhanced_data = {**node_data, 'processed_by': 'layer2'}
            
            # Add semantic properties based on axis type
            if axis_id == 4:  # Methods
                enhanced_data['application_contexts'] = ['research', 'practice', 'education']
            elif axis_id == 5:  # Tools
                enhanced_data['compatibility'] = {'os': ['Windows', 'Linux', 'MacOS'], 'version': '1.0'}
            
            self.graph.add_node(node_id, **enhanced_data)
        
        # Copy and enhance relationships
        for rel_id, rel_data in self.layer1_db.relationships.items():
            source = rel_data.get('source')
            target = rel_data.get('target')
            rel_type = rel_data.get('type')
            weight = rel_data.get('weight', 0.5)
            
            # Add more metadata to relationships
            enhanced_rel = {
                **rel_data,
                'confidence': min(weight + 0.1, 1.0),
                'timestamp': datetime.now().isoformat(),
                'layer': 2
            }
            
            self.graph.add_edge(source, target, key=rel_id, **enhanced_rel)
        
        self.metadata['node_count'] = self.graph.number_of_nodes()
        self.metadata['edge_count'] = self.graph.number_of_edges()
        self.metadata['last_modified'] = datetime.now().isoformat()
        self.metadata['built_from_layer1'] = True
        
        logger.info(f"Built Layer 2 knowledge graph from Layer 1 database with "
                  f"{self.metadata['node_count']} nodes and {self.metadata['edge_count']} edges")
        return True
    
    def process_all_axes(self):
        """
        Process and integrate data from all 13 axes into the knowledge graph.
        """
        # Axis file mapping
        axis_files = {
            1: "pillar_levels.yaml",
            2: "sectors.yaml",
            3: "topics.yaml",
            4: "methods.yaml",
            5: "tools.yaml",
            6: "regulatory_frameworks.yaml",
            7: "compliance_standards.yaml",
            8: "contextual_experts.yaml",
            9: "sectors.yaml",  # Using sectors as proxy for sector experts
            10: "regulatory_frameworks.yaml",  # Using regulatory as proxy for experts
            11: "compliance_standards.yaml",  # Using compliance as proxy for experts
            12: "locations_gazetteer.yaml",
            13: "time_periods.yaml"
        }
        
        for axis_id, filename in axis_files.items():
            try:
                axis_data = self.load_axis_data(axis_id, filename)
                if axis_data:
                    self.integrate_axis_data(axis_id, axis_data)
                    self.axis_data[axis_id] = axis_data
                    self.metadata['axes_loaded'].append(axis_id)
            except Exception as e:
                logger.error(f"Error processing axis {axis_id}: {str(e)}")
                
        # Create indexes for efficient querying
        self.create_indexes()
        
        # Update metadata
        self.metadata['node_count'] = self.graph.number_of_nodes()
        self.metadata['edge_count'] = self.graph.number_of_edges()
        self.metadata['last_modified'] = datetime.now().isoformat()
        self.metadata['axes_processed'] = len(self.metadata['axes_loaded'])
        
        logger.info(f"Processed {len(self.metadata['axes_loaded'])} axes with "
                  f"{self.metadata['node_count']} nodes and {self.metadata['edge_count']} edges")
    
    def integrate_axis_data(self, axis_id: int, axis_data: Dict):
        """
        Integrate data from a specific axis into the knowledge graph.
        
        Args:
            axis_id: The axis ID (1-13)
            axis_data: Dictionary containing axis data
        """
        # Implementation varies by axis type
        if axis_id == 1:  # Pillar Levels
            self._integrate_pillar_levels(axis_data)
        elif axis_id == 2:  # Sectors
            self._integrate_sectors(axis_data)
        elif axis_id == 3:  # Topics
            self._integrate_topics(axis_data)
        elif axis_id == 4:  # Methods
            self._integrate_methods(axis_data)
        elif axis_id == 5:  # Tools
            self._integrate_tools(axis_data)
        elif axis_id in [6, 10]:  # Regulatory Frameworks
            self._integrate_regulatory(axis_data, is_expert=(axis_id == 10))
        elif axis_id in [7, 11]:  # Compliance Standards
            self._integrate_compliance(axis_data, is_expert=(axis_id == 11))
        elif axis_id == 8:  # Knowledge Experts
            self._integrate_knowledge_experts(axis_data)
        elif axis_id == 9:  # Sector Experts
            self._integrate_sector_experts(axis_data)
        elif axis_id == 12:  # Locations
            self._integrate_locations(axis_data)
        elif axis_id == 13:  # Time
            self._integrate_time_periods(axis_data)
    
    # Individual axis integration methods
    def _integrate_pillar_levels(self, data):
        # Implementation for Pillar Levels (Axis 1)
        for item in data.get('levels', []):
            node_id = f"PL_{item.get('id', '')}"
            self.graph.add_node(node_id, 
                                axis_id=1,
                                label=item.get('label', ''),
                                description=item.get('description', ''),
                                level=item.get('level', 0),
                                type='pillar_level')
            
            # Add relationships to parent levels
            if 'parent' in item and item['parent']:
                parent_id = f"PL_{item['parent']}"
                rel_id = f"rel_pl_{item.get('id', '')}_{item['parent']}"
                self.graph.add_edge(parent_id, node_id, key=rel_id,
                                   type='contains',
                                   weight=0.9,
                                   description='Hierarchical relationship between pillar levels')
    
    def _integrate_sectors(self, data):
        # Implementation for Sectors (Axis 2)
        for item in data.get('sectors', []):
            node_id = f"SEC_{item.get('id', '')}"
            self.graph.add_node(node_id,
                               axis_id=2,
                               label=item.get('label', ''),
                               description=item.get('description', ''),
                               type='sector')
            
            # Add relationships to categories
            for category in item.get('categories', []):
                cat_id = f"SECCAT_{category.get('id', '')}"
                self.graph.add_node(cat_id,
                                   axis_id=2,
                                   label=category.get('label', ''),
                                   description=category.get('description', ''),
                                   type='sector_category')
                
                # Sector contains category
                rel_id = f"rel_sec_{item.get('id', '')}_{category.get('id', '')}"
                self.graph.add_edge(node_id, cat_id, key=rel_id,
                                   type='contains',
                                   weight=0.8,
                                   description='Sector contains category')
    
    def _integrate_tools(self, data):
        # Process tools from the data file
        for tool_category in data:
            category_id = tool_category.get('id', '')
            category_node_id = f"TOOL_CAT_{category_id}"
            
            # Add category node
            self.graph.add_node(category_node_id,
                               axis_id=5,
                               label=tool_category.get('label', ''),
                               description=tool_category.get('description', ''),
                               type='tool_category')
            
            # Process subcategories
            for subcategory in tool_category.get('categories', []):
                subcat_id = subcategory.get('id', '')
                subcat_node_id = f"TOOL_SUBCAT_{subcat_id}"
                
                # Add subcategory node
                self.graph.add_node(subcat_node_id,
                                   axis_id=5,
                                   label=subcategory.get('label', ''),
                                   description=subcategory.get('description', ''),
                                   type='tool_subcategory')
                
                # Category contains subcategory
                rel_id = f"rel_toolcat_{category_id}_{subcat_id}"
                self.graph.add_edge(category_node_id, subcat_node_id, key=rel_id,
                                   type='contains',
                                   weight=0.9,
                                   description='Tool category contains subcategory')
                
                # Process individual tools
                for tool in subcategory.get('tools', []):
                    tool_id = tool.get('id', '')
                    tool_node_id = f"TOOL_{tool_id}"
                    
                    # Add tool node
                    self.graph.add_node(tool_node_id,
                                       axis_id=5,
                                       label=tool.get('label', ''),
                                       description=tool.get('description', ''),
                                       version=tool.get('version', ''),
                                       type='tool')
                    
                    # Subcategory contains tool
                    rel_id = f"rel_toolsubcat_{subcat_id}_{tool_id}"
                    self.graph.add_edge(subcat_node_id, tool_node_id, key=rel_id,
                                       type='contains',
                                       weight=0.9,
                                       description='Tool subcategory contains tool')
    
    def _integrate_methods(self, data):
        # Implementation for Methods (Axis 4) - similar structure to tools
        pass
    
    def _integrate_topics(self, data):
        # Implementation for Topics (Axis 3)
        pass
    
    def _integrate_regulatory(self, data, is_expert=False):
        # Implementation for Regulatory Frameworks (Axis 6/10)
        pass
    
    def _integrate_compliance(self, data, is_expert=False):
        # Implementation for Compliance Standards (Axis 7/11)
        pass
    
    def _integrate_knowledge_experts(self, data):
        # Implementation for Knowledge Experts (Axis 8)
        pass
    
    def _integrate_sector_experts(self, data):
        # Implementation for Sector Experts (Axis 9)
        pass
    
    def _integrate_locations(self, data):
        # Implementation for Locations (Axis 12)
        pass
    
    def _integrate_time_periods(self, data):
        # Implementation for Time Periods (Axis 13)
        pass
    
    def create_indexes(self):
        """
        Create indexes for efficient querying of the knowledge graph.
        """
        # Index nodes by axis
        axis_index = {}
        for node, data in self.graph.nodes(data=True):
            axis_id = data.get('axis_id')
            if axis_id not in axis_index:
                axis_index[axis_id] = []
            axis_index[axis_id].append(node)
        self.indexes['by_axis'] = axis_index
        
        # Index nodes by type
        type_index = {}
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('type')
            if node_type not in type_index:
                type_index[node_type] = []
            type_index[node_type].append(node)
        self.indexes['by_type'] = type_index
        
        # Index for text search (labels and descriptions)
        text_index = {}
        for node, data in self.graph.nodes(data=True):
            label = data.get('label', '').lower()
            desc = data.get('description', '').lower()
            
            # Index by words in label
            for word in label.split():
                if word not in text_index:
                    text_index[word] = []
                if node not in text_index[word]:
                    text_index[word].append(node)
            
            # Index by words in description
            for word in desc.split():
                if word not in text_index:
                    text_index[word] = []
                if node not in text_index[word]:
                    text_index[word].append(node)
                    
        self.indexes['text_search'] = text_index
        
        logger.info(f"Created indexes for {len(self.indexes)} query types")
    
    def query_by_axis(self, axis_id: int) -> List[Dict]:
        """
        Query nodes by axis ID.
        
        Args:
            axis_id: The axis ID (1-13)
            
        Returns:
            List of nodes belonging to the specified axis
        """
        if 'by_axis' not in self.indexes or axis_id not in self.indexes['by_axis']:
            return []
        
        results = []
        for node_id in self.indexes['by_axis'][axis_id]:
            node_data = self.graph.nodes[node_id]
            results.append({'id': node_id, **node_data})
            
        return results
    
    def search_text(self, query: str) -> List[Dict]:
        """
        Search for nodes by text in label or description.
        
        Args:
            query: Search text
            
        Returns:
            List of matching nodes
        """
        if 'text_search' not in self.indexes:
            return []
            
        query_words = query.lower().split()
        matches = set()
        
        # Find nodes that match any query word
        for word in query_words:
            if word in self.indexes['text_search']:
                for node_id in self.indexes['text_search'][word]:
                    matches.add(node_id)
        
        # Score and sort results
        scored_results = []
        for node_id in matches:
            node_data = self.graph.nodes[node_id]
            label = node_data.get('label', '').lower()
            desc = node_data.get('description', '').lower()
            
            # Calculate relevance score
            score = 0
            for word in query_words:
                if word in label:
                    score += 2  # Higher weight for label matches
                if word in desc:
                    score += 1  # Lower weight for description matches
                    
            scored_results.append({
                'id': node_id,
                'score': score,
                **node_data
            })
            
        # Sort by score (descending)
        return sorted(scored_results, key=lambda x: x['score'], reverse=True)
    
    def get_node_connections(self, node_id: str) -> Dict:
        """
        Get all incoming and outgoing connections for a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Dictionary with incoming and outgoing connections
        """
        if node_id not in self.graph:
            return {'incoming': [], 'outgoing': []}
            
        incoming = []
        for source, _, edge_data in self.graph.in_edges(node_id, data=True):
            incoming.append({
                'source': source,
                'source_data': self.graph.nodes[source],
                'relationship': edge_data
            })
            
        outgoing = []
        for _, target, edge_data in self.graph.out_edges(node_id, data=True):
            outgoing.append({
                'target': target,
                'target_data': self.graph.nodes[target],
                'relationship': edge_data
            })
            
        return {
            'incoming': incoming,
            'outgoing': outgoing
        }
    
    def compute_path(self, source: str, target: str) -> List[Dict]:
        """
        Compute the shortest path between two nodes.
        
        Args:
            source: Source node ID
            target: Target node ID
            
        Returns:
            List of nodes and edges in the path
        """
        if source not in self.graph or target not in self.graph:
            return []
            
        try:
            # Try to find shortest path
            path_nodes = nx.shortest_path(self.graph, source, target)
            
            # Convert to detailed path
            detailed_path = []
            for i in range(len(path_nodes) - 1):
                curr_node = path_nodes[i]
                next_node = path_nodes[i + 1]
                
                # Get edge data (there may be multiple edges)
                edges = list(self.graph.get_edge_data(curr_node, next_node).values())
                edge_data = edges[0] if edges else {}
                
                detailed_path.append({
                    'source': curr_node,
                    'source_data': self.graph.nodes[curr_node],
                    'target': next_node,
                    'target_data': self.graph.nodes[next_node],
                    'edge': edge_data
                })
                
            return detailed_path
        except nx.NetworkXNoPath:
            return []
    
    def export_to_json(self, filepath: str = "data/layer2_knowledge_graph.json") -> bool:
        """
        Export the knowledge graph to a JSON file.
        
        Args:
            filepath: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert graph to serializable format
            serialized_graph = {
                "metadata": self.metadata,
                "nodes": [],
                "edges": []
            }
            
            # Add nodes
            for node, data in self.graph.nodes(data=True):
                serialized_graph["nodes"].append({
                    "id": node,
                    **data
                })
                
            # Add edges
            for source, target, key, data in self.graph.edges(data=True, keys=True):
                serialized_graph["edges"].append({
                    "source": source,
                    "target": target,
                    "id": key,
                    **data
                })
                
            # Save to file
            with open(filepath, 'w') as file:
                json.dump(serialized_graph, file, indent=2)
                
            logger.info(f"Exported knowledge graph to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting knowledge graph: {str(e)}")
            return False
    
    def import_from_json(self, filepath: str = "data/layer2_knowledge_graph.json") -> bool:
        """
        Import the knowledge graph from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
                
            # Clear existing graph
            self.graph.clear()
            
            # Load metadata
            self.metadata = data.get("metadata", {})
            
            # Load nodes
            for node_data in data.get("nodes", []):
                node_id = node_data.pop("id")
                self.graph.add_node(node_id, **node_data)
                
            # Load edges
            for edge_data in data.get("edges", []):
                source = edge_data.pop("source")
                target = edge_data.pop("target")
                edge_id = edge_data.pop("id")
                self.graph.add_edge(source, target, key=edge_id, **edge_data)
                
            # Recreate indexes
            self.create_indexes()
            
            logger.info(f"Imported knowledge graph from {filepath} with "
                      f"{self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            return True
        except Exception as e:
            logger.error(f"Error importing knowledge graph: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Dictionary with graph statistics
        """
        # Node statistics by axis
        nodes_by_axis = {}
        for node, data in self.graph.nodes(data=True):
            axis_id = data.get('axis_id')
            if axis_id not in nodes_by_axis:
                nodes_by_axis[axis_id] = 0
            nodes_by_axis[axis_id] += 1
            
        # Edge statistics by type
        edges_by_type = {}
        for _, _, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get('type')
            if edge_type not in edges_by_type:
                edges_by_type[edge_type] = 0
            edges_by_type[edge_type] += 1
            
        return {
            "metadata": self.metadata,
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "nodes_by_axis": nodes_by_axis,
            "edges_by_type": edges_by_type,
            "density": nx.density(self.graph.to_undirected())
        }
