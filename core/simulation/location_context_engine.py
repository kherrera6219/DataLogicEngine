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

class LocationContextEngine:
    """
    Location Context Engine
    
    This component manages location-based knowledge context in the UKG system.
    It provides functionality to associate knowledge with geographic locations,
    apply location-specific rules, and filter knowledge based on location context.
    """
    
    def __init__(self, config=None, graph_manager=None, united_system_manager=None):
        """
        Initialize the Location Context Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            graph_manager: Graph Manager instance
            united_system_manager: United System Manager instance
        """
        logging.info(f"[{datetime.now()}] Initializing LocationContextEngine...")
        self.config = config or {}
        self.graph_manager = graph_manager
        self.usm = united_system_manager
        
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