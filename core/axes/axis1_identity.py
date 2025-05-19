"""
UKG Axis 1: Identity

This module implements the Identity axis of the Universal Knowledge Graph (UKG) system.
The Identity axis handles entity recognition, identity establishment, and entity relationship
management within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

class IdentityManager:
    """
    Identity Manager for the UKG System
    
    Responsible for managing Axis 1 (Identity) functionality, including:
    - Entity recognition and extraction
    - Identity establishment and verification
    - Entity disambiguation
    - Entity relationship management
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Identity Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
    
    def extract_entities(self, text: str, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Extract entities from text.
        
        Args:
            text: Text to analyze
            confidence_threshold: Confidence threshold for extraction
            
        Returns:
            Dict containing extracted entities
        """
        self.logging.info(f"[{datetime.now()}] Extracting entities from text")
        
        try:
            # This is a simplified implementation
            # In a real system, this would use NLP techniques
            
            # Basic entity patterns
            entity_patterns = {
                'person': [
                    r'(?:Dr\.|Mr\.|Mrs\.|Ms\.|Prof\.)?\s?[A-Z][a-z]+ [A-Z][a-z]+',
                    r'[A-Z][a-z]+ [A-Z][a-z]+'
                ],
                'organization': [
                    r'(?:the\s)?([A-Z][a-z]* (?:Company|Corporation|Inc\.|Ltd\.|LLC|Group|Organization))',
                    r'(?:the\s)?([A-Z][A-Z0-9]+)'
                ],
                'location': [
                    r'(?:in|at|from|to)\s([A-Z][a-z]+ (?:City|Town))',
                    r'(?:in|at|from|to)\s([A-Z][a-z]+, [A-Z]{2})'
                ],
                'date': [
                    r'\d{1,2}/\d{1,2}/\d{2,4}',
                    r'\d{1,2}-\d{1,2}-\d{2,4}',
                    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(?:st|nd|rd|th)?,? \d{2,4}'
                ],
                'concept': [
                    r'(?:the concept of |the idea of |the principle of )([a-z]+(?:\s[a-z]+){0,2})',
                    r'(?:"|\')([A-Za-z]+(?:\s[A-Za-z]+){0,3})(?:"|\')'
                ]
            }
            
            import re
            entities = []
            
            # Apply each pattern
            for entity_type, patterns in entity_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[0]  # Take first group if there are multiple
                            
                        # Skip if already extracted
                        if any(e['text'] == match and e['type'] == entity_type for e in entities):
                            continue
                            
                        entities.append({
                            'type': entity_type,
                            'text': match,
                            'confidence': 0.8,  # Fixed value for demonstration
                            'context': text[max(0, text.find(match) - 30):min(len(text), text.find(match) + len(match) + 30)]
                        })
            
            # Filter by confidence threshold
            entities = [e for e in entities if e['confidence'] >= confidence_threshold]
            
            return {
                'status': 'success',
                'entities': entities,
                'entity_count': len(entities),
                'confidence_threshold': confidence_threshold,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error extracting entities: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error extracting entities: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def identify_entity(self, entity_text: str, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Identify and disambiguate an entity.
        
        Args:
            entity_text: Entity text
            entity_type: Optional entity type hint
            
        Returns:
            Dict containing identified entity
        """
        self.logging.info(f"[{datetime.now()}] Identifying entity: {entity_text}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Search for matching entities in the database
            query_params = {'label': entity_text}
            if entity_type:
                query_params['node_type'] = entity_type
                
            # Find matching nodes
            matching_nodes = self.db_manager.get_nodes_by_properties(query_params)
            
            if not matching_nodes:
                return {
                    'status': 'not_found',
                    'entity_text': entity_text,
                    'entity_type': entity_type,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Return the best match
            return {
                'status': 'success',
                'entity': matching_nodes[0],
                'alternatives': matching_nodes[1:],
                'match_count': len(matching_nodes),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error identifying entity: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error identifying entity: {str(e)}",
                'entity_text': entity_text,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity in the system.
        
        Args:
            entity_data: Entity data
            
        Returns:
            Dict containing created entity
        """
        self.logging.info(f"[{datetime.now()}] Creating entity: {entity_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure entity has required fields
            required_fields = ['label', 'node_type']
            for field in required_fields:
                if field not in entity_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Generate UID if not provided
            if 'uid' not in entity_data:
                entity_data['uid'] = f"entity_{uuid.uuid4()}"
            
            # Set axis number for Identity axis
            entity_data['axis_number'] = 1
            
            # Add entity to database
            new_entity = self.db_manager.add_node(entity_data)
            
            return {
                'status': 'success',
                'entity': new_entity,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating entity: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating entity: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def link_entities(self, source_uid: str, target_uid: str, 
                     relation_type: str, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a relationship between two entities.
        
        Args:
            source_uid: Source entity UID
            target_uid: Target entity UID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing created relationship
        """
        self.logging.info(f"[{datetime.now()}] Linking entities: {source_uid} -> {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify entities exist
            source_entity = self.db_manager.get_node(source_uid)
            target_entity = self.db_manager.get_node(target_uid)
            
            if not source_entity or not target_entity:
                return {
                    'status': 'error',
                    'message': 'Source or target entity not found',
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare edge data
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': source_uid,
                'target_id': target_uid,
                'edge_type': relation_type,
                'attributes': attributes or {}
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'source': source_entity,
                'target': target_entity,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking entities: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking entities: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_entity_relationships(self, entity_uid: str, 
                               relation_types: Optional[List[str]] = None,
                               direction: str = 'both') -> Dict[str, Any]:
        """
        Get relationships for an entity.
        
        Args:
            entity_uid: Entity UID
            relation_types: Optional list of relation types to filter by
            direction: Relationship direction ('incoming', 'outgoing', or 'both')
            
        Returns:
            Dict containing entity relationships
        """
        self.logging.info(f"[{datetime.now()}] Getting relationships for entity: {entity_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify entity exists
            entity = self.db_manager.get_node(entity_uid)
            
            if not entity:
                return {
                    'status': 'error',
                    'message': 'Entity not found',
                    'entity_uid': entity_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get relationships
            relationships = []
            
            if direction in ['outgoing', 'both']:
                outgoing = self.db_manager.get_outgoing_edges(entity_uid, edge_types=relation_types)
                for edge in outgoing:
                    relationships.append({
                        'direction': 'outgoing',
                        'edge': edge,
                        'related_entity': self.db_manager.get_node(edge['target_id'])
                    })
            
            if direction in ['incoming', 'both']:
                incoming = self.db_manager.get_incoming_edges(entity_uid, edge_types=relation_types)
                for edge in incoming:
                    relationships.append({
                        'direction': 'incoming',
                        'edge': edge,
                        'related_entity': self.db_manager.get_node(edge['source_id'])
                    })
            
            return {
                'status': 'success',
                'entity': entity,
                'relationships': relationships,
                'relationship_count': len(relationships),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting entity relationships: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting entity relationships: {str(e)}",
                'entity_uid': entity_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def merge_entities(self, primary_uid: str, secondary_uid: str) -> Dict[str, Any]:
        """
        Merge two entities to resolve duplication.
        
        Args:
            primary_uid: UID of the primary entity to keep
            secondary_uid: UID of the secondary entity to merge in
            
        Returns:
            Dict containing merge result
        """
        self.logging.info(f"[{datetime.now()}] Merging entities: {secondary_uid} into {primary_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify entities exist
            primary_entity = self.db_manager.get_node(primary_uid)
            secondary_entity = self.db_manager.get_node(secondary_uid)
            
            if not primary_entity or not secondary_entity:
                return {
                    'status': 'error',
                    'message': 'Primary or secondary entity not found',
                    'primary_uid': primary_uid,
                    'secondary_uid': secondary_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get all relationships of the secondary entity
            secondary_relationships = self.get_entity_relationships(secondary_uid)
            
            if secondary_relationships['status'] != 'success':
                return {
                    'status': 'error',
                    'message': 'Error getting secondary entity relationships',
                    'primary_uid': primary_uid,
                    'secondary_uid': secondary_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Transfer all relationships to the primary entity
            for rel in secondary_relationships['relationships']:
                edge = rel['edge']
                
                if rel['direction'] == 'outgoing':
                    # Create new outgoing edge from primary to target
                    self.link_entities(
                        source_uid=primary_uid,
                        target_uid=edge['target_id'],
                        relation_type=edge['edge_type'],
                        attributes=edge.get('attributes', {})
                    )
                else:
                    # Create new incoming edge from source to primary
                    self.link_entities(
                        source_uid=edge['source_id'],
                        target_uid=primary_uid,
                        relation_type=edge['edge_type'],
                        attributes=edge.get('attributes', {})
                    )
            
            # Update primary entity with additional attributes from secondary
            merged_attributes = primary_entity.get('attributes', {}).copy()
            secondary_attributes = secondary_entity.get('attributes', {})
            for key, value in secondary_attributes.items():
                if key not in merged_attributes:
                    merged_attributes[key] = value
            
            # Update primary entity
            primary_entity['attributes'] = merged_attributes
            primary_entity['merged_with'] = secondary_uid
            updated_entity = self.db_manager.update_node(primary_uid, primary_entity)
            
            # Mark secondary entity as merged
            secondary_entity['merged_into'] = primary_uid
            secondary_entity['active'] = False
            self.db_manager.update_node(secondary_uid, secondary_entity)
            
            return {
                'status': 'success',
                'merged_entity': updated_entity,
                'relationships_transferred': len(secondary_relationships['relationships']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error merging entities: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error merging entities: {str(e)}",
                'primary_uid': primary_uid,
                'secondary_uid': secondary_uid,
                'timestamp': datetime.now().isoformat()
            }