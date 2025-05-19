"""
Layer 1 Database Module

This module implements the foundational Layer 1 database for the UKG system.
It provides basic storage and querying for the 13-axis system data.
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Layer1Database:
    """
    Implements the in-memory Layer 1 database for the UKG system.
    This serves as the foundational storage layer for the 13-axis system.
    """

    def __init__(self, data_path: str = "data/layer1_database.json"):
        """
        Initialize the Layer 1 database.

        Args:
            data_path: Path to the JSON file for persistence
        """
        self.nodes = {}  # node_id -> node data
        self.relationships = {}  # rel_id -> relationship data

        # Indexes for faster lookup
        self.axis_indexes = {}  # axis_id -> [node_id]
        self.label_index = {}  # label -> [node_id]
        self.source_index = {}  # source_id -> [rel_id]
        self.target_index = {}  # target_id -> [rel_id]
        self.rel_type_index = {}  # rel_type -> [rel_id]

        # The 13-axis system definition
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

        self.data_path = data_path

        # Try to load existing data if file exists
        self.load_from_json()

        logger.info("Layer1Database initialized")

    def add_node(self, axis: int, label: str, level: int = 1, 
                description: str = None, attributes: Dict = None, 
                node_id: str = None) -> str:
        """
        Add a node to the database.

        Args:
            axis: Axis number (1-13)
            label: Node label
            level: Level within the axis
            description: Node description
            attributes: Additional attributes
            node_id: Optional custom node ID

        Returns:
            The node ID
        """
        # Validate axis
        if axis < 1 or axis > 13:
            raise ValueError(f"Invalid axis: {axis}. Must be between 1 and 13.")

        # Generate node ID if not provided
        if not node_id:
            node_id = f"node_{axis}_{level}_{uuid.uuid4().hex[:8]}"

        # Create node data
        node_data = {
            "node_id": node_id,
            "axis": axis,
            "level": level,
            "label": label,
            "description": description or "",
            "attributes": attributes or {},
            "created_at": datetime.now().isoformat()
        }

        # Add to main storage
        self.nodes[node_id] = node_data

        # Update indexes
        if axis not in self.axis_indexes:
            self.axis_indexes[axis] = []
        self.axis_indexes[axis].append(node_id)

        if label not in self.label_index:
            self.label_index[label] = []
        self.label_index[label].append(node_id)

        logger.debug(f"Added node: {node_id} to axis {axis}, level {level}: {label}")
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

        # Create relationship data
        rel_data = {
            "rel_id": rel_id,
            "source_id": source_id,
            "target_id": target_id,
            "rel_type": rel_type,
            "weight": weight,
            "attributes": attributes or {},
            "created_at": datetime.now().isoformat()
        }

        # Add to main storage
        self.relationships[rel_id] = rel_data

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
        return self.nodes.get(node_id)

    def get_relationship(self, rel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a relationship by its ID.

        Args:
            rel_id: Relationship ID

        Returns:
            Relationship data dictionary or None if not found
        """
        return self.relationships.get(rel_id)

    def get_nodes_by_axis(self, axis: int) -> List[Dict[str, Any]]:
        """
        Get all nodes for a specific axis.

        Args:
            axis: Axis number (1-13)

        Returns:
            List of node data dictionaries
        """
        node_ids = self.axis_indexes.get(axis, [])
        return [self.nodes[node_id] for node_id in node_ids if node_id in self.nodes]

    def get_nodes_by_level(self, axis: int, level: int) -> List[Dict[str, Any]]:
        """
        Get all nodes for a specific axis and level.

        Args:
            axis: Axis number (1-13)
            level: Level within the axis

        Returns:
            List of node data dictionaries
        """
        nodes = self.get_nodes_by_axis(axis)
        return [node for node in nodes if node.get('level') == level]

    def search(self, query: str, axis: int = None) -> List[Dict[str, Any]]:
        """
        Search for nodes by label or description.

        Args:
            query: Search query
            axis: Optional axis to search within

        Returns:
            List of matching node data dictionaries
        """
        results = []
        query = query.lower()

        for node_id, node in self.nodes.items():
            # Skip if not in specified axis
            if axis is not None and node['axis'] != axis:
                continue

            # Check for matches in label or description
            if (query in node['label'].lower() or 
                (node['description'] and query in node['description'].lower())):
                node_with_axis_name = node.copy()
                node_with_axis_name['axis_name'] = self.axes[node['axis']]['name']
                results.append(node_with_axis_name)

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
            if rel and (not rel_types or rel['rel_type'] in rel_types):
                relationships.append(rel)

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
            if rel and (not rel_types or rel['rel_type'] in rel_types):
                relationships.append(rel)

        return relationships

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[Dict[str, Any]]:
        """
        Get neighboring nodes of a node.

        Args:
            node_id: Node ID
            direction: Direction of traversal ("outgoing", "incoming", or "both")

        Returns:
            List of neighboring node data dictionaries
        """
        if node_id not in self.nodes:
            return []

        neighbors = []

        if direction in ["outgoing", "both"]:
            for rel in self.get_outgoing_relationships(node_id):
                target_id = rel['target_id']
                if target_id in self.nodes:
                    neighbors.append(self.nodes[target_id])

        if direction in ["incoming", "both"]:
            for rel in self.get_incoming_relationships(node_id):
                source_id = rel['source_id']
                if source_id in self.nodes:
                    neighbors.append(self.nodes[source_id])

        return neighbors

    def export_to_json(self, file_path: str = None) -> bool:
        """
        Export the database to a JSON file.

        Args:
            file_path: Optional path to save the JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = file_path or self.data_path

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            data = {
                "nodes": self.nodes,
                "relationships": self.relationships,
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "node_count": len(self.nodes),
                    "relationship_count": len(self.relationships)
                }
            }

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported database to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting database: {str(e)}")
            return False

    def load_from_json(self, file_path: str = None) -> bool:
        """
        Load the database from a JSON file.

        Args:
            file_path: Optional path to the JSON file

        Returns:
            True if successful, False otherwise
        """
        input_path = file_path or self.data_path

        if not os.path.exists(input_path):
            logger.warning(f"Database file not found: {input_path}")
            return False

        try:
            with open(input_path, 'r') as f:
                data = json.load(f)

            # Load nodes
            for node_id, node_data in data.get("nodes", {}).items():
                self.nodes[node_id] = node_data

                # Update indexes
                axis = node_data.get("axis")
                if axis is not None:
                    if axis not in self.axis_indexes:
                        self.axis_indexes[axis] = []
                    self.axis_indexes[axis].append(node_id)

                label = node_data.get("label")
                if label is not None:
                    if label not in self.label_index:
                        self.label_index[label] = []
                    self.label_index[label].append(node_id)

            # Load relationships
            for rel_id, rel_data in data.get("relationships", {}).items():
                self.relationships[rel_id] = rel_data

                # Update indexes
                source_id = rel_data.get("source_id")
                if source_id is not None:
                    if source_id not in self.source_index:
                        self.source_index[source_id] = []
                    self.source_index[source_id].append(rel_id)

                target_id = rel_data.get("target_id")
                if target_id is not None:
                    if target_id not in self.target_index:
                        self.target_index[target_id] = []
                    self.target_index[target_id].append(rel_id)

                rel_type = rel_data.get("rel_type")
                if rel_type is not None:
                    if rel_type not in self.rel_type_index:
                        self.rel_type_index[rel_type] = []
                    self.rel_type_index[rel_type].append(rel_id)

            logger.info(f"Loaded database from {input_path} with {len(self.nodes)} nodes and {len(self.relationships)} relationships")
            return True
        except Exception as e:
            logger.error(f"Error loading database: {str(e)}")
            return False

    def clear(self):
        """Clear all data from the database."""
        self.nodes = {}
        self.relationships = {}
        self.axis_indexes = {}
        self.label_index = {}
        self.source_index = {}
        self.target_index = {}
        self.rel_type_index = {}

        logger.info("Database cleared")

    def has_data(self) -> bool:
        """
        Check if the database has any data.

        Returns:
            True if the database has nodes, False otherwise
        """
        return len(self.nodes) > 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        axis_counts = {i: len(nodes) for i, nodes in self.axis_indexes.items()}
        rel_types = {}

        for rel in self.relationships.values():
            rel_type = rel.get("rel_type")
            if rel_type:
                rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "nodes_per_axis": axis_counts,
            "relationships_per_type": rel_types,
            "axis_names": {i: info["name"] for i, info in self.axes.items()}
        }