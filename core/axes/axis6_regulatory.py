"""
UKG Axis 6: Regulatory

This module implements the Regulatory axis of the Universal Knowledge Graph (UKG) system.
The Regulatory axis manages regulatory frameworks, compliance requirements, and
legal structures within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

class RegulatoryManager:
    """
    Regulatory Manager for the UKG System
    
    Responsible for managing Axis 6 (Regulatory) functionality, including:
    - Regulatory framework creation and management
    - Regulatory requirement tracking
    - Cross-jurisdiction mapping
    - Compliance validation
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
    
    def create_regulatory_framework(self, framework_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new regulatory framework in the system.
        
        Args:
            framework_data: Framework data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating regulatory framework: {framework_data.get('label', 'Unknown')}")
        
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
                framework_type = framework_data['framework_type']
                issuing_authority = framework_data['issuing_authority'].lower().replace(' ', '_')[:15]
                label_snippet = framework_data['label'].lower().replace(' ', '_')[:15]
                framework_data['uid'] = f"regulatory_{framework_type}_{issuing_authority}_{label_snippet}_{uuid.uuid4().hex[:8]}"
            
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
    
    def create_regulatory_requirement(self, requirement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new regulatory requirement in the system.
        
        Args:
            requirement_data: Requirement data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating regulatory requirement: {requirement_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure requirement has required fields
            required_fields = ['label', 'framework_uid', 'content']
            for field in required_fields:
                if field not in requirement_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Verify framework exists
            framework_uid = requirement_data['framework_uid']
            framework = self.db_manager.get_node(framework_uid)
            
            if not framework or framework.get('node_type') != 'regulatory_framework':
                return {
                    'status': 'error',
                    'message': 'Invalid framework UID',
                    'framework_uid': framework_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in requirement_data:
                # Extract framework prefix from framework UID for better identification
                framework_prefix = framework_uid.split('_')[1] if len(framework_uid.split('_')) > 1 else 'reg'
                label_snippet = requirement_data['label'].lower().replace(' ', '_')[:15]
                requirement_data['uid'] = f"req_{framework_prefix}_{label_snippet}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Regulatory axis
            requirement_data['axis_number'] = 6
            requirement_data['node_type'] = 'regulatory_requirement'
            
            # Add requirement to database
            new_requirement = self.db_manager.add_node(requirement_data)
            
            # Link requirement to framework
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': framework_uid,
                'target_id': new_requirement['uid'],
                'edge_type': 'has_requirement',
                'attributes': {}
            }
            
            self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'requirement': new_requirement,
                'framework': framework,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating regulatory requirement: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating regulatory requirement: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def link_regulatory_frameworks(self, source_uid: str, target_uid: str, 
                                 relation_type: str, 
                                 attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Link two regulatory frameworks.
        
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
                'amends', 'complements', 'conflicts_with', 'harmonizes_with'
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
                'amends': 'amended_by'
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
    
    def get_framework_details(self, framework_uid: str, 
                           include_requirements: bool = True,
                           include_jurisdictions: bool = True) -> Dict[str, Any]:
        """
        Get detailed information about a regulatory framework.
        
        Args:
            framework_uid: Framework UID
            include_requirements: Whether to include requirements
            include_jurisdictions: Whether to include jurisdictions
            
        Returns:
            Dict containing framework details
        """
        self.logging.info(f"[{datetime.now()}] Getting details for framework: {framework_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get framework
            framework = self.db_manager.get_node(framework_uid)
            
            if not framework or framework.get('node_type') != 'regulatory_framework':
                return {
                    'status': 'error',
                    'message': 'Invalid framework UID',
                    'framework_uid': framework_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            result = {
                'status': 'success',
                'framework': framework,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get requirements if requested
            if include_requirements:
                # Get edges connecting to requirements
                requirement_edges = self.db_manager.get_outgoing_edges(framework_uid, ['has_requirement'])
                requirements = []
                
                for edge in requirement_edges:
                    requirement = self.db_manager.get_node(edge['target_id'])
                    if requirement and requirement.get('node_type') == 'regulatory_requirement':
                        requirements.append({
                            'requirement': requirement,
                            'edge': edge
                        })
                
                result['requirements'] = requirements
                result['requirement_count'] = len(requirements)
            
            # Get jurisdictions if requested
            if include_jurisdictions:
                # Get edges connecting to jurisdictions
                jurisdiction_edges = self.db_manager.get_outgoing_edges(framework_uid, ['applies_to_jurisdiction'])
                jurisdictions = []
                
                for edge in jurisdiction_edges:
                    jurisdiction = self.db_manager.get_node(edge['target_id'])
                    if jurisdiction and jurisdiction.get('node_type') == 'jurisdiction':
                        jurisdictions.append({
                            'jurisdiction': jurisdiction,
                            'edge': edge
                        })
                
                result['jurisdictions'] = jurisdictions
                result['jurisdiction_count'] = len(jurisdictions)
            
            # Get related frameworks
            related_frameworks = []
            
            # Check for outgoing edges to other frameworks
            outgoing_edges = self.db_manager.get_outgoing_edges(framework_uid)
            for edge in outgoing_edges:
                target_node = self.db_manager.get_node(edge['target_id'])
                if target_node and target_node.get('node_type') == 'regulatory_framework':
                    related_frameworks.append({
                        'framework': target_node,
                        'relation_type': edge['edge_type'],
                        'direction': 'outgoing',
                        'edge': edge
                    })
            
            # Check for incoming edges from other frameworks
            incoming_edges = self.db_manager.get_incoming_edges(framework_uid)
            for edge in incoming_edges:
                source_node = self.db_manager.get_node(edge['source_id'])
                if source_node and source_node.get('node_type') == 'regulatory_framework':
                    related_frameworks.append({
                        'framework': source_node,
                        'relation_type': edge['edge_type'],
                        'direction': 'incoming',
                        'edge': edge
                    })
            
            result['related_frameworks'] = related_frameworks
            result['related_framework_count'] = len(related_frameworks)
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting framework details: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting framework details: {str(e)}",
                'framework_uid': framework_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def search_regulatory_elements(self, query: Dict[str, Any], 
                                search_requirements: bool = True,
                                limit: int = 50) -> Dict[str, Any]:
        """
        Search for regulatory frameworks and requirements matching criteria.
        
        Args:
            query: Search criteria
            search_requirements: Whether to search requirements
            limit: Maximum number of results
            
        Returns:
            Dict containing search results
        """
        self.logging.info(f"[{datetime.now()}] Searching regulatory elements: {query}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            results = {
                'frameworks': [],
                'requirements': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Prepare framework query
            framework_query = {
                'node_type': 'regulatory_framework'
            }
            
            # Add other query parameters specific to frameworks
            for key, value in query.items():
                if key in ['framework_type', 'issuing_authority', 'label']:
                    framework_query[key] = value
            
            # Execute framework search
            frameworks = self.db_manager.get_nodes_by_properties(framework_query, limit=limit)
            results['frameworks'] = frameworks
            
            # Search requirements if requested
            if search_requirements:
                # Prepare requirement query
                requirement_query = {
                    'node_type': 'regulatory_requirement'
                }
                
                # Add other query parameters specific to requirements
                for key, value in query.items():
                    if key in ['label', 'content']:
                        requirement_query[key] = value
                
                # Check if we need to filter by framework
                if 'framework_uid' in query:
                    requirement_query['framework_uid'] = query['framework_uid']
                
                # Execute requirement search
                requirements = self.db_manager.get_nodes_by_properties(requirement_query, limit=limit)
                results['requirements'] = requirements
            
            # Compile results
            return {
                'status': 'success',
                'frameworks': results['frameworks'],
                'framework_count': len(results['frameworks']),
                'requirements': results['requirements'] if search_requirements else [],
                'requirement_count': len(results['requirements']) if search_requirements else 0,
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error searching regulatory elements: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error searching regulatory elements: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_regulatory_landscape(self, domain_uid: str) -> Dict[str, Any]:
        """
        Get the regulatory landscape for a specific domain.
        
        Args:
            domain_uid: Domain UID
            
        Returns:
            Dict containing the regulatory landscape
        """
        self.logging.info(f"[{datetime.now()}] Getting regulatory landscape for domain: {domain_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify domain exists
            domain = self.db_manager.get_node(domain_uid)
            
            if not domain:
                return {
                    'status': 'error',
                    'message': 'Invalid domain UID',
                    'domain_uid': domain_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get all frameworks linked to this domain
            # For Axis 3 domains, look for edges of type 'regulated_by'
            if domain.get('node_type') == 'knowledge_domain' and domain.get('axis_number') == 3:
                outgoing_edges = self.db_manager.get_outgoing_edges(domain_uid, ['regulated_by'])
                linked_frameworks = []
                
                for edge in outgoing_edges:
                    framework = self.db_manager.get_node(edge['target_id'])
                    if framework and framework.get('node_type') == 'regulatory_framework':
                        linked_frameworks.append({
                            'framework': framework,
                            'edge': edge
                        })
                
                return {
                    'status': 'success',
                    'domain': domain,
                    'frameworks': linked_frameworks,
                    'framework_count': len(linked_frameworks),
                    'timestamp': datetime.now().isoformat()
                }
            
            # For Axis 2 sectors, look for edges of type 'regulated_by'
            if domain.get('node_type') == 'sector' and domain.get('axis_number') == 2:
                outgoing_edges = self.db_manager.get_outgoing_edges(domain_uid, ['regulated_by'])
                linked_frameworks = []
                
                for edge in outgoing_edges:
                    framework = self.db_manager.get_node(edge['target_id'])
                    if framework and framework.get('node_type') == 'regulatory_framework':
                        linked_frameworks.append({
                            'framework': framework,
                            'edge': edge
                        })
                
                return {
                    'status': 'success',
                    'sector': domain,
                    'frameworks': linked_frameworks,
                    'framework_count': len(linked_frameworks),
                    'timestamp': datetime.now().isoformat()
                }
            
            # If domain type is not recognized, try a generic search
            # Look for nodes with matching domain_uid attribute
            frameworks = self.db_manager.get_nodes_by_properties({
                'node_type': 'regulatory_framework',
                'domain_uid': domain_uid
            })
            
            return {
                'status': 'success',
                'domain': domain,
                'frameworks': frameworks,
                'framework_count': len(frameworks),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting regulatory landscape: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting regulatory landscape: {str(e)}",
                'domain_uid': domain_uid,
                'timestamp': datetime.now().isoformat()
            }