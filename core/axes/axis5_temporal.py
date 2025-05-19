"""
UKG Axis 5: Temporal

This module implements the Temporal axis of the Universal Knowledge Graph (UKG) system.
The Temporal axis manages time-based entities, temporal relationships, and 
time-sensitive knowledge within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

class TemporalManager:
    """
    Temporal Manager for the UKG System
    
    Responsible for managing Axis 5 (Temporal) functionality, including:
    - Temporal entity creation and management
    - Time-bound relationships between entities
    - Temporal evolution of knowledge
    - Temporal reasoning and inference
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Temporal Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Temporal relationship types
        self.temporal_relation_types = {
            "before": "A occurs before B",
            "after": "A occurs after B",
            "during": "A occurs during B",
            "contains": "A contains B temporally",
            "overlaps": "A and B overlap temporally",
            "meets": "A ends when B begins",
            "starts": "A and B start at the same time, but A ends before B",
            "finishes": "A and B end at the same time, but A starts after B",
            "equals": "A and B occur at the same time"
        }
    
    def create_temporal_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new temporal entity in the system.
        
        Args:
            entity_data: Entity data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating temporal entity: {entity_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure entity has required fields
            required_fields = ['label', 'start_time']
            for field in required_fields:
                if field not in entity_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Validate temporal information
            start_time = entity_data['start_time']
            end_time = entity_data.get('end_time')
            
            # Normalize temporal data to ISO format strings
            if isinstance(start_time, datetime):
                entity_data['start_time'] = start_time.isoformat()
            
            if end_time and isinstance(end_time, datetime):
                entity_data['end_time'] = end_time.isoformat()
            
            # Generate UID if not provided
            if 'uid' not in entity_data:
                label_snippet = entity_data['label'].lower().replace(' ', '_')[:15]
                entity_data['uid'] = f"temporal_{label_snippet}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Temporal axis
            entity_data['axis_number'] = 5
            entity_data['node_type'] = 'temporal_entity'
            
            # Calculate duration if not provided and end_time exists
            if 'duration' not in entity_data and end_time:
                try:
                    if isinstance(start_time, str):
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    else:
                        start_dt = start_time
                        
                    if isinstance(end_time, str):
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    else:
                        end_dt = end_time
                        
                    duration = end_dt - start_dt
                    entity_data['duration'] = duration.total_seconds()
                except (ValueError, TypeError) as e:
                    self.logging.warning(f"Could not calculate duration: {str(e)}")
            
            # Set temporal precision if not provided
            if 'temporal_precision' not in entity_data:
                entity_data['temporal_precision'] = 'exact'  # Options: exact, approximate, unknown
            
            # Add entity to database
            new_entity = self.db_manager.add_node(entity_data)
            
            return {
                'status': 'success',
                'entity': new_entity,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating temporal entity: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating temporal entity: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def create_time_bound_relationship(self, source_uid: str, target_uid: str,
                                     relation_type: str,
                                     start_time: Union[str, datetime], 
                                     end_time: Optional[Union[str, datetime]] = None,
                                     attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a time-bound relationship between entities.
        
        Args:
            source_uid: Source entity UID
            target_uid: Target entity UID
            relation_type: Type of relationship
            start_time: Start time of the relationship
            end_time: Optional end time of the relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing relationship result
        """
        self.logging.info(f"[{datetime.now()}] Creating time-bound relationship: {source_uid} -> {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify entities exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source or not target:
                return {
                    'status': 'error',
                    'message': 'Source or target entity not found',
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Normalize temporal data to ISO format strings
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            
            if end_time and isinstance(end_time, datetime):
                end_time = end_time.isoformat()
            
            # Prepare edge attributes with temporal information
            edge_attributes = attributes or {}
            edge_attributes['time_bound'] = True
            edge_attributes['start_time'] = start_time
            
            if end_time:
                edge_attributes['end_time'] = end_time
            
            # Prepare edge data
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': source_uid,
                'target_id': target_uid,
                'edge_type': relation_type,
                'attributes': edge_attributes
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'source': source,
                'target': target,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating time-bound relationship: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating time-bound relationship: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_temporal_relationship(self, source_uid: str, target_uid: str,
                                   temporal_relation: str,
                                   attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a temporal relationship between temporal entities.
        
        Args:
            source_uid: Source temporal entity UID
            target_uid: Target temporal entity UID
            temporal_relation: Type of temporal relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing relationship result
        """
        self.logging.info(f"[{datetime.now()}] Creating temporal relationship: {source_uid} -> {target_uid} ({temporal_relation})")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify entities exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source or not target:
                return {
                    'status': 'error',
                    'message': 'Source or target entity not found',
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate both are temporal entities
            if source.get('node_type') != 'temporal_entity' or target.get('node_type') != 'temporal_entity':
                return {
                    'status': 'error',
                    'message': 'Both entities must be temporal entities',
                    'source_type': source.get('node_type'),
                    'target_type': target.get('node_type'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate temporal relation
            if temporal_relation not in self.temporal_relation_types:
                return {
                    'status': 'error',
                    'message': f'Invalid temporal relation: {temporal_relation}',
                    'valid_relations': list(self.temporal_relation_types.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if relationship already exists
            existing_edges = self.db_manager.get_edges_between(source_uid, target_uid, [temporal_relation])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Temporal relationship already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create relationship
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': source_uid,
                'target_id': target_uid,
                'edge_type': temporal_relation,
                'attributes': attributes or {}
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            # For certain relationship types, create inverse relationship automatically
            inverse_relations = {
                'before': 'after',
                'after': 'before',
                'during': 'contains',
                'contains': 'during'
            }
            
            if temporal_relation in inverse_relations:
                inverse_relation = inverse_relations[temporal_relation]
                # Check if inverse relation already exists
                existing_inverse = self.db_manager.get_edges_between(target_uid, source_uid, [inverse_relation])
                
                if not existing_inverse:
                    inverse_edge_data = {
                        'uid': f"edge_{uuid.uuid4()}",
                        'source_id': target_uid,
                        'target_id': source_uid,
                        'edge_type': inverse_relation,
                        'attributes': attributes or {}
                    }
                    self.db_manager.add_edge(inverse_edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'source': source,
                'target': target,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating temporal relationship: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating temporal relationship: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def infer_temporal_relations(self, entity_uid: str) -> Dict[str, Any]:
        """
        Infer temporal relations for a temporal entity.
        
        Args:
            entity_uid: Temporal entity UID
            
        Returns:
            Dict containing inferred relations
        """
        self.logging.info(f"[{datetime.now()}] Inferring temporal relations for: {entity_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify entity exists
            entity = self.db_manager.get_node(entity_uid)
            
            if not entity or entity.get('node_type') != 'temporal_entity':
                return {
                    'status': 'error',
                    'message': 'Invalid temporal entity UID',
                    'entity_uid': entity_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get temporal attributes
            entity_start = entity.get('start_time')
            entity_end = entity.get('end_time')
            
            if not entity_start:
                return {
                    'status': 'error',
                    'message': 'Entity has no start time',
                    'entity_uid': entity_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Parse datetime objects
            try:
                if isinstance(entity_start, str):
                    entity_start_dt = datetime.fromisoformat(entity_start.replace('Z', '+00:00'))
                else:
                    entity_start_dt = entity_start
                    
                if entity_end:
                    if isinstance(entity_end, str):
                        entity_end_dt = datetime.fromisoformat(entity_end.replace('Z', '+00:00'))
                    else:
                        entity_end_dt = entity_end
                else:
                    entity_end_dt = None
            except ValueError as e:
                return {
                    'status': 'error',
                    'message': f'Error parsing datetime: {str(e)}',
                    'entity_uid': entity_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get all other temporal entities
            all_temporal_entities = self.db_manager.get_nodes_by_properties({'node_type': 'temporal_entity'})
            
            inferred_relations = []
            
            for other_entity in all_temporal_entities:
                if other_entity['uid'] == entity_uid:
                    continue  # Skip self
                
                other_start = other_entity.get('start_time')
                other_end = other_entity.get('end_time')
                
                if not other_start:
                    continue  # Skip entities with no start time
                
                # Parse datetime objects
                try:
                    if isinstance(other_start, str):
                        other_start_dt = datetime.fromisoformat(other_start.replace('Z', '+00:00'))
                    else:
                        other_start_dt = other_start
                        
                    if other_end:
                        if isinstance(other_end, str):
                            other_end_dt = datetime.fromisoformat(other_end.replace('Z', '+00:00'))
                        else:
                            other_end_dt = other_end
                    else:
                        other_end_dt = None
                except ValueError:
                    continue  # Skip if datetime parsing fails
                
                # Determine temporal relationship
                relation = self._determine_temporal_relation(
                    entity_start_dt, entity_end_dt,
                    other_start_dt, other_end_dt
                )
                
                if relation:
                    # Check if relationship already exists
                    existing_edges = self.db_manager.get_edges_between(entity_uid, other_entity['uid'], [relation])
                    
                    if not existing_edges:
                        # Create relationship
                        edge_data = {
                            'uid': f"edge_{uuid.uuid4()}",
                            'source_id': entity_uid,
                            'target_id': other_entity['uid'],
                            'edge_type': relation,
                            'attributes': {
                                'inferred': True,
                                'inference_timestamp': datetime.now().isoformat()
                            }
                        }
                        
                        new_edge = self.db_manager.add_edge(edge_data)
                        
                        inferred_relations.append({
                            'relation': relation,
                            'target': other_entity,
                            'edge': new_edge
                        })
            
            return {
                'status': 'success',
                'entity': entity,
                'inferred_relations': inferred_relations,
                'relation_count': len(inferred_relations),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error inferring temporal relations: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error inferring temporal relations: {str(e)}",
                'entity_uid': entity_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def _determine_temporal_relation(self, a_start: datetime, a_end: Optional[datetime],
                                    b_start: datetime, b_end: Optional[datetime]) -> Optional[str]:
        """
        Determine the temporal relation between two time periods.
        
        Args:
            a_start: Start time of period A
            a_end: End time of period A (optional)
            b_start: Start time of period B
            b_end: End time of period B (optional)
            
        Returns:
            Temporal relation type or None if indeterminate
        """
        # If either period has no end time, treat as ongoing
        ongoing_a = a_end is None
        ongoing_b = b_end is None
        
        # If both are ongoing, relation depends on start times
        if ongoing_a and ongoing_b:
            if a_start == b_start:
                return 'equals'
            elif a_start < b_start:
                return 'starts'
            else:  # a_start > b_start
                return 'during'
        
        # If only A is ongoing
        if ongoing_a:
            if a_start == b_start:
                return 'starts'
            elif a_start > b_start:
                if a_start < b_end:
                    return 'during'
                elif a_start == b_end:
                    return 'meets'
                else:  # a_start > b_end
                    return 'after'
            else:  # a_start < b_start
                return 'overlaps'
        
        # If only B is ongoing
        if ongoing_b:
            if a_start == b_start:
                return 'started_by'
            elif a_start < b_start:
                if a_end > b_start:
                    return 'overlaps'
                elif a_end == b_start:
                    return 'meets'
                else:  # a_end < b_start
                    return 'before'
            else:  # a_start > b_start
                return 'during'
        
        # Both periods have start and end times
        if a_start == b_start and a_end == b_end:
            return 'equals'
        elif a_start < b_start and a_end > b_end:
            return 'contains'
        elif a_start > b_start and a_end < b_end:
            return 'during'
        elif a_start == b_start and a_end < b_end:
            return 'starts'
        elif a_start > b_start and a_end == b_end:
            return 'finishes'
        elif a_end < b_start:
            return 'before'
        elif a_start > b_end:
            return 'after'
        elif a_end == b_start:
            return 'meets'
        else:
            return 'overlaps'
    
    def get_entities_by_time_range(self, start_time: Union[str, datetime],
                                 end_time: Union[str, datetime],
                                 entity_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get entities that exist within a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            entity_type: Optional entity type filter
            
        Returns:
            Dict containing entities in the time range
        """
        self.logging.info(f"[{datetime.now()}] Getting entities in time range")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Normalize datetime objects to ISO strings
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            
            if isinstance(end_time, datetime):
                end_time = end_time.isoformat()
            
            # Build query parameters
            query_params = {}
            if entity_type:
                query_params['node_type'] = entity_type
            
            # Get all potential entities
            if entity_type == 'temporal_entity' or not entity_type:
                # For temporal entities, use specialized query
                temporal_entities = self.db_manager.get_nodes_by_properties({'node_type': 'temporal_entity'})
            else:
                # For other entities, use general query
                temporal_entities = self.db_manager.get_nodes_by_properties(query_params)
            
            # Filter entities by time range
            entities_in_range = []
            
            for entity in temporal_entities:
                entity_start = entity.get('start_time')
                entity_end = entity.get('end_time')
                
                if not entity_start:
                    continue  # Skip entities with no start time
                
                # Parse datetime objects
                try:
                    if isinstance(entity_start, str):
                        entity_start_dt = datetime.fromisoformat(entity_start.replace('Z', '+00:00'))
                    else:
                        entity_start_dt = entity_start
                        
                    if entity_end:
                        if isinstance(entity_end, str):
                            entity_end_dt = datetime.fromisoformat(entity_end.replace('Z', '+00:00'))
                        else:
                            entity_end_dt = entity_end
                    else:
                        entity_end_dt = None
                        
                    # Parse range datetime objects
                    if isinstance(start_time, str):
                        start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    else:
                        start_time_dt = start_time
                        
                    if isinstance(end_time, str):
                        end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    else:
                        end_time_dt = end_time
                except ValueError:
                    continue  # Skip if datetime parsing fails
                
                # Check if entity exists in time range
                entity_in_range = False
                
                if not entity_end_dt:  # Entity has no end time (ongoing)
                    # Entity starts before the end of the range
                    entity_in_range = entity_start_dt <= end_time_dt
                else:
                    # Entity overlaps with the time range
                    entity_in_range = (
                        (entity_start_dt <= end_time_dt) and
                        (start_time_dt <= entity_end_dt)
                    )
                
                if entity_in_range:
                    entities_in_range.append(entity)
            
            return {
                'status': 'success',
                'entities': entities_in_range,
                'count': len(entities_in_range),
                'time_range': {
                    'start': start_time,
                    'end': end_time
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting entities by time range: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting entities by time range: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_time_bound_relationships(self, entity_uid: str, 
                                   at_time: Optional[Union[str, datetime]] = None) -> Dict[str, Any]:
        """
        Get time-bound relationships for an entity.
        
        Args:
            entity_uid: Entity UID
            at_time: Optional specific time to check
            
        Returns:
            Dict containing time-bound relationships
        """
        self.logging.info(f"[{datetime.now()}] Getting time-bound relationships for: {entity_uid}")
        
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
            
            # Normalize datetime object to ISO string
            if at_time and isinstance(at_time, datetime):
                at_time = at_time.isoformat()
            
            # Parse the specific time if provided
            at_time_dt = None
            if at_time:
                try:
                    if isinstance(at_time, str):
                        at_time_dt = datetime.fromisoformat(at_time.replace('Z', '+00:00'))
                    else:
                        at_time_dt = at_time
                except ValueError as e:
                    return {
                        'status': 'error',
                        'message': f'Error parsing datetime: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Get all edges for the entity
            outgoing_edges = self.db_manager.get_outgoing_edges(entity_uid)
            incoming_edges = self.db_manager.get_incoming_edges(entity_uid)
            
            # Filter time-bound edges
            time_bound_outgoing = []
            time_bound_incoming = []
            
            for edge in outgoing_edges:
                if edge.get('attributes', {}).get('time_bound'):
                    if self._edge_valid_at_time(edge, at_time_dt):
                        target = self.db_manager.get_node(edge['target_id'])
                        time_bound_outgoing.append({
                            'edge': edge,
                            'target': target,
                            'direction': 'outgoing',
                            'relation_type': edge['edge_type']
                        })
            
            for edge in incoming_edges:
                if edge.get('attributes', {}).get('time_bound'):
                    if self._edge_valid_at_time(edge, at_time_dt):
                        source = self.db_manager.get_node(edge['source_id'])
                        time_bound_incoming.append({
                            'edge': edge,
                            'source': source,
                            'direction': 'incoming',
                            'relation_type': edge['edge_type']
                        })
            
            return {
                'status': 'success',
                'entity': entity,
                'outgoing_relationships': time_bound_outgoing,
                'incoming_relationships': time_bound_incoming,
                'outgoing_count': len(time_bound_outgoing),
                'incoming_count': len(time_bound_incoming),
                'at_time': at_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting time-bound relationships: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting time-bound relationships: {str(e)}",
                'entity_uid': entity_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def _edge_valid_at_time(self, edge: Dict[str, Any], at_time: Optional[datetime] = None) -> bool:
        """
        Check if a time-bound edge is valid at a specific time.
        
        Args:
            edge: Edge dictionary
            at_time: Optional specific time to check
            
        Returns:
            True if edge is valid at the specified time, False otherwise
        """
        if not at_time:
            return True  # No time specified, so edge is valid
        
        attributes = edge.get('attributes', {})
        
        if not attributes.get('time_bound'):
            return True  # Not a time-bound edge, so always valid
        
        start_time = attributes.get('start_time')
        end_time = attributes.get('end_time')
        
        if not start_time:
            return True  # No start time, so always valid
        
        try:
            if isinstance(start_time, str):
                start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_time_dt = start_time
                
            if end_time:
                if isinstance(end_time, str):
                    end_time_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                else:
                    end_time_dt = end_time
                
                # Valid if at_time is between start_time and end_time
                return start_time_dt <= at_time <= end_time_dt
            else:
                # No end time, valid if at_time is after start_time
                return start_time_dt <= at_time
        except ValueError:
            return False  # Invalid datetime format