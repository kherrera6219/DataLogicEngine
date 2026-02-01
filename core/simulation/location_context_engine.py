"""
Location Context Engine

This module provides functionality for handling location-based context and rules
within the UKG system.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
try:
    from models import Node as UkgNode, Edge as UkgEdge
    from extensions import db as ukg_db
except ImportError:
    UkgNode = None
    UkgEdge = None
    ukg_db = None


class LocationContextEngine:
    """
    Location Context Engine
    
    This component manages location-based knowledge context in the UKG system.
    It provides functionality to associate knowledge with geographic locations,
    apply location-specific rules, and filter knowledge based on location context.
    """
    
    def __init__(self, config=None, graph_manager=None, united_system_manager=None, ukg_db_manager=None):
        """
        Initialize the Location Context Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            graph_manager: Graph Manager instance
            united_system_manager: United System Manager instance
            ukg_db_manager: Database manager for UKG operations (optional)
        """

        logging.info(f"[{datetime.now()}] Initializing LocationContextEngine...")
        self.config = config or {}
        self.graph_manager = graph_manager
        self.usm = united_system_manager
        self.ukg_db = ukg_db_manager

        
        # Configuration
        self.location_config = self.config.get('axis12_location_logic', {})
        self.default_location = self.location_config.get('default_location_context_uid', 'LOC_COUNTRY_USA')
        
        # Extraction settings
        self.extraction_settings = self.location_config.get('location_extraction', {})
        self.use_nlp = self.extraction_settings.get('use_nlp', False)
        self.confidence_threshold = self.extraction_settings.get('confidence_threshold', 0.75)
        
        # Location cache
        self.location_cache = {}
        
        # Stats
        self.stats = {
            'location_extractions': 0,
            'location_resolutions': 0,
            'rule_applications': 0
        }
        
        logging.info(f"[{datetime.now()}] LocationContextEngine initialized")
    
    
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
            for uid in explicit_location_uids:
                location_info = self.get_location_by_id(uid)
                if location_info:
                    active_loc_uids.append(uid)
            
            if active_loc_uids:
                logging.info(f"Using explicit location UIDs: {[uid[:10] for uid in active_loc_uids]}")
                return self._expand_location_hierarchy(active_loc_uids)
        
        # 2. Extract locations from query text
        if query_text:
            extracted = self.extract_location(query_text)
            if extracted:
                active_loc_uids.append(extracted['location_id'])
                logging.info(f"Extracted locations from query: {extracted['name']}")
                return self._expand_location_hierarchy(active_loc_uids)
        
        # 3. Use user profile location if available
        if user_profile_location_uid:
            location_info = self.get_location_by_id(user_profile_location_uid)
            if location_info:
                logging.info(f"Using user profile location: {location_info.get('name')}")
                return self._expand_location_hierarchy([user_profile_location_uid])
        
        # 4. Fall back to default location
        logging.info(f"Using default location: {self.default_location}")
        return self._expand_location_hierarchy([self.default_location])

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
            current_uid = leaf_uid
            visited = set()
            
            while current_uid and current_uid not in visited:
                visited.add(current_uid)
                parent_uid = None
                
                # Check graph manager
                if self.graph_manager:
                    try:
                        edges = self.graph_manager.find_edges_by_properties(
                            target_uid=current_uid,
                            edge_type='contains_sub_location'
                        )
                        if edges:
                            parent_uid = edges[0].get('source_uid')
                    except Exception:
                        pass
                
                # Check SQL DB if no graph or if graph failed
                if not parent_uid and UkgNode and UkgEdge and ukg_db:
                    try:
                        node = UkgNode.query.filter_by(uid=current_uid).first()
                        if node:
                            edge = UkgEdge.query.filter_by(target_id=node.id, edge_type='contains_sub_location').first()
                            if edge:
                                parent_node = UkgNode.query.get(edge.source_id)
                                if parent_node:
                                    parent_uid = parent_node.uid
                    except Exception:
                        pass
                
                if parent_uid:
                    full_hierarchy_uids.add(parent_uid)
                    current_uid = parent_uid
                else:
                    break
                    
        return list(full_hierarchy_uids)

    def get_applicable_regulations_for_locations(self, location_uids: List[str]) -> List[str]:
        """
        Given a list of active location UIDs, find all regulatory frameworks linked to them.
        """
        applicable_reg_uids = set()
        
        for loc_uid in location_uids:
            location_info = self.get_location_by_id(loc_uid)
            if not location_info:
                continue
                
            # Attributes can be in dict format or SQLAlchemy attributes
            attrs = location_info.get('attributes', {})
            if 'linked_regulatory_framework_uids' in attrs:
                reg_orig_ids = attrs['linked_regulatory_framework_uids']
                for reg_orig_id in reg_orig_ids:
                    # In a real system, we'd resolve original_id to UID
                    # For now, we'll assume the UID is what's stored or do a lookup
                    applicable_reg_uids.add(reg_orig_id)
        
        return list(applicable_reg_uids)

    def filter_nodes_by_location_context(self, nodes: List[Dict], active_location_uids: List[str]) -> List[Dict]:
        """
        Filter a list of nodes based on location context relevance.
        """
        if not active_location_uids:
            return nodes
            
        filtered_nodes = []
        for node_data in nodes:
            attrs = node_data.get('attributes', {})
            applicable_locs = attrs.get('applicable_locations', [])
            
            if not applicable_locs or any(loc_uid in applicable_locs for loc_uid in active_location_uids):
                filtered_nodes.append(node_data)
                
        return filtered_nodes

    def extract_location(self, text: str) -> Optional[Dict]:

        """
        Extract location information from text.
        
        Args:
            text: Input text to process
            
        Returns:
            dict: Extracted location information or None if not found
        """
        if not text:
            return None
        
        # Update stats
        self.stats['location_extractions'] += 1
        
        # If NLP extraction is disabled, use rule-based approach
        if not self.use_nlp:
            return self._rule_based_extraction(text)
        
        # Otherwise, use NLP (if available)
        try:
            if self.usm:
                nlp_engine = self.usm.get_component('nlp_engine')
                if nlp_engine:
                    return nlp_engine.extract_location(text, self.confidence_threshold)
            
            # Fall back to rule-based approach if NLP is not available
            return self._rule_based_extraction(text)
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error in NLP location extraction: {str(e)}")
            return self._rule_based_extraction(text)
    
    def _rule_based_extraction(self, text: str) -> Optional[Dict]:
        """
        Extract location using rule-based approach.
        
        Args:
            text: Input text to process
            
        Returns:
            dict: Extracted location information or None if not found
        """
        # Simple implementation - could be extended with more sophisticated rules
        location_indicators = {
            'usa': 'LOC_COUNTRY_USA',
            'united states': 'LOC_COUNTRY_USA',
            'us': 'LOC_COUNTRY_USA',
            'america': 'LOC_COUNTRY_USA',
            'canada': 'LOC_COUNTRY_CAN',
            'uk': 'LOC_COUNTRY_GBR',
            'united kingdom': 'LOC_COUNTRY_GBR',
            'england': 'LOC_COUNTRY_GBR',
            'australia': 'LOC_COUNTRY_AUS',
            'germany': 'LOC_COUNTRY_DEU',
            'france': 'LOC_COUNTRY_FRA',
            'japan': 'LOC_COUNTRY_JPN',
            'china': 'LOC_COUNTRY_CHN',
            'india': 'LOC_COUNTRY_IND',
            'brazil': 'LOC_COUNTRY_BRA',
            'russian': 'LOC_COUNTRY_RUS',
            'russia': 'LOC_COUNTRY_RUS'
        }
        
        text_lower = text.lower()
        
        # Check for location mentions
        for keyword, location_id in location_indicators.items():
            if keyword in text_lower:
                # Get location information
                location_info = self.get_location_by_id(location_id)
                
                if location_info:
                    return {
                        'location_id': location_id,
                        'name': location_info.get('name', keyword),
                        'confidence': 0.8,  # Rule-based extraction has fixed confidence
                        'type': 'country'
                    }
        
        return None
    
    def get_location_by_id(self, location_id: str) -> Optional[Dict]:
        """
        Get location information by ID.
        
        Args:
            location_id: Location ID
            
        Returns:
            dict: Location information or None if not found
        """
        # Check cache
        if location_id in self.location_cache:
            return self.location_cache[location_id]
        
        # Try to get from graph
        if self.graph_manager:
            try:
                node = self.graph_manager.get_node_by_uid(location_id)
                
                if node and node.get('node_type') == 'location':
                    # Add to cache
                    self.location_cache[location_id] = node
                    
                    # Update stats
                    self.stats['location_resolutions'] += 1
                    
                    return node
            except Exception as e:
                logging.error(f"[{datetime.now()}] Error getting location from graph: {str(e)}")
        
        # Fallback to built-in location data
        fallback_locations = {
            'LOC_COUNTRY_USA': {
                'uid': 'LOC_COUNTRY_USA',
                'name': 'United States',
                'code': 'US',
                'level': 'country',
                'attributes': {
                    'region': 'North America',
                    'regulatory_framework': 'Federal',
                    'official_language': 'English'
                }
            },
            'LOC_COUNTRY_CAN': {
                'uid': 'LOC_COUNTRY_CAN',
                'name': 'Canada',
                'code': 'CA',
                'level': 'country',
                'attributes': {
                    'region': 'North America',
                    'regulatory_framework': 'Federal',
                    'official_languages': ['English', 'French']
                }
            },
            'LOC_COUNTRY_GBR': {
                'uid': 'LOC_COUNTRY_GBR',
                'name': 'United Kingdom',
                'code': 'GB',
                'level': 'country',
                'attributes': {
                    'region': 'Europe',
                    'regulatory_framework': 'Constitutional Monarchy',
                    'official_language': 'English'
                }
            }
        }
        
        if location_id in fallback_locations:
            location = fallback_locations[location_id]
            self.location_cache[location_id] = location
            self.stats['location_resolutions'] += 1
            return location
        
        return None
    
    def get_default_location(self) -> Dict:
        """
        Get the default location information.
        
        Returns:
            dict: Default location information
        """
        location = self.get_location_by_id(self.default_location)
        
        if not location:
            # Basic fallback if default location is not found
            location = {
                'uid': self.default_location,
                'name': 'Default Location',
                'level': 'country'
            }
        
        return location
    
    def get_location_rules(self, location_id: Optional[str] = None) -> List[Dict]:
        """
        Get rules associated with a location.
        
        Args:
            location_id: Location ID (uses default if None)
            
        Returns:
            list: List of rule dictionaries
        """
        # Use default location if none provided
        if not location_id:
            location_id = self.default_location
        
        # Try to get from graph
        if self.graph_manager:
            try:
                # Find nodes connected to the location with 'has_rule' edges
                edges = self.graph_manager.find_edges_by_properties(
                    source_uid=location_id,
                    edge_type='has_rule'
                )
                
                if edges:
                    rules = []
                    for edge in edges:
                        rule_id = edge.get('target_uid')
                        if rule_id:
                            rule_node = self.graph_manager.get_node_by_uid(rule_id)
                            if rule_node and rule_node.get('node_type') == 'rule':
                                rules.append(rule_node)
                    
                    return rules
            except Exception as e:
                logging.error(f"[{datetime.now()}] Error getting location rules from graph: {str(e)}")
        
        # Fallback to built-in rules for some locations
        fallback_rules = {
            'LOC_COUNTRY_USA': [
                {
                    'uid': 'RULE_USA_01',
                    'name': 'US Data Privacy Rule',
                    'description': 'Apply US-specific data privacy considerations',
                    'rule_type': 'data_privacy',
                    'priority': 1
                },
                {
                    'uid': 'RULE_USA_02',
                    'name': 'US Regulatory Compliance',
                    'description': 'Apply US regulatory standards',
                    'rule_type': 'regulatory',
                    'priority': 2
                }
            ],
            'LOC_COUNTRY_GBR': [
                {
                    'uid': 'RULE_GBR_01',
                    'name': 'UK Data Protection Rule',
                    'description': 'Apply UK/EU data protection regulations',
                    'rule_type': 'data_privacy',
                    'priority': 1
                }
            ]
        }
        
        if location_id in fallback_rules:
            return fallback_rules[location_id]
        
        # Return empty list if no rules found
        return []
    
    def apply_location_context(self, content: Dict, location_id: Optional[str] = None) -> Dict:
        """
        Apply location-specific context to content.
        
        Args:
            content: Content to process
            location_id: Location ID (uses default if None)
            
        Returns:
            dict: Content with location context applied
        """
        # Use default location if none provided
        if not location_id:
            location_id = self.default_location
        
        # Get location information
        location = self.get_location_by_id(location_id)
        if not location:
            location = self.get_default_location()
        
        # Get location rules
        rules = self.get_location_rules(location_id)
        
        # Apply location context
        result = content.copy()
        
        # Add location metadata
        result['_location_context'] = {
            'location_id': location_id,
            'name': location.get('name'),
            'level': location.get('level'),
            'applied_at': datetime.now().isoformat()
        }
        
        # Apply rules
        if rules:
            # Sort rules by priority (lower values = higher priority)
            sorted_rules = sorted(rules, key=lambda r: r.get('priority', 999))
            
            for rule in sorted_rules:
                result = self._apply_rule(result, rule)
                self.stats['rule_applications'] += 1
        
        return result
    
    def _apply_rule(self, content: Dict, rule: Dict) -> Dict:
        """
        Apply a specific rule to content.
        
        Args:
            content: Content to process
            rule: Rule to apply
            
        Returns:
            dict: Content with rule applied
        """
        rule_type = rule.get('rule_type')
        result = content.copy()
        
        # Apply rule based on type
        if rule_type == 'data_privacy':
            # Apply data privacy rule
            if 'personal_data' in result:
                result['personal_data_note'] = f"Personal data subject to {rule.get('name')}"
        
        elif rule_type == 'regulatory':
            # Apply regulatory rule
            result['regulatory_note'] = f"Content subject to {rule.get('name')}"
            result['regulatory_jurisdiction'] = rule.get('location_id')
        
        # Record the applied rule
        if '_applied_rules' not in result:
            result['_applied_rules'] = []
        
        result['_applied_rules'].append({
            'rule_id': rule.get('uid'),
            'name': rule.get('name'),
            'applied_at': datetime.now().isoformat()
        })
        
        return result