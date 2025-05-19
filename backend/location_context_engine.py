import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .models import db, UkgNode, UkgEdge
from .ukg_db import UkgDatabaseManager

class LocationContextEngine:
    """
    The LocationContextEngine determines the "active location context" for the UKG system
    and helps other components filter or prioritize information based on geographic context.
    This engine processes location information from Axis 12 of the UKG.
    """
    
    def __init__(self, config: dict, ukg_db_manager=None):
        """
        Initialize the LocationContextEngine.
        
        Args:
            config (dict): Configuration dictionary with location-specific settings
            ukg_db_manager (UkgDatabaseManager): Database manager for UKG operations
        """
        self.config = config.get('axis12_location_logic', {})
        self.ukg_db = ukg_db_manager if ukg_db_manager else UkgDatabaseManager()
        self.default_location_uid = self.config.get('default_location_context_uid', 'LOC_COUNTRY_USA')
        logging.info("LocationContextEngine (Axis 12 Logic) initialized")
    
    def determine_active_location_context(self, 
                                         query_text: Optional[str] = None, 
                                         explicit_location_uids: List[str] = None,
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
            # Validate explicit locations exist in the database
            for uid in explicit_location_uids:
                node = UkgNode.query.filter_by(uid=uid).first()
                if node and node.node_type in ['Location', 'Country', 'State', 'City', 'Region', 'SupranationalRegion']:
                    active_loc_uids.append(uid)
            
            if active_loc_uids:
                logging.info(f"Using explicit location UIDs: {[uid[:10] for uid in active_loc_uids]}")
                return self._expand_location_hierarchy(active_loc_uids)
        
        # 2. Extract locations from query text
        if query_text:
            # Simple keyword matching for locations in the text
            # In a production system, this would use NLP/NER for location extraction
            locations_from_query = self._extract_locations_from_text(query_text)
            if locations_from_query:
                active_loc_uids.extend(locations_from_query)
                logging.info(f"Extracted locations from query: {[self._get_location_label(uid) for uid in locations_from_query]}")
                return self._expand_location_hierarchy(active_loc_uids)
        
        # 3. Use user profile location if available
        if user_profile_location_uid:
            node = UkgNode.query.filter_by(uid=user_profile_location_uid).first()
            if node and node.node_type in ['Location', 'Country', 'State', 'City', 'Region']:
                logging.info(f"Using user profile location: {node.label}")
                return self._expand_location_hierarchy([user_profile_location_uid])
        
        # 4. Fall back to default location
        default_loc = UkgNode.query.filter_by(original_id=self.default_location_uid).first()
        if default_loc:
            logging.info(f"Using default location: {default_loc.label}")
            return self._expand_location_hierarchy([default_loc.uid])
        
        logging.info("No specific location context determined")
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
        
        # Get all location nodes from the database
        location_nodes = UkgNode.query.filter(
            UkgNode.node_type.in_(['Location', 'Country', 'State', 'City', 'Region'])
        ).all()
        
        # Check for location mentions in the text
        for node in location_nodes:
            if node.label.lower() in text_lower:
                extracted_uids.append(node.uid)
                continue
            
            # Also check attributes for alternative names, abbreviations, etc.
            if node.attributes:
                for attr_value in node.attributes.values():
                    if isinstance(attr_value, str) and attr_value.lower() in text_lower:
                        extracted_uids.append(node.uid)
                        break
        
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
            # Find all parent locations by following 'contains_sub_location' edges
            current_uid = leaf_uid
            visited = set()  # Prevent infinite loops
            
            while current_uid and current_uid not in visited:
                visited.add(current_uid)
                
                # Find parent edges (where the current node is the target)
                parent_edges = UkgEdge.query.filter_by(
                    target_id=UkgNode.query.filter_by(uid=current_uid).first().id,
                    edge_type='contains_sub_location'
                ).all()
                
                if not parent_edges:
                    break
                
                # Get the parent node
                for edge in parent_edges:
                    parent_node = UkgNode.query.get(edge.source_id)
                    if parent_node:
                        full_hierarchy_uids.add(parent_node.uid)
                        current_uid = parent_node.uid
                        break
                else:
                    # No valid parent found
                    break
        
        return list(full_hierarchy_uids)
    
    def _get_location_label(self, uid: str) -> str:
        """
        Get the human-readable label for a location UID.
        
        Args:
            uid (str): The location UID
            
        Returns:
            str: The location label or a truncated UID if not found
        """
        node = UkgNode.query.filter_by(uid=uid).first()
        return node.label if node else uid[:10]
    
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
            location_node = UkgNode.query.filter_by(uid=loc_uid).first()
            if not location_node:
                continue
            
            # Check if the node has linked regulatory frameworks in its attributes
            if location_node.attributes and 'linked_regulatory_framework_uids' in location_node.attributes:
                reg_orig_ids = location_node.attributes['linked_regulatory_framework_uids']
                
                # Convert original IDs to UIDs in the graph
                for reg_orig_id in reg_orig_ids:
                    reg_node = UkgNode.query.filter_by(
                        original_id=reg_orig_id,
                        node_type='RegulatoryFrameworkNode'
                    ).first()
                    
                    if reg_node:
                        applicable_reg_uids.add(reg_node.uid)
        
        # Log the found regulations
        if applicable_reg_uids:
            reg_labels = []
            for uid in applicable_reg_uids:
                node = UkgNode.query.filter_by(uid=uid).first()
                if node:
                    reg_labels.append(node.label)
            
            logging.info(f"Found {len(applicable_reg_uids)} regulations applicable to locations: {reg_labels}")
        
        return list(applicable_reg_uids)
    
    def filter_nodes_by_location_context(self, nodes: List[Dict], active_location_uids: List[str]) -> List[Dict]:
        """
        Filter a list of nodes based on location context relevance.
        
        Args:
            nodes (List[Dict]): List of node data dictionaries
            active_location_uids (List[str]): List of active location UIDs
            
        Returns:
            List[Dict]: Filtered list of nodes relevant to the active locations
        """
        if not active_location_uids:
            return nodes  # No filtering if no location context
        
        filtered_nodes = []
        
        for node_data in nodes:
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