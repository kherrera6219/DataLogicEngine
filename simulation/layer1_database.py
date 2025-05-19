
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Layer 1 Database

This module implements the core Layer 1 database for the UKG system.
It provides the foundation for the 13-axis knowledge representation.
"""

import logging
import json
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Layer1Database:
    """Implements the Layer 1 database for UKG, focusing on basic storage and retrieval."""
    
    def __init__(self):
        """Initialize the Layer 1 database."""
        self.nodes = {}
        self.relationships = {}
        self.axis_indexes = {i: [] for i in range(1, 14)}  # One index per axis
        self.label_index = {}
        self.created_at = datetime.now().isoformat()
        
        # Initialize database structure
        self._initialize_structure()
        
        logger.info("Layer1Database initialized")
    
    def _initialize_structure(self):
        """Initialize the basic database structure."""
        # Define the 13 axes
        self.axes = {
            1: {"name": "Pillar Levels", "description": "Knowledge abstraction levels"},
            2: {"name": "Sectors", "description": "Industry and domain sectors"},
            3: {"name": "Topics", "description": "Subject areas and themes"},
            4: {"name": "Methods", "description": "Methodologies and approaches"},
            5: {"name": "Tools", "description": "Technologies and resources"},
            6: {"name": "Regulatory Frameworks", "description": "Laws and regulations"},
            7: {"name": "Compliance Standards", "description": "Compliance requirements"},
            8: {"name": "Knowledge Expert", "description": "Domain knowledge expertise"},
            9: {"name": "Sector Expert", "description": "Industry expertise"},
            10: {"name": "Regulatory Expert", "description": "Regulatory expertise"},
            11: {"name": "Compliance Expert", "description": "Compliance expertise"},
            12: {"name": "Locations", "description": "Geographic contexts"},
            13: {"name": "Time", "description": "Temporal contexts"}
        }
    
    def add_node(self, axis: int, label: str, level: int = 1, 
                description: str = "", attributes: Dict = None) -> str:
        """
        Add a node to the database.
        
        Args:
            axis: Axis number (1-13)
            label: Node label
            level: Node level in the hierarchy
            description: Node description
            attributes: Additional node attributes
            
        Returns:
            Node ID
        """
        if axis < 1 or axis > 13:
            raise ValueError(f"Invalid axis number: {axis}. Must be between 1 and 13.")
        
        node_id = f"node_{axis}_{level}_{uuid.uuid4().hex[:8]}"
        
        node = {
            "node_id": node_id,
            "axis": axis,
            "label": label,
            "level": level,
            "description": description,
            "attributes": attributes or {},
            "created_at": datetime.now().isoformat()
        }
        
        self.nodes[node_id] = node
        self.axis_indexes[axis].append(node_id)
        
        # Add to label index for searching
        label_lower = label.lower()
        if label_lower not in self.label_index:
            self.label_index[label_lower] = []
        self.label_index[label_lower].append(node_id)
        
        logger.debug(f"Added node {node_id}: {label} (Axis {axis}, Level {level})")
        return node_id
    
    def add_relationship(self, source_id: str, target_id: str, 
                        rel_type: str, weight: float = 1.0,
                        attributes: Dict = None) -> str:
        """
        Add a relationship between nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_type: Relationship type
            weight: Relationship weight
            attributes: Additional attributes
            
        Returns:
            Relationship ID
        """
        if source_id not in self.nodes:
            raise ValueError(f"Source node {source_id} not found")
        
        if target_id not in self.nodes:
            raise ValueError(f"Target node {target_id} not found")
        
        rel_id = f"rel_{rel_type}_{uuid.uuid4().hex[:8]}"
        
        relationship = {
            "rel_id": rel_id,
            "source_id": source_id,
            "target_id": target_id,
            "rel_type": rel_type,
            "weight": weight,
            "attributes": attributes or {},
            "created_at": datetime.now().isoformat()
        }
        
        self.relationships[rel_id] = relationship
        
        logger.debug(f"Added relationship {rel_id}: {rel_type} from {source_id} to {target_id}")
        return rel_id
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """
        Get a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node dictionary or None if not found
        """
        return self.nodes.get(node_id)
    
    def get_relationship(self, rel_id: str) -> Optional[Dict]:
        """
        Get a relationship by ID.
        
        Args:
            rel_id: Relationship ID
            
        Returns:
            Relationship dictionary or None if not found
        """
        return self.relationships.get(rel_id)
    
    def get_nodes_by_axis(self, axis: int) -> List[Dict]:
        """
        Get all nodes for a specific axis.
        
        Args:
            axis: Axis number (1-13)
            
        Returns:
            List of node dictionaries
        """
        if axis < 1 or axis > 13:
            return []
        
        return [self.nodes[node_id] for node_id in self.axis_indexes[axis] 
                if node_id in self.nodes]
    
    def search_nodes(self, query: str, axis: int = None) -> List[Dict]:
        """
        Search for nodes by label or description.
        
        Args:
            query: Search term
            axis: Optional axis to restrict search
            
        Returns:
            List of matching node dictionaries
        """
        query = query.lower()
        results = []
        
        # Direct match in label index
        if query in self.label_index:
            for node_id in self.label_index[query]:
                node = self.nodes.get(node_id)
                if node and (axis is None or node["axis"] == axis):
                    results.append(node)
        
        # Partial match in all nodes
        for node_id, node in self.nodes.items():
            if node in results:
                continue
                
            if axis is not None and node["axis"] != axis:
                continue
                
            label = node["label"].lower()
            description = node.get("description", "").lower()
            
            if query in label or query in description:
                results.append(node)
        
        return results
    
    def get_node_relationships(self, node_id: str, direction: str = "both") -> List[Dict]:
        """
        Get relationships for a node.
        
        Args:
            node_id: Node ID
            direction: "outgoing", "incoming", or "both"
            
        Returns:
            List of relationship dictionaries
        """
        if node_id not in self.nodes:
            return []
        
        results = []
        
        for rel_id, rel in self.relationships.items():
            if direction in ["outgoing", "both"] and rel["source_id"] == node_id:
                results.append(rel)
            elif direction in ["incoming", "both"] and rel["target_id"] == node_id:
                results.append(rel)
        
        return results
    
    def export_data(self, file_path: str = None) -> Dict:
        """
        Export database data to a file or return as a dictionary.
        
        Args:
            file_path: Optional file path for export
            
        Returns:
            Database data dictionary
        """
        data = {
            "metadata": {
                "created_at": self.created_at,
                "exported_at": datetime.now().isoformat(),
                "node_count": len(self.nodes),
                "relationship_count": len(self.relationships)
            },
            "axes": self.axes,
            "nodes": self.nodes,
            "relationships": self.relationships
        }
        
        if file_path:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Exported database to {file_path}")
        
        return data
    
    def import_data(self, data: Dict, merge: bool = False):
        """
        Import data into the database.
        
        Args:
            data: Data dictionary to import
            merge: Whether to merge with existing data
        """
        if not merge:
            self.nodes = {}
            self.relationships = {}
            self.axis_indexes = {i: [] for i in range(1, 14)}
            self.label_index = {}
        
        # Import nodes
        for node_id, node in data.get("nodes", {}).items():
            if node_id not in self.nodes:
                self.nodes[node_id] = node
                
                axis = node.get("axis")
                if axis and 1 <= axis <= 13:
                    self.axis_indexes[axis].append(node_id)
                
                label = node.get("label", "").lower()
                if label:
                    if label not in self.label_index:
                        self.label_index[label] = []
                    self.label_index[label].append(node_id)
        
        # Import relationships
        for rel_id, rel in data.get("relationships", {}).items():
            if rel_id not in self.relationships:
                self.relationships[rel_id] = rel
        
        logger.info(f"Imported {len(data.get('nodes', {}))} nodes and "
                   f"{len(data.get('relationships', {}))} relationships")
    
    def import_from_file(self, file_path: str, merge: bool = False):
        """
        Import data from a file.
        
        Args:
            file_path: Path to data file
            merge: Whether to merge with existing data
        """
        if not os.path.exists(file_path):
            logger.error(f"Import file {file_path} not found")
            return False
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.import_data(data, merge)
            return True
            
        except Exception as e:
            logger.error(f"Error importing data from {file_path}: {str(e)}")
            return False
    
    def get_stats(self) -> Dict:
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
            "relationship_types": rel_types
        }
"""
Layer 1 Database Module

This module implements the base layer database for the UKG system.
"""

import os
import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Layer1Database:
    """
    Layer 1 Database for the UKG system, providing basic storage and
    retrieval of nodes and relationships.
    """
    
    def __init__(self, load_from_file: bool = False, filepath: str = "data/layer1_database.json"):
        """
        Initialize the Layer 1 Database.
        
        Args:
            load_from_file: Whether to load data from a file
            filepath: Path to the JSON file to load from or save to
        """
        self.nodes = {}  # node_id -> node_data
        self.relationships = {}  # rel_id -> rel_data
        self.filepath = filepath
        self.axis_names = {
            1: "Pillar Levels",
            2: "Sectors",
            3: "Topics",
            4: "Methods",
            5: "Tools",
            6: "Regulatory Frameworks",
            7: "Compliance Standards",
            8: "Knowledge Expert",
            9: "Sector Expert",
            10: "Regulatory Expert",
            11: "Compliance Expert",
            12: "Locations",
            13: "Time"
        }
        
        if load_from_file and os.path.exists(filepath):
            self.import_from_json(filepath)
            
        logger.info("Layer1Database initialized")
    
    def add_node(self, node_id: str, axis_id: int, label: str, description: str, **attributes) -> str:
        """
        Add a node to the database.
        
        Args:
            node_id: Unique identifier for the node
            axis_id: Axis ID (1-13)
            label: Display name
            description: Description
            **attributes: Additional attributes
            
        Returns:
            The node ID
        """
        self.nodes[node_id] = {
            'id': node_id,
            'axis_id': axis_id,
            'label': label,
            'description': description,
            'created_at': datetime.now().isoformat(),
            **attributes
        }
        return node_id
    
    def add_relationship(self, rel_id: str, source: str, target: str, 
                         rel_type: str, weight: float = 0.5, **attributes) -> str:
        """
        Add a relationship between nodes.
        
        Args:
            rel_id: Unique identifier for the relationship
            source: Source node ID
            target: Target node ID
            rel_type: Type of relationship
            weight: Strength of relationship (0.0 to 1.0)
            **attributes: Additional attributes
            
        Returns:
            The relationship ID
        """
        if source not in self.nodes or target not in self.nodes:
            logger.warning(f"Cannot create relationship: source or target not found")
            return None
            
        self.relationships[rel_id] = {
            'id': rel_id,
            'source': source,
            'target': target,
            'type': rel_type,
            'weight': weight,
            'created_at': datetime.now().isoformat(),
            **attributes
        }
        return rel_id
    
    def get_node(self, node_id: str) -> Dict:
        """
        Get a node by ID.
        
        Args:
            node_id: The node ID
            
        Returns:
            Node data or None if not found
        """
        return self.nodes.get(node_id, None)
    
    def get_relationship(self, rel_id: str) -> Dict:
        """
        Get a relationship by ID.
        
        Args:
            rel_id: The relationship ID
            
        Returns:
            Relationship data or None if not found
        """
        return self.relationships.get(rel_id, None)
    
    def get_nodes_by_axis(self, axis_id: int) -> List[Dict]:
        """
        Get all nodes for a specific axis.
        
        Args:
            axis_id: The axis ID (1-13)
            
        Returns:
            List of nodes
        """
        return [node for node in self.nodes.values() if node['axis_id'] == axis_id]
    
    def get_relationships_by_type(self, rel_type: str) -> List[Dict]:
        """
        Get all relationships of a specific type.
        
        Args:
            rel_type: The relationship type
            
        Returns:
            List of relationships
        """
        return [rel for rel in self.relationships.values() if rel['type'] == rel_type]
    
    def get_relationships_for_node(self, node_id: str) -> List[Dict]:
        """
        Get all relationships for a node.
        
        Args:
            node_id: The node ID
            
        Returns:
            List of relationships
        """
        result = []
        
        # Get outgoing relationships
        for rel in self.relationships.values():
            if rel['source'] == node_id:
                target_node = self.get_node(rel['target'])
                if target_node:
                    result.append({
                        **rel,
                        'direction': 'outgoing',
                        'other_node_id': rel['target'],
                        'other_node_label': target_node['label'],
                        'other_node_axis_id': target_node['axis_id'],
                        'other_node_axis_name': self.get_axis_name(target_node['axis_id'])
                    })
        
        # Get incoming relationships
        for rel in self.relationships.values():
            if rel['target'] == node_id:
                source_node = self.get_node(rel['source'])
                if source_node:
                    result.append({
                        **rel,
                        'direction': 'incoming',
                        'other_node_id': rel['source'],
                        'other_node_label': source_node['label'],
                        'other_node_axis_id': source_node['axis_id'],
                        'other_node_axis_name': self.get_axis_name(source_node['axis_id'])
                    })
        
        return result
    
    def get_outgoing_relationships(self, node_id: str) -> List[Dict]:
        """
        Get outgoing relationships for a node.
        
        Args:
            node_id: The node ID
            
        Returns:
            List of outgoing relationships
        """
        return [rel for rel in self.relationships.values() if rel['source'] == node_id]
    
    def get_incoming_relationships(self, node_id: str) -> List[Dict]:
        """
        Get incoming relationships for a node.
        
        Args:
            node_id: The node ID
            
        Returns:
            List of incoming relationships
        """
        return [rel for rel in self.relationships.values() if rel['target'] == node_id]
    
    def search(self, query: str) -> List[Dict]:
        """
        Search for nodes by text in label or description.
        
        Args:
            query: Search text
            
        Returns:
            List of matching nodes
        """
        query = query.lower()
        results = []
        
        for node in self.nodes.values():
            label = node['label'].lower()
            desc = node['description'].lower()
            
            if query in label or query in desc:
                # Calculate relevance score
                score = 0
                if query in label:
                    score += 2  # Higher weight for label matches
                if query in desc:
                    score += 1  # Lower weight for description matches
                
                results.append({
                    **node,
                    'score': score,
                    'axis_name': self.get_axis_name(node['axis_id'])
                })
        
        # Sort by score (descending)
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def get_axis_name(self, axis_id: int) -> str:
        """
        Get the name of an axis.
        
        Args:
            axis_id: The axis ID (1-13)
            
        Returns:
            Axis name
        """
        return self.axis_names.get(axis_id, "Unknown Axis")
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the database.
        
        Returns:
            Dictionary with statistics
        """
        nodes_per_axis = {}
        for node in self.nodes.values():
            axis_id = node['axis_id']
            if axis_id not in nodes_per_axis:
                nodes_per_axis[axis_id] = 0
            nodes_per_axis[axis_id] += 1
        
        relationships_per_type = {}
        for rel in self.relationships.values():
            rel_type = rel['type']
            if rel_type not in relationships_per_type:
                relationships_per_type[rel_type] = 0
            relationships_per_type[rel_type] += 1
        
        return {
            'total_nodes': len(self.nodes),
            'total_relationships': len(self.relationships),
            'nodes_per_axis': nodes_per_axis,
            'relationships_per_type': relationships_per_type,
            'axis_names': self.axis_names
        }
    
    def export_to_json(self, filepath: str = None) -> bool:
        """
        Export the database to a JSON file.
        
        Args:
            filepath: Path to save JSON file (uses self.filepath if None)
            
        Returns:
            True if successful, False otherwise
        """
        if filepath is None:
            filepath = self.filepath
            
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'nodes_count': len(self.nodes),
                    'relationships_count': len(self.relationships)
                },
                'nodes': list(self.nodes.values()),
                'relationships': list(self.relationships.values())
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Exported database to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting database: {str(e)}")
            return False
    
    def import_from_json(self, filepath: str = None) -> bool:
        """
        Import the database from a JSON file.
        
        Args:
            filepath: Path to JSON file (uses self.filepath if None)
            
        Returns:
            True if successful, False otherwise
        """
        if filepath is None:
            filepath = self.filepath
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Clear existing data
            self.nodes.clear()
            self.relationships.clear()
            
            # Import nodes
            for node in data.get('nodes', []):
                node_id = node['id']
                self.nodes[node_id] = node
                
            # Import relationships
            for rel in data.get('relationships', []):
                rel_id = rel['id']
                self.relationships[rel_id] = rel
                
            logger.info(f"Imported database from {filepath} with {len(self.nodes)} nodes and {len(self.relationships)} relationships")
            return True
        except Exception as e:
            logger.error(f"Error importing database: {str(e)}")
            return False
    
    def has_data(self) -> bool:
        """
        Check if the database has data.
        
        Returns:
            True if database has data, False otherwise
        """
        return len(self.nodes) > 0 and len(self.relationships) > 0
    
    def clear(self) -> None:
        """Clear all data in the database."""
        self.nodes.clear()
        self.relationships.clear()
        logger.info("Database cleared")
