
"""
UKG Axis 6: Regulatory Framework

This module implements the Regulatory Framework axis of the Universal Knowledge Graph (UKG) system,
using an octopus node structure with branch-style mappings.

The Octopus Node System represents how regulatory frameworks branch out with:
- Mega regulatory frameworks (central nodes)
- Large regulatory frameworks (primary tentacles)
- Medium regulatory frameworks (secondary branches)
- Small regulatory frameworks (tertiary branches)
- Granular requirements (leaf nodes)
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

class RegulatoryManager:
    """
    Regulatory Manager for the UKG System
    
    Responsible for managing Axis 6 (Regulatory) functionality, including:
    - Regulatory framework creation and management in octopus structure
    - Regulatory requirement tracking and mapping
    - Cross-jurisdiction mapping
    - Compliance validation and crosswalking with Axis 7
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Regulatory Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Octopus node structure levels
        self.node_levels = {
            "mega": "Top-level regulatory architecture (e.g., EU Regulatory System)",
            "large": "Major regulatory framework (e.g., GDPR, Dodd-Frank)",
            "medium": "Specific regulation area (e.g., GDPR Article 5, Dodd-Frank Title IX)",
            "small": "Individual regulation (e.g., GDPR Art. 5.1.a, specific provisions)",
            "granular": "Detailed requirements (e.g., specific compliance points)"
        }
        
        # Common regulatory framework types
        self.framework_types = {
            "law": "Enacted legislation",
            "regulation": "Administrative rules issued by government agencies",
            "directive": "Administrative instruction",
            "standard": "Technical specifications or requirements",
            "guideline": "Recommended practices",
            "policy": "Organization or agency policy",
            "code": "Formalized set of rules",
            "order": "Executive or administrative order"
        }
        
        # Authority levels for regulatory frameworks
        self.authority_levels = {
            "supranational": "Above the national level (e.g., EU, UN)",
            "federal": "National government level",
            "state": "State or provincial level",
            "local": "Local government level",
            "industry": "Industry self-regulation",
            "organizational": "Organization-specific policies"
        }
    
    def create_mega_framework(self, framework_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new mega regulatory framework (top-level node).
        
        Args:
            framework_data: Framework data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating mega regulatory framework: {framework_data.get('label', 'Unknown')}")
        
        # Add node level
        framework_data['node_level'] = 'mega'
        
        # Create the framework
        return self._create_regulatory_framework(framework_data)
    
    def create_large_framework(self, framework_data: Dict[str, Any], parent_uid: str) -> Dict[str, Any]:
        """
        Create a new large regulatory framework connected to a mega framework.
        
        Args:
            framework_data: Framework data dictionary
            parent_uid: Parent mega framework UID
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating large regulatory framework: {framework_data.get('label', 'Unknown')}")
        
        # Add node level
        framework_data['node_level'] = 'large'
        framework_data['parent_uid'] = parent_uid
        
        # Create the framework and link to parent
        result = self._create_regulatory_framework(framework_data)
        
        if result['status'] == 'success':
            self._link_parent_child_frameworks(parent_uid, result['framework']['uid'], 'has_large_framework')
        
        return result
    
    def create_medium_framework(self, framework_data: Dict[str, Any], parent_uid: str) -> Dict[str, Any]:
        """
        Create a new medium regulatory framework connected to a large framework.
        
        Args:
            framework_data: Framework data dictionary
            parent_uid: Parent large framework UID
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating medium regulatory framework: {framework_data.get('label', 'Unknown')}")
        
        # Add node level
        framework_data['node_level'] = 'medium'
        framework_data['parent_uid'] = parent_uid
        
        # Create the framework and link to parent
        result = self._create_regulatory_framework(framework_data)
        
        if result['status'] == 'success':
            self._link_parent_child_frameworks(parent_uid, result['framework']['uid'], 'has_medium_framework')
        
        return result
    
    def create_small_framework(self, framework_data: Dict[str, Any], parent_uid: str) -> Dict[str, Any]:
        """
        Create a new small regulatory framework connected to a medium framework.
        
        Args:
            framework_data: Framework data dictionary
            parent_uid: Parent medium framework UID
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating small regulatory framework: {framework_data.get('label', 'Unknown')}")
        
        # Add node level
        framework_data['node_level'] = 'small'
        framework_data['parent_uid'] = parent_uid
        
        # Create the framework and link to parent
        result = self._create_regulatory_framework(framework_data)
        
        if result['status'] == 'success':
            self._link_parent_child_frameworks(parent_uid, result['framework']['uid'], 'has_small_framework')
        
        return result
    
    def create_granular_requirement(self, requirement_data: Dict[str, Any], parent_uid: str) -> Dict[str, Any]:
        """
        Create a new granular requirement connected to a small framework.
        
        Args:
            requirement_data: Requirement data dictionary
            parent_uid: Parent small framework UID
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating granular requirement: {requirement_data.get('label', 'Unknown')}")
        
        # Add node level and type
        requirement_data['node_level'] = 'granular'
        requirement_data['node_type'] = 'regulatory_requirement'
        requirement_data['parent_uid'] = parent_uid
        requirement_data['axis_number'] = 6
        
        # Ensure the requirement has a unique ID
        if 'uid' not in requirement_data:
            parent_id = parent_uid.split('_')[-2] if '_' in parent_uid else 'reg'
            label_snippet = requirement_data['label'].lower().replace(' ', '_')[:15]
            requirement_data['uid'] = f"req_granular_{parent_id}_{label_snippet}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Add requirement to database
            new_requirement = self.db_manager.add_node(requirement_data)
            
            # Link requirement to parent framework
            self._link_parent_child_frameworks(parent_uid, new_requirement['uid'], 'has_requirement')
            
            return {
                'status': 'success',
                'requirement': new_requirement,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating granular requirement: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating granular requirement: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_regulatory_framework(self, framework_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to create a regulatory framework at any level.
        
        Args:
            framework_data: Framework data dictionary
            
        Returns:
            Dict containing creation result
        """
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure framework has required fields
            required_fields = ['label', 'framework_type', 'issuing_authority']
            for field in required_fields:
                if field not in framework_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Validate framework type
            if framework_data['framework_type'] not in self.framework_types:
                return {
                    'status': 'warning',
                    'message': f'Uncommon framework type: {framework_data["framework_type"]}',
                    'valid_types': list(self.framework_types.keys()),
                    'proceeding_with_custom_type': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in framework_data:
                node_level = framework_data.get('node_level', 'generic')
                framework_type = framework_data['framework_type']
                issuing_authority = framework_data['issuing_authority'].lower().replace(' ', '_')[:15]
                label_snippet = framework_data['label'].lower().replace(' ', '_')[:15]
                framework_data['uid'] = f"regulatory_{node_level}_{framework_type}_{issuing_authority}_{label_snippet}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Regulatory axis
            framework_data['axis_number'] = 6
            framework_data['node_type'] = 'regulatory_framework'
            
            # Set effective dates if provided
            if 'effective_date' in framework_data:
                if isinstance(framework_data['effective_date'], datetime):
                    framework_data['effective_date'] = framework_data['effective_date'].isoformat()
            
            if 'expiration_date' in framework_data:
                if isinstance(framework_data['expiration_date'], datetime):
                    framework_data['expiration_date'] = framework_data['expiration_date'].isoformat()
            
            # Add framework to database
            new_framework = self.db_manager.add_node(framework_data)
            
            return {
                'status': 'success',
                'framework': new_framework,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating regulatory framework: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating regulatory framework: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _link_parent_child_frameworks(self, parent_uid: str, child_uid: str, edge_type: str) -> Dict[str, Any]:
        """
        Link parent and child frameworks with appropriate edge type.
        
        Args:
            parent_uid: Parent framework UID
            child_uid: Child framework UID
            edge_type: Type of relationship edge
            
        Returns:
            Dict containing link result
        """
        try:
            # Check if link already exists
            existing_edges = self.db_manager.get_edges_between(parent_uid, child_uid, [edge_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Link already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create edge
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': parent_uid,
                'target_id': child_uid,
                'edge_type': edge_type,
                'attributes': {
                    'created_at': datetime.now().isoformat()
                }
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            # Create inverse edge for efficient traversal
            inverse_edge_types = {
                'has_large_framework': 'belongs_to_mega_framework',
                'has_medium_framework': 'belongs_to_large_framework',
                'has_small_framework': 'belongs_to_medium_framework',
                'has_requirement': 'belongs_to_small_framework'
            }
            
            if edge_type in inverse_edge_types:
                inverse_edge_data = {
                    'uid': f"edge_{uuid.uuid4()}",
                    'source_id': child_uid,
                    'target_id': parent_uid,
                    'edge_type': inverse_edge_types[edge_type],
                    'attributes': {
                        'created_at': datetime.now().isoformat()
                    }
                }
                self.db_manager.add_edge(inverse_edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking frameworks: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking frameworks: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_octopus_structure(self, mega_framework_uid: str) -> Dict[str, Any]:
        """
        Get the complete octopus structure for a mega framework.
        
        Args:
            mega_framework_uid: Mega framework UID
            
        Returns:
            Dict containing the octopus structure
        """
        self.logging.info(f"[{datetime.now()}] Getting octopus structure for framework: {mega_framework_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get mega framework
            mega_framework = self.db_manager.get_node(mega_framework_uid)
            
            if not mega_framework or mega_framework.get('node_type') != 'regulatory_framework' or mega_framework.get('node_level') != 'mega':
                return {
                    'status': 'error',
                    'message': 'Invalid mega framework UID or not a mega framework',
                    'framework_uid': mega_framework_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Initialize octopus structure
            octopus = {
                'mega_framework': mega_framework,
                'large_frameworks': {}
            }
            
            # Get large frameworks
            large_frameworks_edges = self.db_manager.get_outgoing_edges(mega_framework_uid, ['has_large_framework'])
            
            for large_edge in large_frameworks_edges:
                large_framework = self.db_manager.get_node(large_edge['target_id'])
                
                if not large_framework:
                    continue
                
                large_framework_id = large_framework['uid']
                octopus['large_frameworks'][large_framework_id] = {
                    'framework': large_framework,
                    'relation': large_edge,
                    'medium_frameworks': {}
                }
                
                # Get medium frameworks for each large framework
                medium_frameworks_edges = self.db_manager.get_outgoing_edges(large_framework_id, ['has_medium_framework'])
                
                for medium_edge in medium_frameworks_edges:
                    medium_framework = self.db_manager.get_node(medium_edge['target_id'])
                    
                    if not medium_framework:
                        continue
                    
                    medium_framework_id = medium_framework['uid']
                    octopus['large_frameworks'][large_framework_id]['medium_frameworks'][medium_framework_id] = {
                        'framework': medium_framework,
                        'relation': medium_edge,
                        'small_frameworks': {}
                    }
                    
                    # Get small frameworks for each medium framework
                    small_frameworks_edges = self.db_manager.get_outgoing_edges(medium_framework_id, ['has_small_framework'])
                    
                    for small_edge in small_frameworks_edges:
                        small_framework = self.db_manager.get_node(small_edge['target_id'])
                        
                        if not small_framework:
                            continue
                        
                        small_framework_id = small_framework['uid']
                        octopus['large_frameworks'][large_framework_id]['medium_frameworks'][medium_framework_id]['small_frameworks'][small_framework_id] = {
                            'framework': small_framework,
                            'relation': small_edge,
                            'granular_requirements': {}
                        }
                        
                        # Get granular requirements for each small framework
                        requirement_edges = self.db_manager.get_outgoing_edges(small_framework_id, ['has_requirement'])
                        
                        for req_edge in requirement_edges:
                            requirement = self.db_manager.get_node(req_edge['target_id'])
                            
                            if not requirement:
                                continue
                            
                            requirement_id = requirement['uid']
                            octopus['large_frameworks'][large_framework_id]['medium_frameworks'][medium_framework_id]['small_frameworks'][small_framework_id]['granular_requirements'][requirement_id] = {
                                'requirement': requirement,
                                'relation': req_edge
                            }
            
            # Count nodes at each level
            large_count = len(octopus['large_frameworks'])
            medium_count = sum(len(large_data['medium_frameworks']) for large_data in octopus['large_frameworks'].values())
            small_count = sum(
                sum(len(medium_data['small_frameworks']) for medium_data in large_data['medium_frameworks'].values())
                for large_data in octopus['large_frameworks'].values()
            )
            requirement_count = sum(
                sum(
                    sum(len(small_data['granular_requirements']) for small_data in medium_data['small_frameworks'].values())
                    for medium_data in large_data['medium_frameworks'].values()
                )
                for large_data in octopus['large_frameworks'].values()
            )
            
            return {
                'status': 'success',
                'octopus': octopus,
                'counts': {
                    'mega': 1,
                    'large': large_count,
                    'medium': medium_count,
                    'small': small_count,
                    'granular': requirement_count,
                    'total': 1 + large_count + medium_count + small_count + requirement_count
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting octopus structure: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting octopus structure: {str(e)}",
                'framework_uid': mega_framework_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def link_regulatory_frameworks(self, source_uid: str, target_uid: str, 
                                 relation_type: str, 
                                 attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Link two regulatory frameworks with custom relation type.
        
        Args:
            source_uid: Source framework UID
            target_uid: Target framework UID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing link result
        """
        self.logging.info(f"[{datetime.now()}] Linking regulatory frameworks: {source_uid} -> {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify frameworks exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source or source.get('node_type') != 'regulatory_framework':
                return {
                    'status': 'error',
                    'message': 'Invalid source framework UID',
                    'source_uid': source_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not target or target.get('node_type') != 'regulatory_framework':
                return {
                    'status': 'error',
                    'message': 'Invalid target framework UID',
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate relation type - common relationships between regulatory frameworks
            valid_relation_types = [
                'supersedes', 'implements', 'references', 'derives_from', 
                'amends', 'complements', 'conflicts_with', 'harmonizes_with',
                'extends', 'specializes', 'provides_exception_to'
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
            
            # For certain relationship types, create inverse relationship automatically
            inverse_relations = {
                'supersedes': 'superseded_by',
                'implements': 'implemented_by',
                'references': 'referenced_by',
                'derives_from': 'derived_by',
                'amends': 'amended_by',
                'extends': 'extended_by',
                'specializes': 'generalized_by',
                'provides_exception_to': 'has_exception_from'
            }
            
            if relation_type in inverse_relations:
                inverse_type = inverse_relations[relation_type]
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
            self.logging.error(f"[{datetime.now()}] Error linking regulatory frameworks: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking regulatory frameworks: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def map_jurisdictions(self, framework_uid: str, 
                        jurisdiction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a regulatory framework to jurisdictions.
        
        Args:
            framework_uid: Framework UID
            jurisdiction_data: Jurisdiction data dictionary
            
        Returns:
            Dict containing mapping result
        """
        self.logging.info(f"[{datetime.now()}] Mapping jurisdictions for framework: {framework_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify framework exists
            framework = self.db_manager.get_node(framework_uid)
            
            if not framework or framework.get('node_type') != 'regulatory_framework':
                return {
                    'status': 'error',
                    'message': 'Invalid framework UID',
                    'framework_uid': framework_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure jurisdiction data has required fields
            required_fields = ['type', 'name']
            for field in required_fields:
                if field not in jurisdiction_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field in jurisdiction data: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Validate jurisdiction type
            valid_jurisdiction_types = [
                'global', 'international', 'supranational', 'national', 
                'federal', 'state', 'provincial', 'regional', 'local', 
                'municipal', 'industry', 'sector'
            ]
            
            if jurisdiction_data['type'] not in valid_jurisdiction_types:
                return {
                    'status': 'warning',
                    'message': f'Uncommon jurisdiction type: {jurisdiction_data["type"]}',
                    'valid_types': valid_jurisdiction_types,
                    'proceeding_with_custom_type': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate jurisdiction UID
            jurisdiction_type = jurisdiction_data['type']
            jurisdiction_name = jurisdiction_data['name'].lower().replace(' ', '_')
            jurisdiction_uid = f"jurisdiction_{jurisdiction_type}_{jurisdiction_name}_{uuid.uuid4().hex[:8]}"
            
            # See if jurisdiction already exists
            existing_jurisdictions = self.db_manager.get_nodes_by_properties({
                'node_type': 'jurisdiction',
                'type': jurisdiction_data['type'],
                'name': jurisdiction_data['name']
            })
            
            if existing_jurisdictions:
                jurisdiction_uid = existing_jurisdictions[0]['uid']
                jurisdiction = existing_jurisdictions[0]
                is_new_jurisdiction = False
            else:
                # Create jurisdiction node
                jurisdiction_node_data = {
                    'uid': jurisdiction_uid,
                    'node_type': 'jurisdiction',
                    'label': jurisdiction_data['name'],
                    'type': jurisdiction_data['type'],
                    'name': jurisdiction_data['name'],
                    'axis_number': 6,  # Jurisdictions are part of Regulatory axis
                    'attributes': jurisdiction_data.get('attributes', {})
                }
                
                jurisdiction = self.db_manager.add_node(jurisdiction_node_data)
                is_new_jurisdiction = True
            
            # Link framework to jurisdiction
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': framework_uid,
                'target_id': jurisdiction_uid,
                'edge_type': 'applies_to_jurisdiction',
                'attributes': jurisdiction_data.get('relationship_attributes', {})
            }
            
            # Check if link already exists
            existing_edges = self.db_manager.get_edges_between(framework_uid, jurisdiction_uid, ['applies_to_jurisdiction'])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Framework already mapped to this jurisdiction',
                    'edge': existing_edges[0],
                    'framework': framework,
                    'jurisdiction': jurisdiction,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            # Create reverse edge
            reverse_edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': jurisdiction_uid,
                'target_id': framework_uid,
                'edge_type': 'has_regulatory_framework',
                'attributes': jurisdiction_data.get('relationship_attributes', {})
            }
            self.db_manager.add_edge(reverse_edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'framework': framework,
                'jurisdiction': jurisdiction,
                'is_new_jurisdiction': is_new_jurisdiction,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error mapping jurisdictions: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error mapping jurisdictions: {str(e)}",
                'framework_uid': framework_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_regulatory_crosswalk(self, source_uid: str, target_uid: str, 
                                  crosswalk_type: str,
                                  attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a crosswalk between regulatory frameworks or requirements.
        
        Args:
            source_uid: Source node UID
            target_uid: Target node UID
            crosswalk_type: Type of crosswalk
            attributes: Optional crosswalk attributes
            
        Returns:
            Dict containing crosswalk result
        """
        self.logging.info(f"[{datetime.now()}] Creating regulatory crosswalk: {source_uid} -> {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify nodes exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source:
                return {
                    'status': 'error',
                    'message': 'Invalid source node UID',
                    'source_uid': source_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not target:
                return {
                    'status': 'error',
                    'message': 'Invalid target node UID',
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate crosswalk type
            valid_crosswalk_types = [
                'equivalent_to', 'similar_to', 'more_stringent_than', 
                'less_stringent_than', 'overlaps_with', 'contradicts', 
                'complements', 'derived_from'
            ]
            
            if crosswalk_type not in valid_crosswalk_types:
                return {
                    'status': 'warning',
                    'message': f'Uncommon crosswalk type: {crosswalk_type}',
                    'suggested_types': valid_crosswalk_types,
                    'proceeding_with_custom_type': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare attributes
            crosswalk_attributes = attributes or {}
            crosswalk_attributes.update({
                'created_at': datetime.now().isoformat(),
                'crosswalk': True,
                'description': f"Regulatory crosswalk: {crosswalk_type}"
            })
            
            # Check if crosswalk already exists
            existing_edges = self.db_manager.get_edges_between(source_uid, target_uid, [crosswalk_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Crosswalk already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create crosswalk edge
            edge_data = {
                'uid': f"crosswalk_{uuid.uuid4()}",
                'source_id': source_uid,
                'target_id': target_uid,
                'edge_type': crosswalk_type,
                'attributes': crosswalk_attributes
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            # Add inverse edge for certain crosswalk types
            inverse_crosswalks = {
                'equivalent_to': 'equivalent_to',
                'similar_to': 'similar_to',
                'more_stringent_than': 'less_stringent_than',
                'less_stringent_than': 'more_stringent_than',
                'overlaps_with': 'overlaps_with',
                'contradicts': 'contradicts',
                'complements': 'complemented_by',
                'derived_from': 'derived_by'
            }
            
            if crosswalk_type in inverse_crosswalks:
                inverse_type = inverse_crosswalks[crosswalk_type]
                
                # Skip if source and target are the same and inverse type is the same
                if source_uid != target_uid or crosswalk_type != inverse_type:
                    # Check if inverse crosswalk already exists
                    existing_inverse = self.db_manager.get_edges_between(target_uid, source_uid, [inverse_type])
                    
                    if not existing_inverse:
                        inverse_edge_data = {
                            'uid': f"crosswalk_{uuid.uuid4()}",
                            'source_id': target_uid,
                            'target_id': source_uid,
                            'edge_type': inverse_type,
                            'attributes': crosswalk_attributes
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
            self.logging.error(f"[{datetime.now()}] Error creating regulatory crosswalk: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating regulatory crosswalk: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_compliance_link(self, framework_uid: str, 
                             compliance_standard_uid: str, 
                             link_type: str = 'implements',
                             attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a link between a regulatory framework and a compliance standard (Axis 7).
        
        Args:
            framework_uid: Framework UID
            compliance_standard_uid: Compliance standard UID
            link_type: Type of link
            attributes: Optional link attributes
            
        Returns:
            Dict containing link result
        """
        self.logging.info(f"[{datetime.now()}] Creating compliance link: {framework_uid} -> {compliance_standard_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify nodes exist
            framework = self.db_manager.get_node(framework_uid)
            compliance_standard = self.db_manager.get_node(compliance_standard_uid)
            
            if not framework or framework.get('node_type') != 'regulatory_framework':
                return {
                    'status': 'error',
                    'message': 'Invalid framework UID',
                    'framework_uid': framework_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not compliance_standard or compliance_standard.get('axis_number') != 7:
                return {
                    'status': 'error',
                    'message': 'Invalid compliance standard UID or not from Axis 7',
                    'compliance_standard_uid': compliance_standard_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate link type
            valid_link_types = [
                'implements', 'references', 'influenced_by', 
                'basis_for', 'helps_comply_with', 'certifies'
            ]
            
            if link_type not in valid_link_types:
                return {
                    'status': 'warning',
                    'message': f'Uncommon link type: {link_type}',
                    'suggested_types': valid_link_types,
                    'proceeding_with_custom_type': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Prepare attributes
            link_attributes = attributes or {}
            link_attributes.update({
                'created_at': datetime.now().isoformat(),
                'cross_axis': True,
                'axis_source': 6,
                'axis_target': 7
            })
            
            # Check if link already exists
            existing_edges = self.db_manager.get_edges_between(framework_uid, compliance_standard_uid, [link_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Link already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create link edge
            edge_data = {
                'uid': f"axis6_axis7_link_{uuid.uuid4()}",
                'source_id': framework_uid,
                'target_id': compliance_standard_uid,
                'edge_type': link_type,
                'attributes': link_attributes
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            # Add inverse edge for proper traversal
            inverse_links = {
                'implements': 'implemented_by',
                'references': 'referenced_by',
                'influenced_by': 'influences',
                'basis_for': 'based_on',
                'helps_comply_with': 'compliance_helped_by',
                'certifies': 'certified_by'
            }
            
            if link_type in inverse_links:
                inverse_type = inverse_links[link_type]
                
                # Check if inverse link already exists
                existing_inverse = self.db_manager.get_edges_between(compliance_standard_uid, framework_uid, [inverse_type])
                
                if not existing_inverse:
                    inverse_edge_data = {
                        'uid': f"axis7_axis6_link_{uuid.uuid4()}",
                        'source_id': compliance_standard_uid,
                        'target_id': framework_uid,
                        'edge_type': inverse_type,
                        'attributes': {
                            'created_at': datetime.now().isoformat(),
                            'cross_axis': True,
                            'axis_source': 7,
                            'axis_target': 6
                        }
                    }
                    self.db_manager.add_edge(inverse_edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'framework': framework,
                'compliance_standard': compliance_standard,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating compliance link: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating compliance link: {str(e)}",
                'framework_uid': framework_uid,
                'compliance_standard_uid': compliance_standard_uid,
                'timestamp': datetime.now().isoformat()
            }
