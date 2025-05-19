
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
