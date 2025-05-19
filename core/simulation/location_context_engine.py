import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class LocationContextEngine:
    """
    Location Context Engine
    
    This component implements Axis 12 of the UKG, managing spatial relationship logic.
    It determines the active location context for queries and simulations, helping to
    filter knowledge based on geographic relevance.
    """
    
    def __init__(self, config=None, graph_manager=None, usm=None):
        """
        Initialize the Location Context Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            graph_manager: Graph Manager reference
            usm: United System Manager reference
        """
        logging.info(f"[{datetime.now()}] Initializing LocationContextEngine...")
        self.config = config or {}
        self.graph_manager = graph_manager
        self.usm = usm
        
        # Configure axis12 settings
        self.axis12_config = self.config.get('axis12_location_logic', {})
        self.default_location_uid = self.axis12_config.get('default_location_context_uid', 'LOC_COUNTRY_USA')
        self.use_nlp_extraction = self.axis12_config.get('location_extraction', {}).get('use_nlp', False)
        self.confidence_threshold = self.axis12_config.get('location_extraction', {}).get('confidence_threshold', 0.75)
        
        # Location cache for performance
        self.location_label_to_uid = {}
        self.location_uid_to_info = {}
        self.location_parent_map = {}
        self.regulation_location_map = {}
        
        # Initialize cache if graph manager is available
        if self.graph_manager:
            self._initialize_location_cache()
        
        logging.info(f"[{datetime.now()}] LocationContextEngine initialized with default location: {self.default_location_uid}")
    
    def _initialize_location_cache(self):
        """
        Initialize the location cache from the graph database.
        """
        try:
            if not self.graph_manager:
                logging.warning(f"[{datetime.now()}] LCE: Cannot initialize location cache without graph manager")
                return
            
            # Get all location nodes from the graph
            locations = self.graph_manager.get_nodes_by_type('Location')
            
            # Build caches
            for loc in locations:
                uid = loc.get('uid')
                if not uid:
                    continue
                    
                label = loc.get('label', '')
                self.location_uid_to_info[uid] = loc
                self.location_label_to_uid[label.lower()] = uid
            
            # Build parent-child relationships
            location_edges = self.graph_manager.get_edges_by_type('LOCATED_WITHIN')
            for edge in location_edges:
                child_uid = edge.get('source_uid')
                parent_uid = edge.get('target_uid')
                
                if child_uid and parent_uid:
                    if child_uid not in self.location_parent_map:
                        self.location_parent_map[child_uid] = []
                    self.location_parent_map[child_uid].append(parent_uid)
            
            # Build regulation to location map
            reg_loc_edges = self.graph_manager.get_edges_by_type('APPLIES_TO_LOCATION')
            for edge in reg_loc_edges:
                reg_uid = edge.get('source_uid')
                loc_uid = edge.get('target_uid')
                
                if reg_uid and loc_uid:
                    if reg_uid not in self.regulation_location_map:
                        self.regulation_location_map[reg_uid] = []
                    self.regulation_location_map[reg_uid].append(loc_uid)
            
            logging.info(f"[{datetime.now()}] LCE: Initialized location cache with {len(self.location_uid_to_info)} locations")
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] LCE: Error initializing location cache: {str(e)}")
    
    def determine_active_location_context(self, query_text: Optional[str] = None, 
                                        explicit_location_uids: Optional[List[str]] = None,
                                        user_profile_location_uid: Optional[str] = None) -> List[str]:
        """
        Determine the active location context for a query.
        
        Args:
            query_text: The user's query text
            explicit_location_uids: Explicitly provided location UIDs
            user_profile_location_uid: User's profile location UID
            
        Returns:
            list: List of active location UIDs
        """
        active_locations = []
        
        # Priority 1: Explicit location UIDs
        if explicit_location_uids:
            active_locations = self._validate_location_uids(explicit_location_uids)
            if active_locations:
                logging.info(f"[{datetime.now()}] LCE: Using explicit location UIDs: {active_locations}")
                return self._expand_location_hierarchy(active_locations)
        
        # Priority 2: Extract from query text
        if query_text and self.use_nlp_extraction:
            extracted_locations = self._extract_locations_from_text(query_text)
            if extracted_locations:
                logging.info(f"[{datetime.now()}] LCE: Extracted locations from query: {extracted_locations}")
                return self._expand_location_hierarchy(extracted_locations)
        
        # Priority 3: User profile location
        if user_profile_location_uid:
            valid_uid = self._validate_location_uids([user_profile_location_uid])
            if valid_uid:
                logging.info(f"[{datetime.now()}] LCE: Using user profile location: {valid_uid}")
                return self._expand_location_hierarchy(valid_uid)
        
        # Priority 4: Default location
        logging.info(f"[{datetime.now()}] LCE: Using default location: {self.default_location_uid}")
        return self._expand_location_hierarchy([self.default_location_uid])
    
    def _validate_location_uids(self, location_uids: List[str]) -> List[str]:
        """
        Validate that location UIDs exist in the system.
        
        Args:
            location_uids: List of location UIDs to validate
            
        Returns:
            list: List of valid location UIDs
        """
        valid_uids = []
        
        for uid in location_uids:
            # Check in cache first
            if uid in self.location_uid_to_info:
                valid_uids.append(uid)
                continue
                
            # If not in cache, check in graph database if available
            if self.graph_manager:
                node = self.graph_manager.get_node_by_uid(uid)
                if node and node.get('node_type') == 'Location':
                    valid_uids.append(uid)
                    # Add to cache
                    self.location_uid_to_info[uid] = node
        
        return valid_uids
    
    def _extract_locations_from_text(self, text: str) -> List[str]:
        """
        Extract location references from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            list: List of extracted location UIDs
        """
        # This would use a more sophisticated NLP approach in a full implementation
        # For now, we'll use a simple text matching approach
        
        extracted_uids = []
        
        # Convert text to lowercase for matching
        text_lower = text.lower()
        
        # Check if any location labels appear in the text
        for label, uid in self.location_label_to_uid.items():
            if label in text_lower:
                extracted_uids.append(uid)
        
        return extracted_uids
    
    def _expand_location_hierarchy(self, leaf_location_uids: List[str]) -> List[str]:
        """
        Expand location UIDs to include all ancestors in the hierarchy.
        
        Args:
            leaf_location_uids: List of leaf location UIDs
            
        Returns:
            list: List of all location UIDs in the hierarchy
        """
        all_locations = set(leaf_location_uids)
        
        # For each leaf location, traverse up the hierarchy
        for leaf_uid in leaf_location_uids:
            current_uid = leaf_uid
            
            # Continue until we reach a location with no parent
            while current_uid in self.location_parent_map:
                for parent_uid in self.location_parent_map[current_uid]:
                    all_locations.add(parent_uid)
                    current_uid = parent_uid
        
        return list(all_locations)
    
    def get_applicable_regulations(self, location_uids: List[str]) -> List[str]:
        """
        Get regulations that apply to the given locations.
        
        Args:
            location_uids: List of location UIDs
            
        Returns:
            list: List of applicable regulation UIDs
        """
        applicable_regulation_uids = set()
        
        # For each regulation, check if it applies to any of the locations
        for reg_uid, reg_locations in self.regulation_location_map.items():
            for loc_uid in reg_locations:
                if loc_uid in location_uids:
                    applicable_regulation_uids.add(reg_uid)
                    break
        
        return list(applicable_regulation_uids)
    
    def filter_nodes_by_location(self, nodes: List[Dict], active_location_uids: List[str]) -> List[Dict]:
        """
        Filter nodes based on location relevance.
        
        Args:
            nodes: List of node dictionaries
            active_location_uids: List of active location UIDs
            
        Returns:
            list: Filtered list of nodes
        """
        # If no active locations, return all nodes
        if not active_location_uids:
            return nodes
        
        filtered_nodes = []
        
        for node in nodes:
            # Get node's location attributes
            node_locations = node.get('attributes', {}).get('applicable_locations', [])
            
            # If node has no location constraints, include it
            if not node_locations:
                filtered_nodes.append(node)
                continue
            
            # Check if any of the node's locations overlap with active locations
            for loc_uid in node_locations:
                if loc_uid in active_location_uids:
                    filtered_nodes.append(node)
                    break
        
        return filtered_nodes
    
    def get_location_info(self, location_uid: str) -> Optional[Dict]:
        """
        Get information about a location.
        
        Args:
            location_uid: Location UID
            
        Returns:
            dict: Location information or None if not found
        """
        # Check cache first
        if location_uid in self.location_uid_to_info:
            return self.location_uid_to_info[location_uid]
            
        # If not in cache, check graph database if available
        if self.graph_manager:
            node = self.graph_manager.get_node_by_uid(location_uid)
            if node and node.get('node_type') == 'Location':
                # Add to cache
                self.location_uid_to_info[location_uid] = node
                return node
        
        return None
    
    def get_child_locations(self, parent_uid: str) -> List[Dict]:
        """
        Get child locations for a parent location.
        
        Args:
            parent_uid: Parent location UID
            
        Returns:
            list: List of child location dictionaries
        """
        child_locations = []
        
        # Look through parent map for children
        for child_uid, parents in self.location_parent_map.items():
            if parent_uid in parents:
                location_info = self.get_location_info(child_uid)
                if location_info:
                    child_locations.append(location_info)
        
        return child_locations