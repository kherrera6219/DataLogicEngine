"""
Universal Knowledge Graph (UKG) System - Axis 12: Location

This module implements the Location axis for the UKG system,
providing spatial and geographical context for knowledge.
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import and_, or_, func
from app import db
from models import Location, KnowledgeNode

logger = logging.getLogger(__name__)

class LocationAxis:
    """Handler for Axis 12: Location - Spatial and Geographical Context"""
    
    def __init__(self):
        """Initialize the Location axis handler."""
        self.axis_number = 12
        self.axis_name = "Location"
        self.description = "Spatial and geographical context for knowledge elements"
    
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """
        Navigate the Location axis based on provided parameters.
        
        Parameters:
        - location_id (int): ID of a specific location
        - name (str): Name of the location to search for
        - location_type (str): Type of location (e.g., "country", "city", "virtual")
        - coordinates (tuple): Latitude/longitude pair for proximity search
        - radius (float): Radius in kilometers for proximity search
        - parent_id (int): ID of parent location to find children
        - include_nodes (bool): Whether to include associated knowledge nodes
        
        Returns:
        - Dict containing the navigation results
        """
        # Extract parameters
        location_id = kwargs.get('location_id')
        name = kwargs.get('name')
        location_type = kwargs.get('location_type')
        coordinates = kwargs.get('coordinates')
        radius = kwargs.get('radius', 10.0)  # Default 10km radius
        parent_id = kwargs.get('parent_id')
        include_nodes = kwargs.get('include_nodes', False)
        
        # Build query for locations
        query = db.session.query(Location)
        
        # Apply filters based on provided parameters
        if location_id is not None:
            query = query.filter(Location.id == location_id)
        
        if name is not None:
            search_pattern = f"%{name}%"
            query = query.filter(Location.name.ilike(search_pattern))
        
        if location_type is not None:
            query = query.filter(Location.location_type == location_type)
        
        if parent_id is not None:
            query = query.filter(Location.parent_location_id == parent_id)
        
        if coordinates is not None:
            # This would typically use a geographical distance function
            # Simplified version using approximate distance calculation
            lat, lon = coordinates
            # Filtering would be performed here with a proper GIS extension
            
        # Execute query
        try:
            locations = query.all()
            
            # Convert to dictionary format
            result_data = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "locations": [loc.to_dict() for loc in locations],
                "count": len(locations)
            }
            
            # Include associated knowledge nodes if requested
            if include_nodes and locations:
                # Get all location IDs
                location_ids = [loc.id for loc in locations]
                
                # Query for associated knowledge nodes
                nodes_query = db.session.query(KnowledgeNode).filter(
                    KnowledgeNode.location_id.in_(location_ids)
                )
                
                nodes = nodes_query.all()
                result_data["knowledge_nodes"] = [node.to_dict() for node in nodes]
                result_data["node_count"] = len(nodes)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error navigating Location axis: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }
    
    def get_location(self, location_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific location by its ID.
        
        Parameters:
        - location_id (int): The location ID
        
        Returns:
        - Optional[Dict]: The location data or None if not found
        """
        try:
            location = db.session.query(Location).get(location_id)
            
            if location:
                return location.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving location {location_id}: {str(e)}")
            return None
    
    def create_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new location.
        
        Parameters:
        - data (Dict): Data for the new location
        
        Returns:
        - Dict: Result of the creation operation
        """
        try:
            # Check for required fields
            required_fields = ['name', 'location_type']
            for field in required_fields:
                if field not in data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Create new location
            location = Location(
                uid=str(uuid.uuid4()),
                name=data['name'],
                location_type=data['location_type'],
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                parent_location_id=data.get('parent_location_id'),
                attributes=data.get('attributes')
            )
            
            db.session.add(location)
            db.session.commit()
            
            return {
                "success": True,
                "location": location.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating location: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_location(self, location_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing location.
        
        Parameters:
        - location_id (int): ID of the location to update
        - data (Dict): Updated data
        
        Returns:
        - Dict: Result of the update operation
        """
        try:
            # Find the location
            location = db.session.query(Location).get(location_id)
            
            if not location:
                return {
                    "success": False,
                    "error": f"Location with ID {location_id} not found"
                }
            
            # Update fields
            updateable_fields = [
                'name', 'location_type', 'latitude', 'longitude',
                'parent_location_id', 'attributes'
            ]
            
            for field in updateable_fields:
                if field in data:
                    setattr(location, field, data[field])
            
            # Save changes
            db.session.commit()
            
            return {
                "success": True,
                "location": location.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating location {location_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_location_hierarchy(self, root_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get the hierarchical structure of locations.
        
        Parameters:
        - root_id (Optional[int]): ID of the root location, or None for all top-level locations
        
        Returns:
        - Dict: The hierarchical location structure
        """
        try:
            if root_id is not None:
                # Get a specific location and its descendants
                root_location = db.session.query(Location).get(root_id)
                
                if not root_location:
                    return {
                        "success": False,
                        "error": f"Root location with ID {root_id} not found"
                    }
                
                # Build hierarchical structure starting from this root
                hierarchy = self._build_location_hierarchy(root_location)
                
                return {
                    "success": True,
                    "root_id": root_id,
                    "hierarchy": hierarchy
                }
            else:
                # Get all top-level locations (those without parent)
                top_level_locations = db.session.query(Location).filter(
                    Location.parent_location_id == None
                ).all()
                
                # Build hierarchical structure for each top-level location
                hierarchies = [
                    self._build_location_hierarchy(loc)
                    for loc in top_level_locations
                ]
                
                return {
                    "success": True,
                    "root_id": None,
                    "hierarchies": hierarchies
                }
            
        except Exception as e:
            logger.error(f"Error retrieving location hierarchy: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_location_hierarchy(self, location: Location) -> Dict[str, Any]:
        """
        Recursively build the hierarchical structure for a location.
        
        Parameters:
        - location (Location): The location to build hierarchy for
        
        Returns:
        - Dict: The hierarchical structure
        """
        # Convert location to dictionary
        result = location.to_dict()
        
        # Add children if available
        if hasattr(location, 'sub_locations') and location.sub_locations:
            result['children'] = [
                self._build_location_hierarchy(child)
                for child in location.sub_locations
            ]
        else:
            result['children'] = []
        
        return result
    
    def find_nearest_locations(self, latitude: float, longitude: float, 
                              radius: float = 10.0, 
                              limit: int = 10) -> Dict[str, Any]:
        """
        Find locations nearest to specified coordinates.
        
        Parameters:
        - latitude (float): Latitude coordinate
        - longitude (float): Longitude coordinate
        - radius (float): Search radius in kilometers
        - limit (int): Maximum number of results to return
        
        Returns:
        - Dict: The nearest locations with distances
        """
        try:
            # This would typically use a geographical distance function
            # Simplified version using approximate distance calculation
            
            # Get all locations with coordinates
            locations = db.session.query(Location).filter(
                Location.latitude.isnot(None),
                Location.longitude.isnot(None)
            ).all()
            
            # Calculate distances and filter by radius
            result_locations = []
            for location in locations:
                distance = self._calculate_distance(
                    latitude, longitude, 
                    location.latitude, location.longitude
                )
                
                if distance <= radius:
                    location_data = location.to_dict()
                    location_data['distance'] = distance
                    result_locations.append(location_data)
            
            # Sort by distance and limit results
            result_locations.sort(key=lambda x: x['distance'])
            if limit:
                result_locations = result_locations[:limit]
            
            return {
                "success": True,
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius,
                "locations": result_locations,
                "count": len(result_locations)
            }
            
        except Exception as e:
            logger.error(f"Error finding nearest locations: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points in kilometers using the Haversine formula.
        
        Parameters:
        - lat1, lon1: Coordinates of first point
        - lat2, lon2: Coordinates of second point
        
        Returns:
        - float: Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Earth radius in kilometers
        radius = 6371
        
        # Calculate distance
        distance = radius * c
        
        return distance