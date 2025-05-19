"""
UKG Axis 4: Knowledge

This module implements the Knowledge axis of the Universal Knowledge Graph (UKG) system.
The Knowledge axis manages knowledge artifacts, epistemic attributes, and
knowledge organization within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class KnowledgeManager:
    """
    Knowledge Manager for the UKG System
    
    Responsible for managing Axis 4 (Knowledge) functionality, including:
    - Knowledge artifact creation and management
    - Epistemic attributes (certainty, validity, etc.)
    - Knowledge provenance and sourcing
    - Knowledge versioning and evolution
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Knowledge Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Knowledge artifact types
        self.artifact_types = {
            "assertion": "A statement of fact or belief",
            "definition": "A formal statement of meaning",
            "theory": "A system of ideas explaining something",
            "model": "A representation of a system or process",
            "principle": "A fundamental truth or proposition",
            "formula": "A mathematical or symbolic representation",
            "procedure": "A sequence of actions or operations",
            "heuristic": "A practical method for problem solving",
            "rule": "A prescribed guide for conduct or action",
            "example": "A specific instance illustrating a concept"
        }
        
        # Epistemic attributes
        self.epistemic_attributes = {
            "certainty": "Degree of confidence in truth/validity (0.0-1.0)",
            "validity": "Logical soundness (0.0-1.0)",
            "reliability": "Consistency of results (0.0-1.0)",
            "precision": "Exactness or accuracy (0.0-1.0)",
            "recency": "Temporal relevance (0.0-1.0)",
            "authority": "Credibility of source (0.0-1.0)",
            "consensus": "Degree of agreement among experts (0.0-1.0)",
            "completeness": "Coverage of relevant aspects (0.0-1.0)"
        }
    
    def create_knowledge_artifact(self, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new knowledge artifact in the system.
        
        Args:
            artifact_data: Artifact data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating knowledge artifact: {artifact_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure artifact has required fields
            required_fields = ['label', 'artifact_type', 'content']
            for field in required_fields:
                if field not in artifact_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Validate artifact type
            if artifact_data['artifact_type'] not in self.artifact_types:
                return {
                    'status': 'error',
                    'message': f'Invalid artifact type: {artifact_data["artifact_type"]}',
                    'valid_types': list(self.artifact_types.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in artifact_data:
                artifact_type = artifact_data['artifact_type']
                label_snippet = artifact_data['label'].lower().replace(' ', '_')[:15]
                artifact_data['uid'] = f"artifact_{artifact_type}_{label_snippet}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Knowledge axis
            artifact_data['axis_number'] = 4
            artifact_data['node_type'] = 'knowledge_artifact'
            
            # Initialize epistemic attributes if not provided
            if 'epistemic_attributes' not in artifact_data:
                artifact_data['epistemic_attributes'] = {}
            
            # Validate and normalize all provided epistemic attributes
            for attr, value in artifact_data['epistemic_attributes'].items():
                if attr not in self.epistemic_attributes:
                    return {
                        'status': 'error',
                        'message': f'Invalid epistemic attribute: {attr}',
                        'valid_attributes': list(self.epistemic_attributes.keys()),
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Ensure all values are between 0 and 1
                if not isinstance(value, (int, float)) or value < 0 or value > 1:
                    return {
                        'status': 'error',
                        'message': f'Epistemic attribute {attr} must be a float between 0 and 1',
                        'provided_value': value,
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Set default values for missing epistemic attributes
            for attr in self.epistemic_attributes:
                if attr not in artifact_data['epistemic_attributes']:
                    artifact_data['epistemic_attributes'][attr] = 0.5  # Default neutral value
            
            # Add source information if provided
            if 'source' in artifact_data:
                source_info = artifact_data['source']
                if not isinstance(source_info, dict):
                    return {
                        'status': 'error',
                        'message': 'Source must be a dictionary',
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Ensure source has required fields
                if 'name' not in source_info:
                    return {
                        'status': 'error',
                        'message': 'Source must have a name',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Set creation timestamp if not provided
            if 'created_at' not in artifact_data:
                artifact_data['created_at'] = datetime.now().isoformat()
            
            # Set version if not provided
            if 'version' not in artifact_data:
                artifact_data['version'] = '1.0'
            
            # Add artifact to database
            new_artifact = self.db_manager.add_node(artifact_data)
            
            # If concept_uids provided, link to concepts
            if 'concept_uids' in artifact_data and isinstance(artifact_data['concept_uids'], list):
                for concept_uid in artifact_data['concept_uids']:
                    self.link_to_concept(new_artifact['uid'], concept_uid)
            
            return {
                'status': 'success',
                'artifact': new_artifact,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating knowledge artifact: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating knowledge artifact: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def update_knowledge_artifact(self, artifact_uid: str, 
                              update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing knowledge artifact.
        
        Args:
            artifact_uid: Artifact UID
            update_data: Data to update
            
        Returns:
            Dict containing update result
        """
        self.logging.info(f"[{datetime.now()}] Updating knowledge artifact: {artifact_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify artifact exists
            artifact = self.db_manager.get_node(artifact_uid)
            
            if not artifact or artifact.get('node_type') != 'knowledge_artifact':
                return {
                    'status': 'error',
                    'message': 'Invalid artifact UID',
                    'artifact_uid': artifact_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create a new version if content is being updated
            if 'content' in update_data and update_data['content'] != artifact.get('content'):
                # Create a new version node
                old_version = artifact.copy()
                
                # Calculate new version number
                current_version = artifact.get('version', '1.0')
                try:
                    # Simple version increment (1.0 -> 1.1, etc.)
                    major, minor = current_version.split('.')
                    new_version = f"{major}.{int(minor) + 1}"
                except (ValueError, AttributeError):
                    # Fallback for non-standard versions
                    new_version = f"{current_version}_v2"
                
                # Archive old version
                old_version_uid = f"{artifact_uid}_v{current_version}"
                old_version['uid'] = old_version_uid
                old_version['node_type'] = 'archived_knowledge_artifact'
                old_version['archived_at'] = datetime.now().isoformat()
                
                self.db_manager.add_node(old_version)
                
                # Link new version to old version
                edge_data = {
                    'uid': f"edge_{uuid.uuid4()}",
                    'source_id': artifact_uid,
                    'target_id': old_version_uid,
                    'edge_type': 'previous_version',
                    'attributes': {
                        'from_version': current_version,
                        'to_version': new_version,
                        'change_timestamp': datetime.now().isoformat()
                    }
                }
                
                self.db_manager.add_edge(edge_data)
                
                # Update version in update data
                update_data['version'] = new_version
                update_data['updated_at'] = datetime.now().isoformat()
            
            # Update epistemic attributes if provided
            if 'epistemic_attributes' in update_data:
                current_attributes = artifact.get('epistemic_attributes', {})
                
                for attr, value in update_data['epistemic_attributes'].items():
                    if attr not in self.epistemic_attributes:
                        return {
                            'status': 'error',
                            'message': f'Invalid epistemic attribute: {attr}',
                            'valid_attributes': list(self.epistemic_attributes.keys()),
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    # Ensure all values are between 0 and 1
                    if not isinstance(value, (int, float)) or value < 0 or value > 1:
                        return {
                            'status': 'error',
                            'message': f'Epistemic attribute {attr} must be a float between 0 and 1',
                            'provided_value': value,
                            'timestamp': datetime.now().isoformat()
                        }
                
                # Merge with existing attributes
                current_attributes.update(update_data['epistemic_attributes'])
                update_data['epistemic_attributes'] = current_attributes
            
            # Update artifact in database
            updated_artifact = self.db_manager.update_node(artifact_uid, update_data)
            
            return {
                'status': 'success',
                'artifact': updated_artifact,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error updating knowledge artifact: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error updating knowledge artifact: {str(e)}",
                'artifact_uid': artifact_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def link_to_concept(self, artifact_uid: str, concept_uid: str,
                      relation_type: str = 'related_to_concept',
                      attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Link a knowledge artifact to a concept.
        
        Args:
            artifact_uid: Artifact UID
            concept_uid: Concept UID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing link result
        """
        self.logging.info(f"[{datetime.now()}] Linking artifact to concept: {artifact_uid} -> {concept_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify artifact and concept exist
            artifact = self.db_manager.get_node(artifact_uid)
            concept = self.db_manager.get_node(concept_uid)
            
            if not artifact or artifact.get('node_type') != 'knowledge_artifact':
                return {
                    'status': 'error',
                    'message': 'Invalid artifact UID',
                    'artifact_uid': artifact_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not concept or concept.get('node_type') != 'concept':
                return {
                    'status': 'error',
                    'message': 'Invalid concept UID',
                    'concept_uid': concept_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if link already exists
            existing_edges = self.db_manager.get_edges_between(artifact_uid, concept_uid, [relation_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Link already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create link
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': artifact_uid,
                'target_id': concept_uid,
                'edge_type': relation_type,
                'attributes': attributes or {}
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'artifact': artifact,
                'concept': concept,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking artifact to concept: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking artifact to concept: {str(e)}",
                'artifact_uid': artifact_uid,
                'concept_uid': concept_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_knowledge_artifact(self, artifact_uid: str, include_versions: bool = False) -> Dict[str, Any]:
        """
        Get a knowledge artifact by UID.
        
        Args:
            artifact_uid: Artifact UID
            include_versions: Whether to include version history
            
        Returns:
            Dict containing artifact information
        """
        self.logging.info(f"[{datetime.now()}] Getting knowledge artifact: {artifact_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get artifact
            artifact = self.db_manager.get_node(artifact_uid)
            
            if not artifact or artifact.get('node_type') != 'knowledge_artifact':
                return {
                    'status': 'error',
                    'message': 'Invalid artifact UID',
                    'artifact_uid': artifact_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            result = {
                'status': 'success',
                'artifact': artifact,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get linked concepts
            outgoing_edges = self.db_manager.get_outgoing_edges(artifact_uid, ['related_to_concept'])
            linked_concepts = []
            
            for edge in outgoing_edges:
                concept = self.db_manager.get_node(edge['target_id'])
                if concept and concept.get('node_type') == 'concept':
                    linked_concepts.append({
                        'concept': concept,
                        'relation_type': edge['edge_type'],
                        'attributes': edge.get('attributes', {})
                    })
            
            result['linked_concepts'] = linked_concepts
            
            # Get version history if requested
            if include_versions:
                version_history = []
                
                # Get previous versions
                outgoing_edges = self.db_manager.get_outgoing_edges(artifact_uid, ['previous_version'])
                
                for edge in outgoing_edges:
                    old_version = self.db_manager.get_node(edge['target_id'])
                    if old_version and old_version.get('node_type') == 'archived_knowledge_artifact':
                        version_history.append({
                            'version': old_version.get('version', 'unknown'),
                            'artifact': old_version,
                            'edge': edge
                        })
                
                result['version_history'] = version_history
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting knowledge artifact: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting knowledge artifact: {str(e)}",
                'artifact_uid': artifact_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def update_epistemic_attributes(self, artifact_uid: str, 
                                  attributes: Dict[str, float]) -> Dict[str, Any]:
        """
        Update epistemic attributes of a knowledge artifact.
        
        Args:
            artifact_uid: Artifact UID
            attributes: Dictionary of epistemic attributes and their values
            
        Returns:
            Dict containing update result
        """
        self.logging.info(f"[{datetime.now()}] Updating epistemic attributes for: {artifact_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify artifact exists
            artifact = self.db_manager.get_node(artifact_uid)
            
            if not artifact or artifact.get('node_type') != 'knowledge_artifact':
                return {
                    'status': 'error',
                    'message': 'Invalid artifact UID',
                    'artifact_uid': artifact_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate attributes
            for attr, value in attributes.items():
                if attr not in self.epistemic_attributes:
                    return {
                        'status': 'error',
                        'message': f'Invalid epistemic attribute: {attr}',
                        'valid_attributes': list(self.epistemic_attributes.keys()),
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Ensure all values are between 0 and 1
                if not isinstance(value, (int, float)) or value < 0 or value > 1:
                    return {
                        'status': 'error',
                        'message': f'Epistemic attribute {attr} must be a float between 0 and 1',
                        'provided_value': value,
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Get current attributes
            current_attributes = artifact.get('epistemic_attributes', {})
            
            # Update attributes
            current_attributes.update(attributes)
            
            # Update artifact
            update_data = {
                'epistemic_attributes': current_attributes,
                'updated_at': datetime.now().isoformat()
            }
            
            updated_artifact = self.db_manager.update_node(artifact_uid, update_data)
            
            return {
                'status': 'success',
                'artifact': updated_artifact,
                'updated_attributes': list(attributes.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error updating epistemic attributes: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error updating epistemic attributes: {str(e)}",
                'artifact_uid': artifact_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def search_knowledge_artifacts(self, query: Dict[str, Any], 
                               limit: int = 50) -> Dict[str, Any]:
        """
        Search for knowledge artifacts matching criteria.
        
        Args:
            query: Search criteria
            limit: Maximum number of results
            
        Returns:
            Dict containing search results
        """
        self.logging.info(f"[{datetime.now()}] Searching knowledge artifacts: {query}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Start with base query
            base_query = {
                'node_type': 'knowledge_artifact'
            }
            
            # Add other query parameters
            query_params = {**base_query, **query}
            
            # Execute search
            artifacts = self.db_manager.get_nodes_by_properties(query_params, limit=limit)
            
            # Filter by epistemic attributes if specified
            if 'min_attributes' in query and isinstance(query['min_attributes'], dict):
                filtered_artifacts = []
                
                for artifact in artifacts:
                    artifact_attributes = artifact.get('epistemic_attributes', {})
                    meets_criteria = True
                    
                    for attr, min_value in query['min_attributes'].items():
                        if attr not in self.epistemic_attributes:
                            continue  # Skip invalid attributes
                        
                        artifact_value = artifact_attributes.get(attr, 0)
                        if artifact_value < min_value:
                            meets_criteria = False
                            break
                    
                    if meets_criteria:
                        filtered_artifacts.append(artifact)
                
                artifacts = filtered_artifacts
            
            return {
                'status': 'success',
                'artifacts': artifacts,
                'count': len(artifacts),
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error searching knowledge artifacts: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error searching knowledge artifacts: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def link_artifacts(self, source_uid: str, target_uid: str, 
                     relation_type: str, 
                     attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Link two knowledge artifacts.
        
        Args:
            source_uid: Source artifact UID
            target_uid: Target artifact UID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing link result
        """
        self.logging.info(f"[{datetime.now()}] Linking artifacts: {source_uid} -> {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify artifacts exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source or source.get('node_type') != 'knowledge_artifact':
                return {
                    'status': 'error',
                    'message': 'Invalid source artifact UID',
                    'source_uid': source_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not target or target.get('node_type') != 'knowledge_artifact':
                return {
                    'status': 'error',
                    'message': 'Invalid target artifact UID',
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate relation type - more flexible for artifact-artifact relations
            valid_relation_types = [
                'supports', 'contradicts', 'elaborates', 'cites', 
                'derives_from', 'builds_upon', 'similar_to', 'alternative_to'
            ]
            
            if relation_type not in valid_relation_types:
                return {
                    'status': 'warning',
                    'message': f'Uncommon relation type: {relation_type}',
                    'suggested_types': valid_relation_types,
                    'proceeding_with_custom_type': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if link already exists
            existing_edges = self.db_manager.get_edges_between(source_uid, target_uid, [relation_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Link already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create link
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
                'source': source,
                'target': target,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking artifacts: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking artifacts: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }