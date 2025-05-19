"""
Universal Knowledge Graph (UKG) System - Axis 1: Knowledge

This module implements the Knowledge axis for the UKG system,
providing access to the core knowledge structure organized by Pillar Levels (1-100).
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import and_, or_, func
from app import db
from models import PillarLevel, KnowledgeNode

logger = logging.getLogger(__name__)

class KnowledgeAxis:
    """Handler for Axis 1: Knowledge - Pillar Levels 1-100"""
    
    def __init__(self):
        """Initialize the Knowledge axis handler."""
        self.axis_number = 1
        self.axis_name = "Knowledge"
        self.description = "The core knowledge axis structured around Pillar Levels 1-100"
    
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """
        Navigate the Knowledge axis based on provided parameters.
        
        Parameters:
        - pillar_level_id (int): ID of a specific pillar level
        - pillar_id (str): Pillar ID code (e.g., "PL01")
        - level_range (tuple): Range of pillar levels to retrieve (e.g., (1, 10))
        - search_term (str): Text to search for in pillar level names/descriptions
        - include_nodes (bool): Whether to include associated knowledge nodes
        
        Returns:
        - Dict containing the navigation results
        """
        # Extract parameters
        pillar_level_id = kwargs.get('pillar_level_id')
        pillar_id = kwargs.get('pillar_id')
        level_range = kwargs.get('level_range')
        search_term = kwargs.get('search_term')
        include_nodes = kwargs.get('include_nodes', False)
        
        # Build query for pillar levels
        query = db.session.query(PillarLevel)
        
        # Apply filters based on provided parameters
        if pillar_level_id is not None:
            query = query.filter(PillarLevel.id == pillar_level_id)
        
        if pillar_id is not None:
            query = query.filter(PillarLevel.pillar_id == pillar_id)
        
        if level_range is not None:
            # Assuming pillar_id is in format "PLxx" where xx is a number
            start, end = level_range
            # This would need to be adapted based on actual pillar_id format
            query = query.filter(
                and_(
                    func.cast(func.substr(PillarLevel.pillar_id, 3), db.Integer) >= start,
                    func.cast(func.substr(PillarLevel.pillar_id, 3), db.Integer) <= end
                )
            )
        
        if search_term is not None:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    PillarLevel.name.ilike(search_pattern),
                    PillarLevel.description.ilike(search_pattern)
                )
            )
        
        # Execute query
        try:
            pillar_levels = query.all()
            
            # Convert to dictionary format
            result_data = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "pillar_levels": [pl.to_dict() for pl in pillar_levels],
                "count": len(pillar_levels)
            }
            
            # Include associated knowledge nodes if requested
            if include_nodes and pillar_levels:
                # Get all pillar level IDs
                pillar_level_ids = [pl.id for pl in pillar_levels]
                
                # Query for associated knowledge nodes
                nodes_query = db.session.query(KnowledgeNode).filter(
                    KnowledgeNode.pillar_level_id.in_(pillar_level_ids)
                )
                
                nodes = nodes_query.all()
                result_data["knowledge_nodes"] = [node.to_dict() for node in nodes]
                result_data["node_count"] = len(nodes)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error navigating Knowledge axis: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }
    
    def get_pillar_level(self, pillar_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific pillar level by its ID.
        
        Parameters:
        - pillar_id (str): The pillar level ID (e.g., "PL01")
        
        Returns:
        - Optional[Dict]: The pillar level data or None if not found
        """
        try:
            pillar_level = db.session.query(PillarLevel).filter(
                PillarLevel.pillar_id == pillar_id
            ).first()
            
            if pillar_level:
                return pillar_level.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving pillar level {pillar_id}: {str(e)}")
            return None
    
    def create_pillar_level(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new pillar level.
        
        Parameters:
        - data (Dict): Data for the new pillar level
        
        Returns:
        - Dict: Result of the creation operation
        """
        try:
            # Check for required fields
            required_fields = ['pillar_id', 'name']
            for field in required_fields:
                if field not in data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Check if pillar ID already exists
            existing = db.session.query(PillarLevel).filter(
                PillarLevel.pillar_id == data['pillar_id']
            ).first()
            
            if existing:
                return {
                    "success": False,
                    "error": f"Pillar ID {data['pillar_id']} already exists"
                }
            
            # Create new pillar level
            pillar_level = PillarLevel(
                uid=str(uuid.uuid4()),
                pillar_id=data['pillar_id'],
                name=data['name'],
                description=data.get('description'),
                sublevels=data.get('sublevels')
            )
            
            db.session.add(pillar_level)
            db.session.commit()
            
            return {
                "success": True,
                "pillar_level": pillar_level.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating pillar level: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_pillar_level(self, pillar_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing pillar level.
        
        Parameters:
        - pillar_id (str): ID of the pillar level to update
        - data (Dict): Updated data
        
        Returns:
        - Dict: Result of the update operation
        """
        try:
            # Find the pillar level
            pillar_level = db.session.query(PillarLevel).filter(
                PillarLevel.pillar_id == pillar_id
            ).first()
            
            if not pillar_level:
                return {
                    "success": False,
                    "error": f"Pillar level with ID {pillar_id} not found"
                }
            
            # Update fields
            if 'name' in data:
                pillar_level.name = data['name']
            
            if 'description' in data:
                pillar_level.description = data['description']
            
            if 'sublevels' in data:
                pillar_level.sublevels = data['sublevels']
            
            # Save changes
            db.session.commit()
            
            return {
                "success": True,
                "pillar_level": pillar_level.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating pillar level {pillar_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_knowledge_node(self, node_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a knowledge node by its ID.
        
        Parameters:
        - node_id (int): The node ID
        
        Returns:
        - Optional[Dict]: The node data or None if not found
        """
        try:
            node = db.session.query(KnowledgeNode).get(node_id)
            
            if node:
                return node.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge node {node_id}: {str(e)}")
            return None
    
    def create_knowledge_node(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new knowledge node.
        
        Parameters:
        - data (Dict): Data for the new knowledge node
        
        Returns:
        - Dict: Result of the creation operation
        """
        try:
            # Check for required fields
            required_fields = ['title', 'content', 'content_type']
            for field in required_fields:
                if field not in data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Create new knowledge node
            node = KnowledgeNode(
                uid=str(uuid.uuid4()),
                title=data['title'],
                content=data['content'],
                content_type=data['content_type'],
                pillar_level_id=data.get('pillar_level_id'),
                domain_id=data.get('domain_id'),
                location_id=data.get('location_id'),
                meta_info=data.get('meta_info')
            )
            
            db.session.add(node)
            db.session.commit()
            
            return {
                "success": True,
                "knowledge_node": node.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating knowledge node: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_knowledge_node(self, node_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing knowledge node.
        
        Parameters:
        - node_id (int): ID of the node to update
        - data (Dict): Updated data
        
        Returns:
        - Dict: Result of the update operation
        """
        try:
            # Find the knowledge node
            node = db.session.query(KnowledgeNode).get(node_id)
            
            if not node:
                return {
                    "success": False,
                    "error": f"Knowledge node with ID {node_id} not found"
                }
            
            # Update fields
            updateable_fields = [
                'title', 'content', 'content_type', 'pillar_level_id',
                'domain_id', 'location_id', 'meta_info'
            ]
            
            for field in updateable_fields:
                if field in data:
                    setattr(node, field, data[field])
            
            # Save changes
            db.session.commit()
            
            return {
                "success": True,
                "knowledge_node": node.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating knowledge node {node_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pillar_structure(self) -> Dict[str, Any]:
        """
        Get the complete pillar level structure.
        
        Returns:
        - Dict: The hierarchical pillar level structure
        """
        try:
            # Get all pillar levels
            pillar_levels = db.session.query(PillarLevel).order_by(
                func.cast(func.substr(PillarLevel.pillar_id, 3), db.Integer)
            ).all()
            
            # Organize into a hierarchical structure
            structure = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "pillar_levels": [pl.to_dict() for pl in pillar_levels],
                "count": len(pillar_levels)
            }
            
            return structure
            
        except Exception as e:
            logger.error(f"Error retrieving pillar structure: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }