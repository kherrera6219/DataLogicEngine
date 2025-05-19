import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

class LocationContextEngine:
    """
    The LocationContextEngine manages location-specific context for the UKG system.
    It determines the active location context for a query and provides access to
    location-specific information, such as applicable regulations.
    
    This component works with Axis 12 (Location) of the UKG.
    """
    
    def __init__(self, config, graph_manager, united_system_manager):
        """
        Initialize the LocationContextEngine.
        
        Args:
            config (dict): Configuration dictionary
            graph_manager (GraphManager): Reference to the GraphManager
            united_system_manager (UnitedSystemManager): Reference to the UnitedSystemManager
        """
        self.config = config
        self.gm = graph_manager
        self.usm = united_system_manager
        
        # Get configuration for location context
        orchestration_config = self.config.get('orchestration_config', {})
        self.location_config = orchestration_config.get('location_awareness', {})
        self.location_enabled = self.location_config.get('enabled', True)
        self.default_location = self.location_config.get('default_location', 'LOC_COUNTRY_USA')
        
        logging.info(f"[{datetime.now()}] LocationContextEngine initialized")
    
    def determine_active_location_context(self, query_text: Optional[str] = None, 
                                        explicit_location_uids: List[str] = None,
                                        user_profile_location_uid: Optional[str] = None) -> List[str]:
        """
        Determines the active location context UIDs for the current simulation.
        
        Priority: Explicit UIDs > Query Text > User Profile > Default.
        
        Args:
            query_text (str, optional): The query text to extract locations from
            explicit_location_uids (list, optional): Explicitly provided location UIDs
            user_profile_location_uid (str, optional): Location UID from user profile
            
        Returns:
            list: List of relevant location UIDs (e.g., [City_UID, State_UID, Country_UID])
        """
        if not self.location_enabled:
            logging.info(f"[{datetime.now()}] LCE: Location context is disabled")
            return []
        
        active_loc_uids = []
        
        # Priority 1: Explicit UIDs
        if explicit_location_uids:
            for uid in explicit_location_uids:
                if self.gm.graph.has_node(uid) and self.gm.get_node_data_by_uid(uid).get("type") in [
                    "Country", "State", "City", "Region", "MilitaryInstallation", "SupranationalRegion"
                ]:
                    active_loc_uids.append(uid)
            
            if active_loc_uids:
                logging.info(f"[{datetime.now()}] LCE: Using explicit location UIDs: {[uid[:10] + '...' for uid in active_loc_uids]}")
                return self._expand_location_hierarchy(active_loc_uids)
        
        # Priority 2: Extract from query text
        if query_text:
            # Use the GraphManager's method to find location UIDs from text
            extracted_loc_uids = self.gm.find_location_uids_from_text(query_text)
            
            if extracted_loc_uids:
                loc_labels = []
                for uid in extracted_loc_uids:
                    node_data = self.gm.get_node_data_by_uid(uid)
                    if node_data:
                        loc_labels.append(node_data.get('label', uid[:10] + '...'))
                
                logging.info(f"[{datetime.now()}] LCE: Location context from query text: {loc_labels}")
                return self._expand_location_hierarchy(extracted_loc_uids)
        
        # Priority 3: User profile location
        if user_profile_location_uid and self.gm.graph.has_node(user_profile_location_uid):
            logging.info(f"[{datetime.now()}] LCE: Using user profile location UID: {user_profile_location_uid[:10] + '...'}")
            return self._expand_location_hierarchy([user_profile_location_uid])
        
        # Priority 4: Default location
        default_loc_uid = None
        
        # Try to get the default location by original ID
        for node, attrs in self.gm.graph.nodes(data=True):
            if attrs.get('original_id') == self.default_location:
                default_loc_uid = node
                break
        
        if default_loc_uid:
            loc_label = self.gm.get_node_data_by_uid(default_loc_uid).get('label', self.default_location)
            logging.info(f"[{datetime.now()}] LCE: Using default location context: {loc_label}")
            return self._expand_location_hierarchy([default_loc_uid])
        
        logging.info(f"[{datetime.now()}] LCE: No specific location context determined")
        return []
    
    def _expand_location_hierarchy(self, leaf_location_uids: List[str]) -> List[str]:
        """
        Given leaf location UIDs, traces up to get their parent location UIDs.
        
        Args:
            leaf_location_uids (list): List of leaf location UIDs
            
        Returns:
            list: Expanded list including parent locations
        """
        full_hierarchy_uids = set(leaf_location_uids)
        
        for leaf_uid in leaf_location_uids:
            curr_uid = leaf_uid
            depth = 0  # Safety break
            
            while curr_uid and depth < 5:  # Max 5 levels up
                # Find parent location (node linked by "contains_sub_location" incoming edge)
                parent_found = False
                
                for source_uid, _, edge_data in self.gm.graph.in_edges(curr_uid, data=True):
                    if edge_data.get("relationship") == "contains_sub_location":
                        full_hierarchy_uids.add(source_uid)
                        curr_uid = source_uid
                        parent_found = True
                        break  # Assume only one primary parent of this type for hierarchy
                
                if not parent_found:
                    break  # No more parents in this relationship type
                
                depth += 1
        
        return list(full_hierarchy_uids)
    
    def get_applicable_regulations_for_locations(self, location_uids: List[str]) -> List[str]:
        """
        Given a list of active location UIDs (e.g., City, State, Country),
        finds all RegulatoryFramework UIDs linked to them.
        
        Args:
            location_uids (list): List of location UIDs
            
        Returns:
            list: List of applicable regulatory framework UIDs
        """
        applicable_reg_uids = set()
        
        for loc_uid in location_uids:
            loc_data = self.gm.get_node_data_by_uid(loc_uid)
            
            if loc_data and "linked_regulatory_framework_uids" in loc_data:
                for reg_uid in loc_data["linked_regulatory_framework_uids"]:
                    applicable_reg_uids.add(reg_uid)
            
            # Also check for outgoing edges to regulatory frameworks
            if self.gm.graph.has_node(loc_uid):
                for _, target_uid, edge_data in self.gm.graph.out_edges(loc_uid, data=True):
                    if edge_data.get("relationship") == "subject_to_regulation":
                        applicable_reg_uids.add(target_uid)
        
        return list(applicable_reg_uids)
    
    def get_location_info(self, location_uid: str) -> Dict[str, Any]:
        """
        Get detailed information about a location.
        
        Args:
            location_uid (str): The location UID
            
        Returns:
            dict: Location information
        """
        loc_data = self.gm.get_node_data_by_uid(location_uid)
        
        if not loc_data:
            return {}
        
        # Extract relevant information
        location_info = {
            'uid': location_uid,
            'label': loc_data.get('label', 'Unknown Location'),
            'type': loc_data.get('type', 'Location'),
            'iso_code': loc_data.get('iso_code'),
            'latitude': loc_data.get('latitude'),
            'longitude': loc_data.get('longitude')
        }
        
        # Add parent information if available
        parent_locations = []
        
        for source_uid, _, edge_data in self.gm.graph.in_edges(location_uid, data=True):
            if edge_data.get("relationship") == "contains_sub_location":
                parent_data = self.gm.get_node_data_by_uid(source_uid)
                if parent_data:
                    parent_locations.append({
                        'uid': source_uid,
                        'label': parent_data.get('label', 'Unknown Parent'),
                        'type': parent_data.get('type', 'Location')
                    })
        
        if parent_locations:
            location_info['parent_locations'] = parent_locations
        
        # Add applicable regulations
        applicable_reg_uids = self.get_applicable_regulations_for_locations([location_uid])
        
        if applicable_reg_uids:
            regulations = []
            
            for reg_uid in applicable_reg_uids:
                reg_data = self.gm.get_node_data_by_uid(reg_uid)
                if reg_data:
                    regulations.append({
                        'uid': reg_uid,
                        'label': reg_data.get('label', 'Unknown Regulation'),
                        'jurisdiction': reg_data.get('jurisdiction', 'Unknown')
                    })
            
            if regulations:
                location_info['applicable_regulations'] = regulations
        
        return location_info
