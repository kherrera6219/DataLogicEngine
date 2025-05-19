"""
UKG Axis 7: Compliance

This module implements the Compliance axis of the Universal Knowledge Graph (UKG) system.
The Compliance axis manages compliance requirements, standards, and
certification processes within the knowledge graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

class ComplianceManager:
    """
    Compliance Manager for the UKG System
    
    Responsible for managing Axis 7 (Compliance) functionality, including:
    - Compliance standard creation and management
    - Compliance requirement tracking
    - Control mapping across frameworks
    - Compliance assessment and certification
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Compliance Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Common compliance standard types
        self.standard_types = {
            "international": "International compliance standards (e.g., ISO standards)",
            "industry": "Industry-specific standards (e.g., PCI DSS)",
            "governmental": "Government-mandated compliance requirements",
            "sectoral": "Sector-specific standards",
            "organizational": "Organization-specific compliance requirements",
            "regional": "Regional standards (e.g., EU standards)",
            "local": "Local standards"
        }
        
        # Common control categories
        self.control_categories = {
            "administrative": "Administrative controls (policies, procedures)",
            "technical": "Technical controls (hardware/software measures)",
            "physical": "Physical controls (physical security measures)",
            "operational": "Operational controls (day-to-day operations)",
            "management": "Management controls (oversight and governance)"
        }
    
    def create_compliance_standard(self, standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new compliance standard in the system.
        
        Args:
            standard_data: Standard data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating compliance standard: {standard_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure standard has required fields
            required_fields = ['label', 'standard_type', 'issuing_authority']
            for field in required_fields:
                if field not in standard_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Validate standard type
            if standard_data['standard_type'] not in self.standard_types:
                return {
                    'status': 'warning',
                    'message': f'Uncommon standard type: {standard_data["standard_type"]}',
                    'valid_types': list(self.standard_types.keys()),
                    'proceeding_with_custom_type': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in standard_data:
                standard_type = standard_data['standard_type']
                issuing_authority = standard_data['issuing_authority'].lower().replace(' ', '_')[:15]
                label_snippet = standard_data['label'].lower().replace(' ', '_')[:15]
                standard_data['uid'] = f"compliance_{standard_type}_{issuing_authority}_{label_snippet}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Compliance axis
            standard_data['axis_number'] = 7
            standard_data['node_type'] = 'compliance_standard'
            
            # Set effective dates if provided
            if 'effective_date' in standard_data:
                if isinstance(standard_data['effective_date'], datetime):
                    standard_data['effective_date'] = standard_data['effective_date'].isoformat()
            
            if 'expiration_date' in standard_data:
                if isinstance(standard_data['expiration_date'], datetime):
                    standard_data['expiration_date'] = standard_data['expiration_date'].isoformat()
            
            # Set version if not provided
            if 'version' not in standard_data:
                standard_data['version'] = '1.0'
            
            # Add standard to database
            new_standard = self.db_manager.add_node(standard_data)
            
            # If there's a related regulatory framework, link to it
            if 'related_regulatory_framework_uid' in standard_data:
                framework_uid = standard_data['related_regulatory_framework_uid']
                framework = self.db_manager.get_node(framework_uid)
                
                if framework and framework.get('node_type') == 'regulatory_framework':
                    edge_data = {
                        'uid': f"edge_{uuid.uuid4()}",
                        'source_id': framework_uid,
                        'target_id': new_standard['uid'],
                        'edge_type': 'implemented_by_standard',
                        'attributes': {}
                    }
                    
                    self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'standard': new_standard,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating compliance standard: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating compliance standard: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def create_compliance_control(self, control_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new compliance control in the system.
        
        Args:
            control_data: Control data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating compliance control: {control_data.get('label', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure control has required fields
            required_fields = ['label', 'standard_uid', 'control_category', 'description']
            for field in required_fields:
                if field not in control_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Verify standard exists
            standard_uid = control_data['standard_uid']
            standard = self.db_manager.get_node(standard_uid)
            
            if not standard or standard.get('node_type') != 'compliance_standard':
                return {
                    'status': 'error',
                    'message': 'Invalid standard UID',
                    'standard_uid': standard_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate control category
            if control_data['control_category'] not in self.control_categories:
                return {
                    'status': 'warning',
                    'message': f'Uncommon control category: {control_data["control_category"]}',
                    'valid_categories': list(self.control_categories.keys()),
                    'proceeding_with_custom_category': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in control_data:
                # Extract standard prefix from standard UID for better identification
                standard_prefix = standard_uid.split('_')[1] if len(standard_uid.split('_')) > 1 else 'std'
                control_id = control_data.get('control_id', '').lower().replace(' ', '_')
                if not control_id:
                    control_id = control_data['label'].lower().replace(' ', '_')[:15]
                control_data['uid'] = f"control_{standard_prefix}_{control_id}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Compliance axis
            control_data['axis_number'] = 7
            control_data['node_type'] = 'compliance_control'
            
            # Set implementation level if not provided
            if 'implementation_level' not in control_data:
                control_data['implementation_level'] = 'standard'  # Options: basic, standard, enhanced
            
            # Add control to database
            new_control = self.db_manager.add_node(control_data)
            
            # Link control to standard
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': standard_uid,
                'target_id': new_control['uid'],
                'edge_type': 'has_control',
                'attributes': {}
            }
            
            self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'control': new_control,
                'standard': standard,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating compliance control: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating compliance control: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def map_control_to_control(self, source_uid: str, target_uid: str, 
                             relation_type: str, 
                             attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map a relationship between compliance controls.
        
        Args:
            source_uid: Source control UID
            target_uid: Target control UID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing mapping result
        """
        self.logging.info(f"[{datetime.now()}] Mapping control to control: {source_uid} -> {target_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify controls exist
            source = self.db_manager.get_node(source_uid)
            target = self.db_manager.get_node(target_uid)
            
            if not source or source.get('node_type') != 'compliance_control':
                return {
                    'status': 'error',
                    'message': 'Invalid source control UID',
                    'source_uid': source_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not target or target.get('node_type') != 'compliance_control':
                return {
                    'status': 'error',
                    'message': 'Invalid target control UID',
                    'target_uid': target_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate relation type - common relationships between controls
            valid_relation_types = [
                'equivalent_to', 'similar_to', 'subset_of', 'superset_of', 
                'conflicts_with', 'depends_on', 'related_to'
            ]
            
            if relation_type not in valid_relation_types:
                return {
                    'status': 'warning',
                    'message': f'Uncommon relation type: {relation_type}',
                    'suggested_types': valid_relation_types,
                    'proceeding_with_custom_type': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if mapping already exists
            existing_edges = self.db_manager.get_edges_between(source_uid, target_uid, [relation_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Mapping already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create mapping
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
                'equivalent_to': 'equivalent_to',  # Symmetric relation
                'subset_of': 'superset_of',
                'superset_of': 'subset_of',
                'depends_on': 'required_by',
                'similar_to': 'similar_to'  # Symmetric relation
            }
            
            if relation_type in inverse_relations:
                inverse_type = inverse_relations[relation_type]
                # Skip if the relation is symmetric and already created
                if relation_type == inverse_type:
                    return {
                        'status': 'success',
                        'edge': new_edge,
                        'source': source,
                        'target': target,
                        'timestamp': datetime.now().isoformat()
                    }
                
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
            self.logging.error(f"[{datetime.now()}] Error mapping control to control: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error mapping control to control: {str(e)}",
                'source_uid': source_uid,
                'target_uid': target_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def link_control_to_regulatory_requirement(self, control_uid: str, 
                                            requirement_uid: str,
                                            relation_type: str = 'implements',
                                            attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Link a compliance control to a regulatory requirement.
        
        Args:
            control_uid: Control UID
            requirement_uid: Requirement UID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing link result
        """
        self.logging.info(f"[{datetime.now()}] Linking control to regulatory requirement: {control_uid} -> {requirement_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify control and requirement exist
            control = self.db_manager.get_node(control_uid)
            requirement = self.db_manager.get_node(requirement_uid)
            
            if not control or control.get('node_type') != 'compliance_control':
                return {
                    'status': 'error',
                    'message': 'Invalid control UID',
                    'control_uid': control_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not requirement or requirement.get('node_type') != 'regulatory_requirement':
                return {
                    'status': 'error',
                    'message': 'Invalid regulatory requirement UID',
                    'requirement_uid': requirement_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate relation type
            valid_relation_types = [
                'implements', 'addresses', 'supports', 'fulfills'
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
            existing_edges = self.db_manager.get_edges_between(control_uid, requirement_uid, [relation_type])
            
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
                'source_id': control_uid,
                'target_id': requirement_uid,
                'edge_type': relation_type,
                'attributes': attributes or {}
            }
            
            # Add edge to database
            new_edge = self.db_manager.add_edge(edge_data)
            
            # Create inverse link
            inverse_relations = {
                'implements': 'implemented_by',
                'addresses': 'addressed_by',
                'supports': 'supported_by',
                'fulfills': 'fulfilled_by'
            }
            
            if relation_type in inverse_relations:
                inverse_type = inverse_relations[relation_type]
                # Check if inverse relation already exists
                existing_inverse = self.db_manager.get_edges_between(requirement_uid, control_uid, [inverse_type])
                
                if not existing_inverse:
                    inverse_edge_data = {
                        'uid': f"edge_{uuid.uuid4()}",
                        'source_id': requirement_uid,
                        'target_id': control_uid,
                        'edge_type': inverse_type,
                        'attributes': attributes or {}
                    }
                    self.db_manager.add_edge(inverse_edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'control': control,
                'requirement': requirement,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking control to regulatory requirement: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking control to regulatory requirement: {str(e)}",
                'control_uid': control_uid,
                'requirement_uid': requirement_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_compliance_assessment(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a compliance assessment record.
        
        Args:
            assessment_data: Assessment data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating compliance assessment for standard: {assessment_data.get('standard_uid', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure assessment has required fields
            required_fields = ['standard_uid', 'entity_name', 'status']
            for field in required_fields:
                if field not in assessment_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Verify standard exists
            standard_uid = assessment_data['standard_uid']
            standard = self.db_manager.get_node(standard_uid)
            
            if not standard or standard.get('node_type') != 'compliance_standard':
                return {
                    'status': 'error',
                    'message': 'Invalid standard UID',
                    'standard_uid': standard_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate assessment status
            valid_statuses = [
                'planned', 'in_progress', 'completed', 'certified', 'failed', 'expired'
            ]
            
            if assessment_data['status'] not in valid_statuses:
                return {
                    'status': 'warning',
                    'message': f'Uncommon assessment status: {assessment_data["status"]}',
                    'valid_statuses': valid_statuses,
                    'proceeding_with_custom_status': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in assessment_data:
                standard_prefix = standard_uid.split('_')[1] if len(standard_uid.split('_')) > 1 else 'std'
                entity_snippet = assessment_data['entity_name'].lower().replace(' ', '_')[:15]
                assessment_data['uid'] = f"assessment_{standard_prefix}_{entity_snippet}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Compliance axis
            assessment_data['axis_number'] = 7
            assessment_data['node_type'] = 'compliance_assessment'
            
            # Set timestamps
            assessment_data['created_at'] = datetime.now().isoformat()
            
            if 'assessment_date' not in assessment_data:
                assessment_data['assessment_date'] = datetime.now().isoformat()
            
            if 'expiration_date' in assessment_data:
                if isinstance(assessment_data['expiration_date'], datetime):
                    assessment_data['expiration_date'] = assessment_data['expiration_date'].isoformat()
            
            # Add assessment to database
            new_assessment = self.db_manager.add_node(assessment_data)
            
            # Link assessment to standard
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': standard_uid,
                'target_id': new_assessment['uid'],
                'edge_type': 'has_assessment',
                'attributes': {}
            }
            
            self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'assessment': new_assessment,
                'standard': standard,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating compliance assessment: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating compliance assessment: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def add_assessment_result(self, assessment_uid: str, 
                           control_uid: str, 
                           result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a control result to a compliance assessment.
        
        Args:
            assessment_uid: Assessment UID
            control_uid: Control UID
            result_data: Result data dictionary
            
        Returns:
            Dict containing addition result
        """
        self.logging.info(f"[{datetime.now()}] Adding assessment result for control: {control_uid} to assessment: {assessment_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify assessment and control exist
            assessment = self.db_manager.get_node(assessment_uid)
            control = self.db_manager.get_node(control_uid)
            
            if not assessment or assessment.get('node_type') != 'compliance_assessment':
                return {
                    'status': 'error',
                    'message': 'Invalid assessment UID',
                    'assessment_uid': assessment_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            if not control or control.get('node_type') != 'compliance_control':
                return {
                    'status': 'error',
                    'message': 'Invalid control UID',
                    'control_uid': control_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure result has required fields
            required_fields = ['status', 'details']
            for field in required_fields:
                if field not in result_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field in result data: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Validate result status
            valid_statuses = [
                'compliant', 'non_compliant', 'partially_compliant', 
                'not_applicable', 'not_assessed'
            ]
            
            if result_data['status'] not in valid_statuses:
                return {
                    'status': 'warning',
                    'message': f'Uncommon result status: {result_data["status"]}',
                    'valid_statuses': valid_statuses,
                    'proceeding_with_custom_status': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in result_data:
                assessment_prefix = assessment_uid.split('_')[1] if len(assessment_uid.split('_')) > 1 else 'assess'
                control_prefix = control_uid.split('_')[1] if len(control_uid.split('_')) > 1 else 'ctrl'
                result_data['uid'] = f"result_{assessment_prefix}_{control_prefix}_{uuid.uuid4().hex[:8]}"
            
            # Set axis number for Compliance axis
            result_data['axis_number'] = 7
            result_data['node_type'] = 'compliance_result'
            result_data['assessment_uid'] = assessment_uid
            result_data['control_uid'] = control_uid
            
            # Set timestamp
            result_data['created_at'] = datetime.now().isoformat()
            
            # Add result to database
            new_result = self.db_manager.add_node(result_data)
            
            # Link result to assessment
            assessment_edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': assessment_uid,
                'target_id': new_result['uid'],
                'edge_type': 'has_result',
                'attributes': {}
            }
            
            self.db_manager.add_edge(assessment_edge_data)
            
            # Link result to control
            control_edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': control_uid,
                'target_id': new_result['uid'],
                'edge_type': 'assessed_as',
                'attributes': {}
            }
            
            self.db_manager.add_edge(control_edge_data)
            
            return {
                'status': 'success',
                'result': new_result,
                'assessment': assessment,
                'control': control,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error adding assessment result: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error adding assessment result: {str(e)}",
                'assessment_uid': assessment_uid,
                'control_uid': control_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_standard_details(self, standard_uid: str, 
                          include_controls: bool = True,
                          include_assessments: bool = False) -> Dict[str, Any]:
        """
        Get detailed information about a compliance standard.
        
        Args:
            standard_uid: Standard UID
            include_controls: Whether to include controls
            include_assessments: Whether to include assessments
            
        Returns:
            Dict containing standard details
        """
        self.logging.info(f"[{datetime.now()}] Getting details for standard: {standard_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get standard
            standard = self.db_manager.get_node(standard_uid)
            
            if not standard or standard.get('node_type') != 'compliance_standard':
                return {
                    'status': 'error',
                    'message': 'Invalid standard UID',
                    'standard_uid': standard_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            result = {
                'status': 'success',
                'standard': standard,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get controls if requested
            if include_controls:
                # Get edges connecting to controls
                control_edges = self.db_manager.get_outgoing_edges(standard_uid, ['has_control'])
                controls = []
                
                for edge in control_edges:
                    control = self.db_manager.get_node(edge['target_id'])
                    if control and control.get('node_type') == 'compliance_control':
                        controls.append({
                            'control': control,
                            'edge': edge
                        })
                
                result['controls'] = controls
                result['control_count'] = len(controls)
            
            # Get assessments if requested
            if include_assessments:
                # Get edges connecting to assessments
                assessment_edges = self.db_manager.get_outgoing_edges(standard_uid, ['has_assessment'])
                assessments = []
                
                for edge in assessment_edges:
                    assessment = self.db_manager.get_node(edge['target_id'])
                    if assessment and assessment.get('node_type') == 'compliance_assessment':
                        assessments.append({
                            'assessment': assessment,
                            'edge': edge
                        })
                
                result['assessments'] = assessments
                result['assessment_count'] = len(assessments)
            
            # Get related regulatory frameworks
            related_frameworks = []
            
            # Check for incoming edges from regulatory frameworks
            incoming_edges = self.db_manager.get_incoming_edges(standard_uid, ['implemented_by_standard'])
            for edge in incoming_edges:
                framework = self.db_manager.get_node(edge['source_id'])
                if framework and framework.get('node_type') == 'regulatory_framework':
                    related_frameworks.append({
                        'framework': framework,
                        'relation_type': 'implementing',
                        'edge': edge
                    })
            
            result['related_frameworks'] = related_frameworks
            result['related_framework_count'] = len(related_frameworks)
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting standard details: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting standard details: {str(e)}",
                'standard_uid': standard_uid,
                'timestamp': datetime.now().isoformat()
            }
    
    def find_equivalent_controls(self, control_uid: str, 
                               max_distance: int = 2) -> Dict[str, Any]:
        """
        Find equivalent or related controls across standards.
        
        Args:
            control_uid: Control UID
            max_distance: Maximum traversal distance
            
        Returns:
            Dict containing equivalent controls
        """
        self.logging.info(f"[{datetime.now()}] Finding equivalent controls for: {control_uid}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify control exists
            control = self.db_manager.get_node(control_uid)
            
            if not control or control.get('node_type') != 'compliance_control':
                return {
                    'status': 'error',
                    'message': 'Invalid control UID',
                    'control_uid': control_uid,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Define relationship types to traverse
            relation_types = [
                'equivalent_to', 'similar_to', 'subset_of', 'superset_of'
            ]
            
            equivalent_controls = []
            visited = set([control_uid])
            current_level = [{'node_uid': control_uid, 'distance': 0, 'path': []}]
            
            for distance in range(1, max_distance + 1):
                next_level = []
                
                for item in current_level:
                    node_uid = item['node_uid']
                    current_path = item['path'].copy()
                    
                    # Get outgoing relationships
                    outgoing = self.db_manager.get_outgoing_edges(node_uid, relation_types)
                    for edge in outgoing:
                        target_uid = edge['target_id']
                        if target_uid not in visited:
                            target_node = self.db_manager.get_node(target_uid)
                            if target_node and target_node.get('node_type') == 'compliance_control':
                                visited.add(target_uid)
                                
                                # Get the standard this control belongs to
                                target_standard_uid = target_node.get('standard_uid')
                                target_standard = None
                                if target_standard_uid:
                                    target_standard = self.db_manager.get_node(target_standard_uid)
                                
                                # Create path entry
                                path_entry = {
                                    'from': node_uid,
                                    'to': target_uid,
                                    'relation': edge['edge_type'],
                                    'attributes': edge.get('attributes', {})
                                }
                                
                                new_path = current_path + [path_entry]
                                
                                equivalent_controls.append({
                                    'control': target_node,
                                    'standard': target_standard,
                                    'relation_type': edge['edge_type'],
                                    'distance': distance,
                                    'path': new_path
                                })
                                
                                next_level.append({
                                    'node_uid': target_uid,
                                    'distance': distance,
                                    'path': new_path
                                })
                    
                    # Get incoming relationships
                    incoming = self.db_manager.get_incoming_edges(node_uid, relation_types)
                    for edge in incoming:
                        source_uid = edge['source_id']
                        if source_uid not in visited:
                            source_node = self.db_manager.get_node(source_uid)
                            if source_node and source_node.get('node_type') == 'compliance_control':
                                visited.add(source_uid)
                                
                                # Get the standard this control belongs to
                                source_standard_uid = source_node.get('standard_uid')
                                source_standard = None
                                if source_standard_uid:
                                    source_standard = self.db_manager.get_node(source_standard_uid)
                                
                                # Create path entry
                                path_entry = {
                                    'from': source_uid,
                                    'to': node_uid,
                                    'relation': edge['edge_type'],
                                    'attributes': edge.get('attributes', {})
                                }
                                
                                new_path = current_path + [path_entry]
                                
                                equivalent_controls.append({
                                    'control': source_node,
                                    'standard': source_standard,
                                    'relation_type': edge['edge_type'],
                                    'distance': distance,
                                    'path': new_path
                                })
                                
                                next_level.append({
                                    'node_uid': source_uid,
                                    'distance': distance,
                                    'path': new_path
                                })
                
                if not next_level:
                    break
                
                current_level = next_level
            
            # Get the standard this control belongs to
            standard_uid = control.get('standard_uid')
            standard = None
            if standard_uid:
                standard = self.db_manager.get_node(standard_uid)
            
            return {
                'status': 'success',
                'control': control,
                'standard': standard,
                'equivalent_controls': equivalent_controls,
                'equivalent_count': len(equivalent_controls),
                'max_distance': max_distance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding equivalent controls: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding equivalent controls: {str(e)}",
                'control_uid': control_uid,
                'timestamp': datetime.now().isoformat()
            }
"""
UKG Axis 7: Compliance Standards

This module implements the Compliance Standards axis of the Universal Knowledge Graph (UKG) system,
using a spiderweb node structure with branch-style mappings.

The Spiderweb Node System represents how compliance standards branch out with:
- Mega compliance frameworks (central nodes)
- Large compliance standards (primary webs)
- Medium compliance standards (secondary connections)
- Small compliance requirements (tertiary branches)
- Granular compliance points (edge nodes)
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set

class ComplianceManager:
    """
    Compliance Manager for the UKG System
    
    Responsible for managing Axis 7 (Compliance Standards) functionality, including:
    - Compliance framework creation and management in spiderweb structure
    - Compliance requirement tracking and mapping
    - Cross-standard mapping
    - Compliance validation and crosswalking with Axis 6 (Regulatory)
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Compliance Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.logging = logging.getLogger(__name__)
        
        # Spiderweb node structure levels
        self.node_levels = {
            "mega": "Top-level compliance architecture (e.g., ISO Compliance System)",
            "large": "Major compliance framework (e.g., ISO 27001, NIST CSF)",
            "medium": "Specific compliance domain (e.g., ISO 27001 Sec 8, NIST CSF ID.AM)",
            "small": "Individual compliance control (e.g., ISO 27001 8.1.1, NIST CSF ID.AM-1)",
            "granular": "Detailed compliance requirements (e.g., specific implementation points)"
        }
        
        # Common compliance standard types
        self.standard_types = {
            "iso": "International Organization for Standardization",
            "nist": "National Institute of Standards and Technology",
            "pci": "Payment Card Industry",
            "hipaa": "Health Insurance Portability and Accountability Act",
            "gdpr": "General Data Protection Regulation",
            "cmmc": "Cybersecurity Maturity Model Certification",
            "fedramp": "Federal Risk and Authorization Management Program",
            "soc": "System and Organization Controls",
            "industry": "Industry-specific standards"
        }
    
    def register_compliance_standard(self, standard_data: Dict[str, Any], 
                                   parent_standard_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a compliance standard in the knowledge graph.
        
        Args:
            standard_data: Standard data dictionary
            parent_standard_id: Optional parent standard ID
            
        Returns:
            Dict containing registration result
        """
        self.logging.info(f"[{datetime.now()}] Registering compliance standard: {standard_data.get('label', 'Unlabeled')}")
        
        try:
            if not self.graph_manager:
                return {
                    'status': 'error',
                    'message': 'Graph manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure standard has required fields
            required_fields = ['label', 'standard_level', 'standard_type']
            for field in required_fields:
                if field not in standard_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Verify standard level
            if standard_data['standard_level'] not in self.node_levels:
                return {
                    'status': 'error',
                    'message': f'Invalid standard level: {standard_data["standard_level"]}. Must be one of {list(self.node_levels.keys())}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify standard type
            if standard_data['standard_type'] not in self.standard_types:
                return {
                    'status': 'error',
                    'message': f'Invalid standard type: {standard_data["standard_type"]}. Must be one of {list(self.standard_types.keys())}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in standard_data:
                standard_level = standard_data['standard_level']
                standard_type = standard_data['standard_type']
                label_part = standard_data['label'].lower().replace(' ', '_')[:10]
                standard_data['uid'] = f"compliance_{standard_level}_{standard_type}_{label_part}_{uuid.uuid4().hex[:8]}"
            
            # Set node type
            standard_data['node_type'] = 'compliance_standard'
            
            # Set axis number for Compliance (Axis 7)
            standard_data['axis_number'] = 7
            
            # Set creation timestamp
            if 'created_at' not in standard_data:
                standard_data['created_at'] = datetime.now().isoformat()
            
            # Check if standard with same properties already exists
            existing_standards = self.db_manager.get_nodes_by_properties({
                'node_type': 'compliance_standard',
                'standard_level': standard_data['standard_level'],
                'label': standard_data['label'],
                'standard_type': standard_data['standard_type']
            })
            
            if existing_standards:
                return {
                    'status': 'exists',
                    'message': 'Compliance standard already exists',
                    'standard': existing_standards[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add standard node
            new_standard = self.graph_manager.add_node(standard_data)
            
            if new_standard.get('status') != 'success':
                return new_standard
            
            new_standard_node = new_standard.get('node', {})
            
            # Connect to parent standard if provided
            if parent_standard_id:
                parent_nodes = self.db_manager.get_nodes_by_properties({
                    'id': parent_standard_id,
                    'node_type': 'compliance_standard'
                })
                
                if not parent_nodes:
                    return {
                        'status': 'error',
                        'message': f'Parent standard not found: {parent_standard_id}',
                        'standard': new_standard_node,  # Still return the created standard
                        'timestamp': datetime.now().isoformat()
                    }
                
                parent_node = parent_nodes[0]
                
                # Check parent-child standard level relationship
                parent_level = parent_node['standard_level']
                child_level = standard_data['standard_level']
                
                valid_parent_child = {
                    'mega': 'large',
                    'large': 'medium',
                    'medium': 'small',
                    'small': 'granular'
                }
                
                if parent_level in valid_parent_child and valid_parent_child[parent_level] == child_level:
                    # Valid parent-child relationship
                    parent_child_edge = {
                        'uid': f"edge_{uuid.uuid4()}",
                        'source_id': parent_node['uid'],
                        'target_id': new_standard_node['uid'],
                        'edge_type': 'has_standard',
                        'attributes': {
                            'parent_level': parent_level,
                            'child_level': child_level
                        }
                    }
                    
                    edge_result = self.graph_manager.add_edge(parent_child_edge)
                    
                    if edge_result.get('status') != 'success':
                        return {
                            'status': 'warning',
                            'message': f'Standard created but parent connection failed: {edge_result.get("message")}',
                            'standard': new_standard_node,
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    return {
                        'status': 'error',
                        'message': f'Invalid parent-child standard level relationship. Parent {parent_level} cannot have child {child_level}',
                        'standard': new_standard_node,  # Still return the created standard
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {
                'status': 'success',
                'standard': new_standard_node,
                'parent_standard_id': parent_standard_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error registering compliance standard: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error registering compliance standard: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_compliance_hierarchy(self, standard_type: str = None) -> Dict[str, Any]:
        """
        Get the compliance standard hierarchy, optionally filtered by standard type.
        
        Args:
            standard_type: Optional standard type to filter by (e.g., 'iso', 'nist')
            
        Returns:
            Dict containing the standard hierarchy
        """
        self.logging.info(f"[{datetime.now()}] Getting compliance hierarchy for type: {standard_type or 'all'}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Build query properties
            query_props = {'node_type': 'compliance_standard'}
            if standard_type:
                query_props['standard_type'] = standard_type
            
            # Get mega standards (top level)
            mega_standards = {}
            mega_standard_nodes = self.db_manager.get_nodes_by_properties({
                **query_props,
                'standard_level': 'mega'
            })
            
            for mega_standard in mega_standard_nodes:
                mega_standard_id = mega_standard.get('id')
                
                if mega_standard_id:
                    mega_standards[mega_standard_id] = {
                        'standard': mega_standard,
                        'large_standards': {}
                    }
                    
                    # Get large standards for mega standard
                    large_standards = self._get_child_standards(mega_standard['uid'], 'large')
                    
                    for large_standard_id, large_standard_data in large_standards.items():
                        mega_standards[mega_standard_id]['large_standards'][large_standard_id] = large_standard_data
                        
                        # Get medium standards for large standard
                        medium_standards = self._get_child_standards(large_standard_data['standard']['uid'], 'medium')
                        large_standard_data['medium_standards'] = medium_standards
                        
                        # Get small standards for each medium standard
                        for medium_standard_id, medium_standard_data in medium_standards.items():
                            small_standards = self._get_child_standards(medium_standard_data['standard']['uid'], 'small')
                            medium_standard_data['small_standards'] = small_standards
                            
                            # Get granular standards for each small standard
                            for small_standard_id, small_standard_data in small_standards.items():
                                granular_standards = self._get_child_standards(small_standard_data['standard']['uid'], 'granular')
                                small_standard_data['granular_standards'] = granular_standards
            
            return {
                'status': 'success',
                'standard_type': standard_type or 'all',
                'hierarchy': mega_standards,
                'total_standards': len(mega_standard_nodes),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting compliance hierarchy: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting compliance hierarchy: {str(e)}",
                'standard_type': standard_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_child_standards(self, parent_uid: str, standard_level: str) -> Dict[str, Dict[str, Any]]:
        """
        Get child standards of a specific level for a parent node.
        
        Args:
            parent_uid: Parent node UID
            standard_level: Standard level to retrieve
            
        Returns:
            Dict mapping standard IDs to standard data
        """
        child_standards = {}
        
        # Get outgoing edges of type 'has_standard'
        outgoing_edges = self.db_manager.get_outgoing_edges(parent_uid, ['has_standard'])
        
        for edge in outgoing_edges:
            target_uid = edge['target_id']
            target_node = self.db_manager.get_node(target_uid)
            
            if target_node and target_node.get('node_type') == 'compliance_standard' and target_node.get('standard_level') == standard_level:
                standard_id = target_node.get('id')
                
                if standard_id:
                    child_standards[standard_id] = {
                        'standard': target_node,
                        'edge': edge
                    }
        
        return child_standards
    
    def map_regulatory_to_compliance(self, regulatory_uid: str, compliance_uid: str, 
                                   relationship_type: str = 'implements',
                                   confidence: float = 0.9) -> Dict[str, Any]:
        """
        Map a regulatory framework element to a compliance standard element.
        
        Args:
            regulatory_uid: UID of the regulatory framework node
            compliance_uid: UID of the compliance standard node
            relationship_type: Type of relationship (e.g., 'implements', 'related_to')
            confidence: Confidence level of the mapping (0.0 to 1.0)
            
        Returns:
            Dict containing the mapping result
        """
        self.logging.info(f"[{datetime.now()}] Mapping regulatory {regulatory_uid} to compliance {compliance_uid}")
        
        try:
            if not self.graph_manager:
                return {
                    'status': 'error',
                    'message': 'Graph manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify nodes exist
            regulatory_node = self.db_manager.get_node(regulatory_uid)
            compliance_node = self.db_manager.get_node(compliance_uid)
            
            if not regulatory_node:
                return {
                    'status': 'error',
                    'message': f'Regulatory node not found: {regulatory_uid}',
                    'timestamp': datetime.now().isoformat()
                }
            
            if not compliance_node:
                return {
                    'status': 'error',
                    'message': f'Compliance node not found: {compliance_uid}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify node types
            if regulatory_node.get('node_type') != 'regulatory_framework':
                return {
                    'status': 'error',
                    'message': f'Node {regulatory_uid} is not a regulatory framework',
                    'timestamp': datetime.now().isoformat()
                }
            
            if compliance_node.get('node_type') != 'compliance_standard':
                return {
                    'status': 'error',
                    'message': f'Node {compliance_uid} is not a compliance standard',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if edge already exists
            existing_edges = self.db_manager.get_edges_between(regulatory_uid, compliance_uid)
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Mapping already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create the edge
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': regulatory_uid,
                'target_id': compliance_uid,
                'edge_type': relationship_type,
                'attributes': {
                    'confidence': confidence,
                    'mapped_at': datetime.now().isoformat(),
                    'source_type': 'regulatory_framework',
                    'target_type': 'compliance_standard',
                    'source_level': regulatory_node.get('framework_level'),
                    'target_level': compliance_node.get('standard_level')
                }
            }
            
            edge_result = self.graph_manager.add_edge(edge_data)
            
            return edge_result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error mapping regulatory to compliance: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error mapping regulatory to compliance: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def find_compliance_for_sector(self, sector_id: str, 
                                 standard_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Find compliance standards relevant to a specific sector.
        
        Args:
            sector_id: Sector ID
            standard_type: Optional standard type to filter by
            
        Returns:
            Dict containing the relevant compliance standards
        """
        self.logging.info(f"[{datetime.now()}] Finding compliance for sector: {sector_id}, type: {standard_type or 'all'}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get sector
            sector_nodes = self.db_manager.get_nodes_by_properties({'id': sector_id, 'node_type': 'sector'})
            
            if not sector_nodes:
                return {
                    'status': 'error',
                    'message': f'Sector not found: {sector_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            sector_node = sector_nodes[0]
            sector_uid = sector_node.get('uid')
            
            # Find compliance standards
            compliance_standards = []
            
            # Method 1: Direct connections from sector to compliance
            direct_edges = self.db_manager.get_outgoing_edges(sector_uid, ['applies_to_sector', 'complies_with'])
            
            for edge in direct_edges:
                target_uid = edge['target_id']
                compliance_node = self.db_manager.get_node(target_uid)
                
                if compliance_node and compliance_node.get('node_type') == 'compliance_standard':
                    if standard_type and compliance_node.get('standard_type') != standard_type:
                        continue
                        
                    compliance_standards.append({
                        'standard': compliance_node,
                        'connection': 'direct',
                        'edge': edge,
                        'confidence': edge.get('attributes', {}).get('confidence', 0.9)
                    })
            
            # Method 2: Find compliance via regulatory frameworks
            # First get regulatory frameworks for the sector
            reg_edges = self.db_manager.get_outgoing_edges(sector_uid, ['regulated_by'])
            
            for reg_edge in reg_edges:
                reg_uid = reg_edge['target_id']
                reg_node = self.db_manager.get_node(reg_uid)
                
                if reg_node and reg_node.get('node_type') == 'regulatory_framework':
                    # Then find compliance standards that implement these regulations
                    impl_edges = self.db_manager.get_outgoing_edges(reg_uid, ['implements'])
                    
                    for impl_edge in impl_edges:
                        comp_uid = impl_edge['target_id']
                        comp_node = self.db_manager.get_node(comp_uid)
                        
                        if comp_node and comp_node.get('node_type') == 'compliance_standard':
                            if standard_type and comp_node.get('standard_type') != standard_type:
                                continue
                                
                            compliance_standards.append({
                                'standard': comp_node,
                                'connection': 'via_regulation',
                                'regulation': reg_node,
                                'confidence': impl_edge.get('attributes', {}).get('confidence', 0.8)
                            })
            
            # Method 3: Find compliance via industry classification
            # This would be a more advanced implementation leveraging the classification codes
            
            # Remove duplicates (same standard might appear multiple times via different paths)
            unique_standards = {}
            for cs in compliance_standards:
                standard_uid = cs['standard'].get('uid')
                if standard_uid not in unique_standards or cs['confidence'] > unique_standards[standard_uid]['confidence']:
                    unique_standards[standard_uid] = cs
            
            return {
                'status': 'success',
                'sector': sector_node,
                'standard_type': standard_type or 'all',
                'standards': list(unique_standards.values()),
                'standard_count': len(unique_standards),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error finding compliance for sector: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error finding compliance for sector: {str(e)}",
                'sector_id': sector_id,
                'timestamp': datetime.now().isoformat()
            }
