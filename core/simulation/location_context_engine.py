"""
Location Context Engine

This module contains the Location Context Engine component of the UKG system,
responsible for providing location-specific knowledge context (Axis 12).
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

class LocationContextEngine:
    """
    Location Context Engine for the UKG System
    
    This engine provides location-specific context for queries, supporting
    Axis 12 (Location) of the UKG system. It helps in understanding how
    knowledge relates to physical and virtual locations.
    """
    
    def __init__(self, graph_manager=None, db_manager=None):
        """
        Initialize the Location Context Engine.
        
        Args:
            graph_manager: Graph Manager instance
            db_manager: Database Manager instance
        """
        self.graph_manager = graph_manager
        self.db_manager = db_manager
        self.logging = logging.getLogger(__name__)
    
    def get_context_for_location(self, location_uid: str, 
                                 query_text: Optional[str] = None,
                                 context_depth: int = 2) -> Dict[str, Any]:
        """
        Get context information for a specific location.
        
        Args:
            location_uid: UID of the location node
            query_text: Optional query text to tailor the context
            context_depth: Depth of context to retrieve (1-5)
            
        Returns:
            Dict containing location context
        """
        self.logging.info(f"[{datetime.now()}] Getting context for location {location_uid}")
        
        try:
            # Validate context depth
            context_depth = max(1, min(5, context_depth))
            
            # Get location node from graph
            location_node = None
            if self.db_manager:
                location_node = self.db_manager.get_node(location_uid)
            
            if not location_node:
                return {
                    'status': 'error',
                    'message': f'Location node not found: {location_uid}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get connected nodes based on context depth
            connected_nodes = self._get_connected_nodes(location_uid, context_depth)
            
            # Filter and organize nodes based on relevance to query
            organized_context = self._organize_context(connected_nodes, query_text)
            
            # Prepare result
            result = {
                'status': 'success',
                'location_uid': location_uid,
                'location_data': location_node,
                'context': organized_context,
                'context_depth': context_depth,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting location context for {location_uid}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting location context: {str(e)}",
                'location_uid': location_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_nearby_locations(self, location_uid: str, 
                           radius_km: float = 5.0,
                           limit: int = 10) -> Dict[str, Any]:
        """
        Get locations that are physically near the specified location.
        
        Args:
            location_uid: UID of the central location node
            radius_km: Radius in kilometers to search
            limit: Maximum number of locations to return
            
        Returns:
            Dict containing nearby locations
        """
        self.logging.info(f"[{datetime.now()}] Getting nearby locations for {location_uid} within {radius_km}km")
        
        try:
            # Get location node
            location_node = None
            if self.db_manager:
                location_node = self.db_manager.get_node(location_uid)
            
            if not location_node:
                return {
                    'status': 'error',
                    'message': f'Location node not found: {location_uid}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if location has coordinates
            coordinates = self._extract_coordinates(location_node)
            if not coordinates:
                return {
                    'status': 'error',
                    'message': f'Location does not have valid coordinates: {location_uid}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find nearby locations using spatial query
            nearby_locations = self._find_nearby_locations(coordinates, radius_km, limit)
            
            # Prepare result
            result = {
                'status': 'success',
                'location_uid': location_uid,
                'location_data': location_node,
                'radius_km': radius_km,
                'nearby_locations': nearby_locations,
                'count': len(nearby_locations),
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting nearby locations for {location_uid}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting nearby locations: {str(e)}",
                'location_uid': location_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_location_paths(self, source_uid: str, target_uid: str) -> Dict[str, Any]:
        """
        Find paths between two locations in the graph.
        
        Args:
            source_uid: UID of the source location node
            target_uid: UID of the target location node
            
        Returns:
            Dict containing paths between locations
        """
        self.logging.info(f"[{datetime.now()}] Finding paths from {source_uid} to {target_uid}")
        
        try:
            # Get location nodes
            source_node = None
            target_node = None
            if self.db_manager:
                source_node = self.db_manager.get_node(source_uid)
                target_node = self.db_manager.get_node(target_uid)
            
            if not source_node or not target_node:
                return {
                    'status': 'error',
                    'message': 'Source or target location not found',
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find paths between locations
            paths = self._find_paths(source_uid, target_uid)
            
            # Prepare result
            result = {
                'status': 'success',
                'source_uid': source_uid,
                'target_uid': target_uid,
                'paths': paths,
                'path_count': len(paths),
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding paths from {source_uid} to {target_uid}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding location paths: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def detect_location_from_text(self, text: str, 
                                 confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Detect location references in text.
        
        Args:
            text: Text to analyze for location references
            confidence_threshold: Confidence threshold for detections
            
        Returns:
            Dict containing detected locations
        """
        self.logging.info(f"[{datetime.now()}] Detecting locations in text: '{text[:50]}...'")
        
        try:
            # Extract location references from text (simplified implementation)
            detected_locations = self._extract_location_references(text)
            
            # Filter by confidence threshold
            filtered_locations = [
                loc for loc in detected_locations 
                if loc.get('confidence', 0) >= confidence_threshold
            ]
            
            # Look up detected locations in database
            resolved_locations = []
            if self.db_manager:
                for loc in filtered_locations:
                    # Try to find matching location in database
                    name = loc.get('name', '')
                    location_nodes = self.db_manager.get_nodes_by_property('label', name, node_type='location')
                    
                    if location_nodes:
                        loc['resolved'] = True
                        loc['node_uids'] = [node.get('uid') for node in location_nodes]
                    else:
                        loc['resolved'] = False
                        loc['node_uids'] = []
                    
                    resolved_locations.append(loc)
            else:
                resolved_locations = filtered_locations
            
            # Prepare result
            result = {
                'status': 'success',
                'locations': resolved_locations,
                'location_count': len(resolved_locations),
                'confidence_threshold': confidence_threshold,
                'analyzed_text': text[:200] + '...' if len(text) > 200 else text,  # Truncate for readability
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error detecting locations in text: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error detecting locations: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_connected_nodes(self, location_uid: str, depth: int) -> List[Dict[str, Any]]:
        """
        Get nodes connected to a location up to a specified depth.
        
        Args:
            location_uid: UID of the location node
            depth: Maximum connection depth
            
        Returns:
            List of connected nodes
        """
        connected_nodes = []
        
        if self.graph_manager:
            connected_nodes = self.graph_manager.get_connected_nodes(location_uid, max_depth=depth)
        elif self.db_manager:
            # Fallback to database manager if graph manager not available
            connected_nodes = self.db_manager.get_connected_nodes(location_uid, max_depth=depth)
        
        return connected_nodes
    
    def _organize_context(self, nodes: List[Dict[str, Any]], query_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Organize nodes into a structured context based on relevance.
        
        Args:
            nodes: List of connected nodes
            query_text: Optional query to determine relevance
            
        Returns:
            Dict containing organized context
        """
        # Initialize context categories
        context = {
            'physical_attributes': [],
            'cultural_context': [],
            'historical_context': [],
            'functional_context': [],
            'related_entities': [],
            'other': []
        }
        
        # Sort nodes by type and relevance
        for node in nodes:
            node_type = node.get('node_type', '')
            
            if node_type in ['building', 'terrain', 'infrastructure', 'landmark']:
                context['physical_attributes'].append(node)
                
            elif node_type in ['culture', 'language', 'art', 'customs']:
                context['cultural_context'].append(node)
                
            elif node_type in ['history', 'event', 'period', 'era']:
                context['historical_context'].append(node)
                
            elif node_type in ['function', 'purpose', 'service', 'activity']:
                context['functional_context'].append(node)
                
            elif node_type in ['person', 'organization', 'document', 'concept']:
                context['related_entities'].append(node)
                
            else:
                context['other'].append(node)
        
        # If query text provided, sort each category by relevance to query
        if query_text:
            for category in context:
                context[category] = self._sort_by_relevance(context[category], query_text)
        
        return context
    
    def _sort_by_relevance(self, nodes: List[Dict[str, Any]], query_text: str) -> List[Dict[str, Any]]:
        """
        Sort nodes by relevance to the query text.
        
        Args:
            nodes: List of nodes to sort
            query_text: Query text to determine relevance
            
        Returns:
            Sorted list of nodes
        """
        # For a real implementation, this would use NLP techniques
        # For now, use a simple term matching approach
        
        query_terms = query_text.lower().split()
        
        def relevance_score(node):
            # Calculate relevance score based on matching terms
            score = 0
            for term in query_terms:
                node_label = node.get('label', '').lower()
                node_desc = node.get('description', '').lower()
                
                if term in node_label:
                    score += 3  # Higher weight for matches in label
                    
                if term in node_desc:
                    score += 1  # Lower weight for matches in description
                    
            return score
        
        # Sort nodes by relevance score (descending)
        return sorted(nodes, key=relevance_score, reverse=True)
    
    def _extract_coordinates(self, location_node: Dict[str, Any]) -> Tuple[float, float]:
        """
        Extract coordinates from a location node.
        
        Args:
            location_node: Location node data
            
        Returns:
            Tuple of (latitude, longitude) or None if not available
        """
        attributes = location_node.get('attributes', {})
        
        # Check for coordinates in different possible formats
        if 'coordinates' in attributes:
            coords = attributes['coordinates']
            
            if isinstance(coords, dict) and 'latitude' in coords and 'longitude' in coords:
                return (coords['latitude'], coords['longitude'])
                
            elif isinstance(coords, list) and len(coords) >= 2:
                return (coords[0], coords[1])
        
        # Check for separate latitude/longitude fields
        if 'latitude' in attributes and 'longitude' in attributes:
            return (attributes['latitude'], attributes['longitude'])
        
        # No valid coordinates found
        return None
    
    def _find_nearby_locations(self, coordinates: Tuple[float, float], 
                             radius_km: float, limit: int) -> List[Dict[str, Any]]:
        """
        Find locations near the given coordinates.
        
        Args:
            coordinates: (latitude, longitude) tuple
            radius_km: Radius in kilometers
            limit: Maximum number of locations to return
            
        Returns:
            List of nearby location nodes
        """
        lat, lon = coordinates
        nearby_locations = []
        
        if self.db_manager:
            # This is a simplified implementation
            # In a real system, this would use spatial queries
            
            # Get all location nodes
            location_nodes = self.db_manager.get_nodes_by_type('location')
            
            # Calculate distances and filter
            for node in location_nodes:
                node_coords = self._extract_coordinates(node)
                
                if node_coords:
                    distance = self._calculate_distance(lat, lon, node_coords[0], node_coords[1])
                    
                    if distance <= radius_km:
                        node['distance_km'] = distance
                        nearby_locations.append(node)
            
            # Sort by distance and apply limit
            nearby_locations.sort(key=lambda x: x.get('distance_km', float('inf')))
            nearby_locations = nearby_locations[:limit]
        
        return nearby_locations
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Differences
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine formula
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def _find_paths(self, source_uid: str, target_uid: str) -> List[List[Dict[str, Any]]]:
        """
        Find paths between two location nodes.
        
        Args:
            source_uid: UID of source location
            target_uid: UID of target location
            
        Returns:
            List of paths, where each path is a list of nodes
        """
        paths = []
        
        if self.graph_manager:
            # Use graph manager if available
            paths = self.graph_manager.find_paths(source_uid, target_uid, max_paths=5)
            
        elif self.db_manager:
            # Simplified implementation using database manager
            # In a real implementation, this would use a graph traversal algorithm
            
            # For simplicity, just return direct connections
            # This is a placeholder for a more sophisticated path-finding algorithm
            source_node = self.db_manager.get_node(source_uid)
            target_node = self.db_manager.get_node(target_uid)
            
            if source_node and target_node:
                # Check for direct connection
                direct_edges = self.db_manager.get_edges_between(source_uid, target_uid)
                
                if direct_edges:
                    paths.append([source_node, target_node])
        
        return paths
    
    def _extract_location_references(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract location references from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected locations with confidence scores
        """
        # This is a simplified implementation
        # In a real system, this would use NLP/NER techniques
        
        # Example location patterns to detect
        location_patterns = [
            # Cities
            r'(?:in|at|from|to)\s([A-Z][a-z]+ (?:City|Town))',
            r'(?:in|at|from|to)\s([A-Z][a-z]+, [A-Z]{2})',
            
            # Countries
            r'(?:in|at|from|to)\s((?:the )?(?:United States|Canada|Mexico|France|Germany|Italy|Japan|China|India|Brazil|Australia))',
            
            # Buildings/Landmarks
            r'(?:in|at|from|to)\s((?:the )?(?:[A-Z][a-z]+ )+(?:Building|Tower|Center|Centre|Museum|Library|Park|Garden|Square|Plaza|Airport|Station))'
        ]
        
        import re
        locations = []
        
        # Apply each pattern
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            
            for match in matches:
                # Skip duplicates
                if any(loc['name'] == match for loc in locations):
                    continue
                    
                # Add with basic confidence score
                locations.append({
                    'name': match,
                    'confidence': 0.8,  # Fixed confidence for demonstration
                    'text_context': text[max(0, text.find(match) - 30):min(len(text), text.find(match) + len(match) + 30)]
                })
        
        return locations