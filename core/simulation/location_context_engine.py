import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import sys
import os

# Add the parent directory to path to allow imports from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.models import UkgNode, UkgEdge

class LocationContextEngine:
    """
    The LocationContextEngine determines the "active location context" for the UKG system
    and helps other components filter or prioritize information based on geographic context.
    This engine integrates with the database to process location information from Axis 12 of the UKG.
    """
    
    def __init__(self, config, graph_manager, united_system_manager):
        """
        Initialize the LocationContextEngine.
        
        Args:
            config (dict): Configuration dictionary with location-specific settings
            graph_manager: Reference to the GraphManager
            united_system_manager: Reference to the UnitedSystemManager
        """
        self.config = config.get('axis12_location_logic', {})
        self.gm = graph_manager
        self.usm = united_system_manager
        self.default_location_uid = self.config.get('default_location_context_uid', 'LOC_COUNTRY_USA')
        
        logging.info(f"[{datetime.now()}] LocationContextEngine (Axis 12 Logic) initialized")
    
    def determine_active_location_context(self, 
                                         query_text: Optional[str] = None, 
                                         explicit_location_uids: Optional[List[str]] = None,
                                         user_profile_location_uid: Optional[str] = None) -> List[str]:
        """
        Determines the active location context UIDs for the current simulation.
        Priority: Explicit UIDs > Query Text > User Profile > Default.
        
        Args:
            query_text (str, optional): The user's query text to extract locations from
            explicit_location_uids (List[str], optional): Explicitly provided location UIDs
            user_profile_location_uid (str, optional): User's profile location UID
            
        Returns:
            List[str]: A list of relevant location UIDs (e.g., [City_UID, State_UID, Country_UID])
        """
        active_loc_uids = []
        
        # 1. Check explicit location UIDs first (highest priority)
        if explicit_location_uids:
            # Validate explicit locations exist in the graph
            for uid in explicit_location_uids:
                if self.gm.get_node_data_by_uid(uid) and self.gm.get_node_data_by_uid(uid).get("type") in [
                    'Location', 'Country', 'State', 'City', 'Region', 'MilitaryInstallation', 'SupranationalRegion'
                ]:
                    active_loc_uids.append(uid)
            
            if active_loc_uids:
                logging.info(f"[{datetime.now()}] LCE: Using explicit location UIDs: {[uid[:10] for uid in active_loc_uids]}")
                return self._expand_location_hierarchy(active_loc_uids)
        
        # 2. Extract locations from query text
        if query_text:
            # Simple keyword matching for locations in the text
            # In a production system, this would use NLP/NER for location extraction
            locations_from_query = self._extract_locations_from_text(query_text)
            if locations_from_query:
                active_loc_uids.extend(locations_from_query)
                logging.info(f"[{datetime.now()}] LCE: Extracted locations from query: {[self._get_location_label(uid) for uid in locations_from_query]}")
                return self._expand_location_hierarchy(active_loc_uids)
        
        # 3. Use user profile location if available
        if user_profile_location_uid and self.gm.get_node_data_by_uid(user_profile_location_uid):
            node_data = self.gm.get_node_data_by_uid(user_profile_location_uid)
            if node_data and node_data.get("type") in ['Location', 'Country', 'State', 'City', 'Region']:
                logging.info(f"[{datetime.now()}] LCE: Using user profile location: {node_data.get('label')}")
                return self._expand_location_hierarchy([user_profile_location_uid])
        
        # 4. Fall back to default location
        default_loc_uid = self.gm.get_node_data_by_attribute("original_id", self.default_location_uid)
        if default_loc_uid:
            default_node = self.gm.get_node_data_by_uid(default_loc_uid)
            if default_node:
                logging.info(f"[{datetime.now()}] LCE: Using default location: {default_node.get('label')}")
                return self._expand_location_hierarchy([default_loc_uid])
        
        logging.info(f"[{datetime.now()}] LCE: No specific location context determined")
        return []
    
    def _extract_locations_from_text(self, text: str) -> List[str]:
        """
        Extract location references from text.
        
        Args:
            text (str): The text to analyze for location references
            
        Returns:
            List[str]: List of extracted location UIDs
        """
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # This is a simple keyword matching approach
        # In a production system, this would use a more sophisticated NER model
        extracted_uids = []
        
        # Simple keyword matching for locations
        # For demo, we check for a few common location names
        common_locations = {
            "united states": "LOC_COUNTRY_USA",
            "usa": "LOC_COUNTRY_USA",
            "us": "LOC_COUNTRY_USA",
            "america": "LOC_COUNTRY_USA",
            "texas": "LOC_STATE_USA_TX",
            "tx": "LOC_STATE_USA_TX",
            "austin": "LOC_CITY_USA_TX_AUSTIN",
            "california": "LOC_STATE_USA_CA",
            "ca": "LOC_STATE_USA_CA",
            "san francisco": "LOC_CITY_USA_CA_SF",
            "sf": "LOC_CITY_USA_CA_SF",
            "european union": "LOC_REGION_EU",
            "eu": "LOC_REGION_EU",
            "europe": "LOC_REGION_EU",
            "germany": "LOC_COUNTRY_DEU",
            "de": "LOC_COUNTRY_DEU",
            "berlin": "LOC_STATE_DEU_BER",
            "united kingdom": "LOC_COUNTRY_GBR",
            "uk": "LOC_COUNTRY_GBR",
            "england": "LOC_REGION_GBR_ENG",
            "london": "LOC_CITY_GBR_ENG_LON"
        }
        
        for location_name, location_id in common_locations.items():
            if location_name in text_lower:
                # Find the node UID by original_id
                node_uid = self.gm.get_node_data_by_attribute("original_id", location_id)
                if node_uid:
                    extracted_uids.append(node_uid)
        
        return extracted_uids
    
    def _expand_location_hierarchy(self, leaf_location_uids: List[str]) -> List[str]:
        """
        Given leaf location UIDs, traces up to get their parent location UIDs.
        
        Args:
            leaf_location_uids (List[str]): The starting location UIDs
            
        Returns:
            List[str]: Full hierarchy of location UIDs including parents
        """
        full_hierarchy_uids = set(leaf_location_uids)
        
        for leaf_uid in leaf_location_uids:
            curr_uid = leaf_uid
            depth = 0  # Safety limit to prevent infinite loops
            
            while curr_uid and depth < 5:  # Max 5 levels up
                # Find parent locations (connected by "contains_sub_location" edge)
                parent_found = False
                
                for source_uid, _, edge_data in self.gm.graph.in_edges(curr_uid, data=True):
                    if edge_data.get("relationship") == "contains_sub_location":
                        full_hierarchy_uids.add(source_uid)
                        curr_uid = source_uid
                        parent_found = True
                        break
                
                if not parent_found:
                    break
                
                depth += 1
        
        return list(full_hierarchy_uids)
    
    def _get_location_label(self, uid: str) -> str:
        """
        Get the human-readable label for a location UID.
        
        Args:
            uid (str): The location UID
            
        Returns:
            str: The location label or a truncated UID if not found
        """
        node_data = self.gm.get_node_data_by_uid(uid)
        return node_data.get('label', uid[:10]) if node_data else uid[:10]
    
    def get_applicable_regulations_for_locations(self, location_uids: List[str]) -> List[str]:
        """
        Given a list of active location UIDs, find all regulatory frameworks linked to them.
        
        Args:
            location_uids (List[str]): List of location UIDs
            
        Returns:
            List[str]: List of applicable regulatory framework UIDs
        """
        applicable_reg_uids = set()
        
        for loc_uid in location_uids:
            # Get the location node
            loc_data = self.gm.get_node_data_by_uid(loc_uid)
            if not loc_data:
                continue
            
            # Check if the node has linked regulatory frameworks in its attributes
            if "linked_regulatory_framework_uids" in loc_data:
                reg_orig_ids = loc_data["linked_regulatory_framework_uids"]
                
                # Convert original IDs to UIDs in the graph
                for reg_orig_id in reg_orig_ids:
                    reg_uid = self.gm.get_node_data_by_attribute("original_id", reg_orig_id, "RegulatoryFrameworkNode")
                    if reg_uid:
                        applicable_reg_uids.add(reg_uid)
        
        # Log the found regulations
        if applicable_reg_uids:
            reg_labels = []
            for uid in applicable_reg_uids:
                node_data = self.gm.get_node_data_by_uid(uid)
                if node_data:
                    reg_labels.append(node_data.get('label', uid[:10]))
            
            logging.info(f"[{datetime.now()}] LCE: Found {len(applicable_reg_uids)} regulations applicable to locations: {reg_labels}")
        
        return list(applicable_reg_uids)
    
    def filter_nodes_by_location_context(self, nodes_data: List[Dict], active_location_uids: List[str]) -> List[Dict]:
        """
        Filter a list of nodes based on location context relevance.
        
        Args:
            nodes_data (List[Dict]): List of node data dictionaries
            active_location_uids (List[str]): List of active location UIDs
            
        Returns:
            List[Dict]: Filtered list of nodes relevant to the active locations
        """
        if not active_location_uids:
            return nodes_data  # No filtering if no location context
        
        filtered_nodes = []
        
        for node_data in nodes_data:
            # Check if the node has location-specific attributes
            if 'attributes' in node_data and 'applicable_locations' in node_data['attributes']:
                # Check if any of the active locations are in the node's applicable locations
                applicable_locs = node_data['attributes']['applicable_locations']
                if any(loc_uid in applicable_locs for loc_uid in active_location_uids):
                    filtered_nodes.append(node_data)
            else:
                # If no location constraints, include the node
                filtered_nodes.append(node_data)
        
        return filtered_nodes