"""
UKG Axis 3: Knowledge Domain

This module implements the Knowledge Domain axis of the Universal Knowledge Graph (UKG) system.
The Knowledge Domain axis manages the conceptual domains, knowledge areas, and taxonomic
relationships between concepts within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

class DomainManager:
    """
    Domain Manager for the UKG System
    
    Responsible for managing Axis 3 (Knowledge Domain) functionality, including:
    - Knowledge domain creation and management
    - Concept definition and relationships
    - Taxonomic structures (broader/narrower terms)
    - Cross-domain concept mapping
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Domain Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Relationship types for domain concepts
        self.concept_relation_types = {
            "broader": "Represents a broader/narrower hierarchical relationship",
            "narrower": "Inverse of broader",
            "related": "Indicates a non-hierarchical association between concepts",
            "equivalent": "Indicates conceptual equivalence across domains",
            "part_of": "Represents a part-whole relationship",
            "has_part": "Inverse of part_of",
            "causes": "Indicates a causal relationship",
            "uses": "Indicates that one concept uses or applies another",
            "instance_of": "Indicates that an entity is an instance of a concept"
        }
    
    def create_domain(self, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new knowledge domain in the system.
        
        Args:
            domain_data: Domain data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating domain: {domain_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure domain has required fields
            required_fields = ['label', 'description']
            for field in required_fields:
                if field not in domain_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Generate UID if not provided
            if 'uid' not in domain_data:
                domain_data['uid'] = f"domain_{uuid.uuid4()}"
            
            # Set axis number for Knowledge Domain axis
            domain_data['axis_number'] = 3
            domain_data['node_type'] = 'knowledge_domain'
            
            # Check if domain already exists with the same label
            existing_domains = self.db_manager.get_nodes_by_properties({
                'node_type': 'knowledge_domain',
                'label': domain_data['label']
            })
            
            if existing_domains:
                return {
                    'status': 'exists',
                    'message': 'Domain with this label already exists',
                    'domain': existing_domains[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add domain to database
            new_domain = self.db_manager.add_node(domain_data)
            
            return {
                'status': 'success',
                'domain': new_domain,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating domain: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating domain: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def create_concept(self, concept_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new concept in the system.
        
        Args:
            concept_data: Concept data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating concept: {concept_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure concept has required fields
            required_fields = ['label', 'domain_uid']
            for field in required_fields:
                if field not in concept_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Verify domain exists
            domain_uid = concept_data['domain_uid']
            domain = self.db_manager.get_node(domain_uid)
            
            if not domain or domain.get('node_type') != 'knowledge_domain':
                return {
                    'status': 'error',
                    'message': 'Invalid domain UID',
                    'domain_uid': domain_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in concept_data:
                # Use domain label as part of concept UID for better identification
                domain_prefix = domain.get('label', '').lower().replace(' ', '_')[:10]
                concept_prefix = concept_data['label'].lower().replace(' ', '_')[:10]
                concept_data['uid'] = f"concept_{domain_prefix}_{concept_prefix}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Knowledge Domain axis
            concept_data['axis_number'] = 3
            concept_data['node_type'] = 'concept'
            
            # Check if concept already exists in this domain
            existing_concepts = self.db_manager.get_nodes_by_properties({
                'node_type': 'concept',
                'label': concept_data['label'],
                'domain_uid': domain_uid
            })
            
            if existing_concepts:
                return {
                    'status': 'exists',
                    'message': 'Concept with this label already exists in the domain',
                    'concept': existing_concepts[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add concept to database
            new_concept = self.db_manager.add_node(concept_data)
            
            # Link concept to domain
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': domain_uid,
                'target_id': new_concept['uid'],
                'edge_type': 'has_concept',
                'attributes': {}
            }
            
            self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'concept': new_concept,
                'domain': domain,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating concept: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating concept: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def relate_concepts(self, source_uid: str, target_uid: str, 
                       relation_type: str, 
                       attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a relationship between two concepts.
        
        Args:
            source_uid: Source concept UID
            target_uid: Target concept UID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing relationship result
        """
        self.logging.info(f"[{datetime.now()}] Relating concepts: {source_uid} -> {target_uid} ({relation_type})")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify concepts exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source or not target:
                return {
                    'status': 'error',
                    'message': 'Source or target concept not found',
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate that both nodes are concepts
            if source.get('node_type') != 'concept' or target.get('node_type') != 'concept':
                return {
                    'status': 'error',
                    'message': 'Both nodes must be concepts',
                    'source_type': source.get('node_type'),
                    'target_type': target.get('node_type'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate relation type
            if relation_type not in self.concept_relation_types:
                return {
                    'status': 'error',
                    'message': f'Invalid relation type: {relation_type}',
                    'valid_types': list(self.concept_relation_types.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check for existing relationship
            existing_edges = self.db_manager.get_edges_between(source_uid, target_uid, [relation_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Relationship already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create the edge
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': source_uid,
                'target_id': target_uid,
                'edge_type': relation_type,
                'attributes': attributes or {}
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            # For certain relationship types, create inverse relationship automatically
            inverse_types = {
                'broader': 'narrower',
                'narrower': 'broader',
                'part_of': 'has_part',
                'has_part': 'part_of'
            }
            
            if relation_type in inverse_types:
                inverse_type = inverse_types[relation_type]
                # Check if inverse relation already exists
                existing_inverse = self.db_manager.get_edges_between(target_uid, source_uid, [inverse_type])
                
                if not existing_inverse:
                    inverse_edge_data = {
                        'uid': f"edge_{uuid.uuid4()}",
                        'source_id': target_uid,
                        'target_id': source_uid,
                        'edge_type': inverse_type,
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
            self.logging.error(f"[{datetime.now()}] Error relating concepts: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error relating concepts: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_domain_concepts(self, domain_uid: str) -> Dict[str, Any]:
        """
        Get all concepts in a domain.
        
        Args:
            domain_uid: Domain UID
            
        Returns:
            Dict containing domain concepts
        """
        self.logging.info(f"[{datetime.now()}] Getting concepts for domain: {domain_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify domain exists
            domain = self.db_manager.get_node(domain_uid)
            
            if not domain or domain.get('node_type') != 'knowledge_domain':
                return {
                    'status': 'error',
                    'message': 'Invalid domain UID',
                    'domain_uid': domain_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get all concepts linked to this domain
            # Method 1: Using domain_uid property
            concepts = self.db_manager.get_nodes_by_properties({
                'node_type': 'concept',
                'domain_uid': domain_uid
            })
            
            # Method 2: Using edges (as a backup)
            if not concepts:
                outgoing_edges = self.db_manager.get_outgoing_edges(domain_uid, ['has_concept'])
                concept_uids = [edge['target_id'] for edge in outgoing_edges]
                concepts = [self.db_manager.get_node(uid) for uid in concept_uids if uid]
                concepts = [c for c in concepts if c]  # Filter out None values
            
            return {
                'status': 'success',
                'domain': domain,
                'concepts': concepts,
                'concept_count': len(concepts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting domain concepts: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting domain concepts: {str(e)}",
                'domain_uid': domain_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_concept_relations(self, concept_uid: str, 
                            relation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get all relationships for a concept.
        
        Args:
            concept_uid: Concept UID
            relation_types: Optional list of relation types to filter by
            
        Returns:
            Dict containing concept relations
        """
        self.logging.info(f"[{datetime.now()}] Getting relations for concept: {concept_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify concept exists
            concept = self.db_manager.get_node(concept_uid)
            
            if not concept or concept.get('node_type') != 'concept':
                return {
                    'status': 'error',
                    'message': 'Invalid concept UID',
                    'concept_uid': concept_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # If no relation types specified, use all valid types
            if not relation_types:
                relation_types = list(self.concept_relation_types.keys())
            else:
                # Validate relation types
                invalid_types = [t for t in relation_types if t not in self.concept_relation_types]
                if invalid_types:
                    return {
                        'status': 'error',
                        'message': f'Invalid relation types: {invalid_types}',
                        'valid_types': list(self.concept_relation_types.keys()),
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Get outgoing relations
            outgoing_edges = self.db_manager.get_outgoing_edges(concept_uid, relation_types)
            outgoing_relations = []
            
            for edge in outgoing_edges:
                target_node = self.db_manager.get_node(edge['target_id'])
                if target_node and target_node.get('node_type') == 'concept':
                    outgoing_relations.append({
                        'relation_type': edge['edge_type'],
                        'target_concept': target_node,
                        'edge': edge
                    })
            
            # Get incoming relations
            incoming_edges = self.db_manager.get_incoming_edges(concept_uid, relation_types)
            incoming_relations = []
            
            for edge in incoming_edges:
                source_node = self.db_manager.get_node(edge['source_id'])
                if source_node and source_node.get('node_type') == 'concept':
                    incoming_relations.append({
                        'relation_type': edge['edge_type'],
                        'source_concept': source_node,
                        'edge': edge
                    })
            
            return {
                'status': 'success',
                'concept': concept,
                'outgoing_relations': outgoing_relations,
                'incoming_relations': incoming_relations,
                'outgoing_count': len(outgoing_relations),
                'incoming_count': len(incoming_relations),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting concept relations: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting concept relations: {str(e)}",
                'concept_uid': concept_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def find_concept_path(self, source_uid: str, target_uid: str, 
                        relation_types: Optional[List[str]] = None,
                        max_depth: int = 5) -> Dict[str, Any]:
        """
        Find paths between two concepts.
        
        Args:
            source_uid: Source concept UID
            target_uid: Target concept UID
            relation_types: Optional list of relation types to traverse
            max_depth: Maximum path depth
            
        Returns:
            Dict containing paths between concepts
        """
        self.logging.info(f"[{datetime.now()}] Finding path between concepts: {source_uid} -> {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify concepts exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source or not target:
                return {
                    'status': 'error',
                    'message': 'Source or target concept not found',
                    'source_uid': source_uid,
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate that both nodes are concepts
            if source.get('node_type') != 'concept' or target.get('node_type') != 'concept':
                return {
                    'status': 'error',
                    'message': 'Both nodes must be concepts',
                    'source_type': source.get('node_type'),
                    'target_type': target.get('node_type'),
                    'timestamp': datetime.now().isoformat()
                }
            
            # If no relation types specified, use all valid types
            if not relation_types:
                relation_types = list(self.concept_relation_types.keys())
            else:
                # Validate relation types
                invalid_types = [t for t in relation_types if t not in self.concept_relation_types]
                if invalid_types:
                    return {
                        'status': 'error',
                        'message': f'Invalid relation types: {invalid_types}',
                        'valid_types': list(self.concept_relation_types.keys()),
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Breadth-first search for paths
            paths = []
            visited = set([source_uid])
            queue = [[(source_uid, None, None)]]  # (node_uid, edge_from_parent, parent_uid)
            
            while queue and len(paths) < 10:  # Limit to 10 paths
                path = queue.pop(0)
                node_uid, _, _ = path[-1]
                
                if node_uid == target_uid:
                    # Found a path
                    formatted_path = []
                    for i, (node_id, edge, parent_id) in enumerate(path):
                        node = self.db_manager.get_node(node_id)
                        if i > 0:  # Skip edge for the first node
                            formatted_path.append({
                                'edge_type': edge.get('edge_type'),
                                'edge': edge
                            })
                        formatted_path.append({
                            'node': node,
                            'node_type': node.get('node_type'),
                            'label': node.get('label')
                        })
                    
                    paths.append(formatted_path)
                    continue
                
                if len(path) >= max_depth:
                    # Max depth reached for this path
                    continue
                
                # Get outgoing edges
                outgoing_edges = self.db_manager.get_outgoing_edges(node_uid, relation_types)
                
                for edge in outgoing_edges:
                    target_id = edge['target_id']
                    if target_id not in visited:
                        visited.add(target_id)
                        new_path = path.copy()
                        new_path.append((target_id, edge, node_uid))
                        queue.append(new_path)
            
            return {
                'status': 'success',
                'source': source,
                'target': target,
                'paths': paths,
                'path_count': len(paths),
                'max_depth': max_depth,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding concept path: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding concept path: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def extract_concept_taxonomy(self, root_concept_uid: str, 
                               relation_type: str = 'broader',
                               max_depth: int = 5) -> Dict[str, Any]:
        """
        Extract a taxonomic tree from a root concept.
        
        Args:
            root_concept_uid: Root concept UID
            relation_type: Relation type for taxonomy (usually 'broader' or 'narrower')
            max_depth: Maximum depth of taxonomy
            
        Returns:
            Dict containing taxonomic structure
        """
        self.logging.info(f"[{datetime.now()}] Extracting taxonomy from concept: {root_concept_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify root concept exists
            root_concept = self.db_manager.get_node(root_concept_uid)
            
            if not root_concept or root_concept.get('node_type') != 'concept':
                return {
                    'status': 'error',
                    'message': 'Invalid root concept UID',
                    'root_concept_uid': root_concept_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate relation type
            if relation_type not in self.concept_relation_types:
                return {
                    'status': 'error',
                    'message': f'Invalid relation type: {relation_type}',
                    'valid_types': list(self.concept_relation_types.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Choose edge direction based on relation type
            if relation_type == 'broader':
                # For 'broader', we find narrower terms (outgoing 'narrower' edges)
                traverse_relation = 'narrower'
                traverse_direction = 'outgoing'
            elif relation_type == 'narrower':
                # For 'narrower', we find broader terms (outgoing 'broader' edges)
                traverse_relation = 'broader'
                traverse_direction = 'outgoing'
            else:
                # For other relation types, use as-is
                traverse_relation = relation_type
                traverse_direction = 'outgoing'
            
            # Build taxonomy tree recursively
            taxonomy_tree = self._build_taxonomy_tree(
                concept_uid=root_concept_uid,
                relation_type=traverse_relation,
                direction=traverse_direction,
                current_depth=0,
                max_depth=max_depth,
                visited=set()
            )
            
            return {
                'status': 'success',
                'root_concept': root_concept,
                'taxonomy_tree': taxonomy_tree,
                'relation_type': relation_type,
                'max_depth': max_depth,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error extracting concept taxonomy: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error extracting concept taxonomy: {str(e)}",
                'root_concept_uid': root_concept_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def _build_taxonomy_tree(self, concept_uid: str, relation_type: str, direction: str,
                          current_depth: int, max_depth: int, visited: Set[str]) -> Dict[str, Any]:
        """
        Recursively build a taxonomy tree.
        
        Args:
            concept_uid: Current concept UID
            relation_type: Relation type to traverse
            direction: Direction of traversal ('incoming' or 'outgoing')
            current_depth: Current depth in the tree
            max_depth: Maximum depth to traverse
            visited: Set of visited concept UIDs
            
        Returns:
            Dict containing the taxonomy tree
        """
        if concept_uid in visited or current_depth >= max_depth:
            return None
        
        visited.add(concept_uid)
        concept = self.db_manager.get_node(concept_uid)
        
        if not concept:
            return None
        
        # Get related concepts
        edges = []
        if direction == 'outgoing':
            edges = self.db_manager.get_outgoing_edges(concept_uid, [relation_type])
        else:  # incoming
            edges = self.db_manager.get_incoming_edges(concept_uid, [relation_type])
        
        children = []
        for edge in edges:
            child_uid = edge['target_id'] if direction == 'outgoing' else edge['source_id']
            
            # Skip if already in this branch
            if child_uid in visited:
                continue
            
            child_tree = self._build_taxonomy_tree(
                concept_uid=child_uid,
                relation_type=relation_type,
                direction=direction,
                current_depth=current_depth + 1,
                max_depth=max_depth,
                visited=visited.copy()
            )
            
            if child_tree:
                children.append(child_tree)
        
        # Build the tree node
        tree_node = {
            'concept': concept,
            'uid': concept['uid'],
            'label': concept['label'],
            'depth': current_depth,
            'children': children
        }
        
        return tree_node