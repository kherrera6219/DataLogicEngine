
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
