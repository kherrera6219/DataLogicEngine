"""
UKG Axis 1: Knowledge

This module implements the Knowledge axis of the Universal Knowledge Graph (UKG) system.
The Knowledge axis handles the Pillar Levels (PL1-PL100) structure that forms the 
foundation of knowledge organization within the UKG.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

class KnowledgeManager:
    """
    Knowledge Manager for the UKG System
    
    Responsible for managing Axis 1 (Knowledge) functionality, including:
    - Managing Pillar Levels (PL1-PL100)
    - Creating and managing sublevels within pillars
    - Cross-pillar connections and knowledge organization
    - Domain expertise mapping across pillars
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
        
        # Initialize pillar level definitions
        self.pillar_levels = self._initialize_pillar_levels()
    
    def _initialize_pillar_levels(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize the dictionary of all Pillar Levels (PL1-PL100).
        
        Returns:
            Dictionary of pillar level definitions
        """
        # This would typically come from a database or configuration file
        # For demonstration, creating a simplified structure with just a few examples
        
        pillar_levels = {}
        
        # Example Pillar Levels based on files provided
        pillar_levels["PL01"] = {
            "id": "PL01",
            "name": "U.S. Government Regulatory Systems",
            "description": "Core government regulatory frameworks and legal systems",
            "sublevels": {
                "1": "Federal Regulations",
                "2": "State Regulations",
                "3": "Local Government Codes",
                "4": "Regulatory Authorities"
            }
        }
        
        pillar_levels["PL02"] = {
            "id": "PL02",
            "name": "Physical Sciences",
            "description": "Core physical science disciplines and applied research",
            "sublevels": {
                "1": "Physics",
                "1.1": "Astrophysics",
                "1.1.1": "Space Propulsion",
                "2": "Chemistry", 
                "3": "Earth Sciences",
                "4": "Materials Science"
            }
        }
        
        pillar_levels["PL04"] = {
            "id": "PL04",
            "name": "Contracting & Procurement Sciences",
            "description": "Government and private sector acquisition methodologies",
            "sublevels": {
                "1": "Contract Types",
                "2": "Procurement Procedures",
                "3": "Source Selection",
                "4": "Contract Administration"
            }
        }
        
        pillar_levels["PL05"] = {
            "id": "PL05",
            "name": "Healthcare Sciences",
            "description": "Medical disciplines, healthcare administration, and clinical practices",
            "sublevels": {
                "1": "Clinical Medicine",
                "2": "Healthcare Administration",
                "3": "Public Health",
                "4": "Medical Research"
            }
        }
        
        pillar_levels["PL07"] = {
            "id": "PL07",
            "name": "Data Privacy & Security",
            "description": "Information security, privacy frameworks, and protection methods",
            "sublevels": {
                "1": "Data Protection Frameworks",
                "2": "Information Security",
                "3": "Privacy Engineering",
                "4": "Compliance Management"
            }
        }
        
        pillar_levels["PL20"] = {
            "id": "PL20",
            "name": "Legal Frameworks",
            "description": "Legal disciplines, practices, and specializations",
            "sublevels": {
                "1": "Constitutional Law",
                "2": "Administrative Law",
                "3": "Contract Law",
                "3.2": "Government Contracting",
                "3.2.1": "FAR-Based Contracting",
                "4": "Criminal Law"
            }
        }
        
        pillar_levels["PL48"] = {
            "id": "PL48",
            "name": "Public Policy and Federal Governance",
            "description": "Government policy development and implementation methods",
            "sublevels": {
                "1": "Policy Analysis",
                "2": "Federal Budget Process",
                "3": "Agency Rulemaking",
                "4": "Legislative Process"
            }
        }
        
        pillar_levels["PL87"] = {
            "id": "PL87",
            "name": "Cybersecurity Law",
            "description": "Legal frameworks governing digital security and cyber operations",
            "sublevels": {
                "1": "Data Breach Notification Laws",
                "2": "Critical Infrastructure Protection",
                "3": "International Cyber Law",
                "4": "Digital Privacy Laws"
            }
        }
        
        # Populate remaining pillars with placeholder information
        for i in range(1, 101):
            pl_id = f"PL{i:02d}"
            if pl_id not in pillar_levels:
                pillar_levels[pl_id] = {
                    "id": pl_id,
                    "name": f"Pillar Level {i}",
                    "description": f"Domain knowledge area {i}",
                    "sublevels": {}
                }
        
        return pillar_levels
    
    def get_pillar_level(self, pillar_id: str) -> Dict[str, Any]:
        """
        Get information about a specific Pillar Level.
        
        Args:
            pillar_id: Pillar Level ID (e.g., "PL01", "PL87")
            
        Returns:
            Dict containing pillar level information
        """
        self.logging.info(f"[{datetime.now()}] Getting Pillar Level: {pillar_id}")
        
        try:
            # Check if pillar exists in internal dictionary
            if pillar_id in self.pillar_levels:
                return {
                    'status': 'success',
                    'pillar': self.pillar_levels[pillar_id],
                    'timestamp': datetime.now().isoformat()
                }
            
            # If not found in internal dictionary, check database
            if self.db_manager:
                pillar_node = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_level',
                    'pillar_id': pillar_id
                })
                
                if pillar_node:
                    return {
                        'status': 'success',
                        'pillar': pillar_node[0],
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Not found in dictionary or database
            return {
                'status': 'not_found',
                'message': f'Pillar Level {pillar_id} not found',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting Pillar Level: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting Pillar Level: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_all_pillar_levels(self) -> Dict[str, Any]:
        """
        Get a list of all Pillar Levels.
        
        Returns:
            Dict containing list of pillar levels
        """
        self.logging.info(f"[{datetime.now()}] Getting all Pillar Levels")
        
        try:
            # Combine internal dictionary with database entries
            pillars = list(self.pillar_levels.values())
            
            # If database is available, fetch additional entries
            if self.db_manager:
                db_pillars = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_level'
                })
                
                # Merge with internal dictionary, avoiding duplicates
                existing_ids = set(p['id'] for p in pillars)
                for db_pillar in db_pillars:
                    if db_pillar.get('pillar_id') not in existing_ids:
                        pillars.append(db_pillar)
            
            return {
                'status': 'success',
                'pillars': pillars,
                'pillar_count': len(pillars),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting all Pillar Levels: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting all Pillar Levels: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def create_pillar_level(self, pillar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Pillar Level in the system.
        
        Args:
            pillar_data: Pillar level data dictionary
            
        Returns:
            Dict containing creation result
        """
        self.logging.info(f"[{datetime.now()}] Creating Pillar Level: {pillar_data.get('id', 'Unknown')}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Ensure pillar has required fields
            required_fields = ['id', 'name', 'description']
            for field in required_fields:
                if field not in pillar_data:
                    return {
                        'status': 'error',
                        'message': f'Missing required field: {field}',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Check if pillar already exists
            pillar_id = pillar_data['id']
            if pillar_id in self.pillar_levels:
                return {
                    'status': 'exists',
                    'message': f'Pillar Level {pillar_id} already exists',
                    'pillar': self.pillar_levels[pillar_id],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if pillar exists in database
            existing_pillar = self.db_manager.get_nodes_by_properties({
                'node_type': 'pillar_level',
                'pillar_id': pillar_id
            })
            
            if existing_pillar:
                return {
                    'status': 'exists',
                    'message': f'Pillar Level {pillar_id} already exists in database',
                    'pillar': existing_pillar[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Generate UID if not provided
            if 'uid' not in pillar_data:
                pillar_data['uid'] = f"pillar_level_{pillar_id}_{uuid.uuid4().hex[:8]}"
            
            # Set node type and axis number
            pillar_data['node_type'] = 'pillar_level'
            pillar_data['axis_number'] = 1
            
            # Ensure sublevels is a dictionary
            if 'sublevels' not in pillar_data:
                pillar_data['sublevels'] = {}
            
            # Add pillar to database
            new_pillar = self.db_manager.add_node(pillar_data)
            
            # Add to internal dictionary
            self.pillar_levels[pillar_id] = {
                'id': pillar_id,
                'name': pillar_data['name'],
                'description': pillar_data['description'],
                'sublevels': pillar_data.get('sublevels', {})
            }
            
            return {
                'status': 'success',
                'pillar': new_pillar,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error creating Pillar Level: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating Pillar Level: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def add_sublevel(self, pillar_id: str, sublevel_id: str, sublevel_name: str, 
                   parent_sublevel_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a sublevel to a Pillar Level.
        
        Args:
            pillar_id: Pillar Level ID (e.g., "PL01")
            sublevel_id: Sublevel ID (e.g., "1", "1.1", "1.1.1")
            sublevel_name: Name of the sublevel
            parent_sublevel_id: Optional parent sublevel ID
            
        Returns:
            Dict containing addition result
        """
        self.logging.info(f"[{datetime.now()}] Adding sublevel {sublevel_id} to {pillar_id}")
        
        try:
            # Check if pillar exists
            pillar_result = self.get_pillar_level(pillar_id)
            
            if pillar_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f'Pillar Level {pillar_id} not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            pillar = pillar_result['pillar']
            
            # Check if sublevel already exists
            if 'sublevels' in pillar and sublevel_id in pillar['sublevels']:
                return {
                    'status': 'exists',
                    'message': f'Sublevel {sublevel_id} already exists in {pillar_id}',
                    'sublevel': {
                        'id': sublevel_id,
                        'name': pillar['sublevels'][sublevel_id]
                    },
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if parent sublevel exists if specified
            if parent_sublevel_id and (
                'sublevels' not in pillar or 
                parent_sublevel_id not in pillar['sublevels']
            ):
                return {
                    'status': 'error',
                    'message': f'Parent sublevel {parent_sublevel_id} not found in {pillar_id}',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add sublevel to pillar
            if 'sublevels' not in pillar:
                pillar['sublevels'] = {}
            
            pillar['sublevels'][sublevel_id] = sublevel_name
            
            # Update internal dictionary
            self.pillar_levels[pillar_id]['sublevels'][sublevel_id] = sublevel_name
            
            # Update database if available
            if self.db_manager:
                # Find the pillar node in the database
                db_pillars = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_level',
                    'pillar_id': pillar_id
                })
                
                if db_pillars:
                    db_pillar = db_pillars[0]
                    db_pillar['sublevels'] = pillar['sublevels']
                    self.db_manager.update_node(db_pillar['uid'], db_pillar)
                else:
                    # Create pillar node if it doesn't exist in the database
                    pillar_node = {
                        'uid': f"pillar_level_{pillar_id}_{uuid.uuid4().hex[:8]}",
                        'node_type': 'pillar_level',
                        'axis_number': 1,
                        'pillar_id': pillar_id,
                        'name': pillar['name'],
                        'description': pillar.get('description', ''),
                        'sublevels': pillar['sublevels']
                    }
                    self.db_manager.add_node(pillar_node)
                
                # Create a sublevel node
                sublevel_node = {
                    'uid': f"sublevel_{pillar_id}_{sublevel_id}_{uuid.uuid4().hex[:8]}",
                    'node_type': 'pillar_sublevel',
                    'axis_number': 1,
                    'pillar_id': pillar_id,
                    'sublevel_id': sublevel_id,
                    'name': sublevel_name,
                    'parent_sublevel_id': parent_sublevel_id
                }
                new_sublevel = self.db_manager.add_node(sublevel_node)
                
                # Create edge from pillar to sublevel
                edge_data = {
                    'uid': f"edge_{uuid.uuid4()}",
                    'source_id': f"pillar_level_{pillar_id}",
                    'target_id': new_sublevel['uid'],
                    'edge_type': 'has_sublevel',
                    'attributes': {}
                }
                self.db_manager.add_edge(edge_data)
                
                # Create edge from parent sublevel to child sublevel if applicable
                if parent_sublevel_id:
                    # Find parent sublevel node
                    parent_sublevels = self.db_manager.get_nodes_by_properties({
                        'node_type': 'pillar_sublevel',
                        'pillar_id': pillar_id,
                        'sublevel_id': parent_sublevel_id
                    })
                    
                    if parent_sublevels:
                        parent_edge_data = {
                            'uid': f"edge_{uuid.uuid4()}",
                            'source_id': parent_sublevels[0]['uid'],
                            'target_id': new_sublevel['uid'],
                            'edge_type': 'has_child_sublevel',
                            'attributes': {}
                        }
                        self.db_manager.add_edge(parent_edge_data)
            
            return {
                'status': 'success',
                'pillar_id': pillar_id,
                'sublevel': {
                    'id': sublevel_id,
                    'name': sublevel_name,
                    'parent_sublevel_id': parent_sublevel_id
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error adding sublevel: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error adding sublevel: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def link_pillars(self, source_pillar_id: str, target_pillar_id: str, 
                   relation_type: str, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a relationship between two Pillar Levels.
        
        Args:
            source_pillar_id: Source Pillar Level ID
            target_pillar_id: Target Pillar Level ID
            relation_type: Type of relationship
            attributes: Optional relationship attributes
            
        Returns:
            Dict containing created relationship
        """
        self.logging.info(f"[{datetime.now()}] Linking pillars: {source_pillar_id} -> {target_pillar_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify pillars exist
            source_result = self.get_pillar_level(source_pillar_id)
            target_result = self.get_pillar_level(target_pillar_id)
            
            if source_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f'Source Pillar Level {source_pillar_id} not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            if target_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f'Target Pillar Level {target_pillar_id} not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get database nodes for pillars
            source_nodes = self.db_manager.get_nodes_by_properties({
                'node_type': 'pillar_level',
                'pillar_id': source_pillar_id
            })
            
            target_nodes = self.db_manager.get_nodes_by_properties({
                'node_type': 'pillar_level',
                'pillar_id': target_pillar_id
            })
            
            if not source_nodes:
                # Create source pillar node
                source_pillar = source_result['pillar']
                source_node = {
                    'uid': f"pillar_level_{source_pillar_id}_{uuid.uuid4().hex[:8]}",
                    'node_type': 'pillar_level',
                    'axis_number': 1,
                    'pillar_id': source_pillar_id,
                    'name': source_pillar['name'],
                    'description': source_pillar.get('description', ''),
                    'sublevels': source_pillar.get('sublevels', {})
                }
                source_node = self.db_manager.add_node(source_node)
            else:
                source_node = source_nodes[0]
            
            if not target_nodes:
                # Create target pillar node
                target_pillar = target_result['pillar']
                target_node = {
                    'uid': f"pillar_level_{target_pillar_id}_{uuid.uuid4().hex[:8]}",
                    'node_type': 'pillar_level',
                    'axis_number': 1,
                    'pillar_id': target_pillar_id,
                    'name': target_pillar['name'],
                    'description': target_pillar.get('description', ''),
                    'sublevels': target_pillar.get('sublevels', {})
                }
                target_node = self.db_manager.add_node(target_node)
            else:
                target_node = target_nodes[0]
            
            # Check if relationship already exists
            existing_edges = self.db_manager.get_edges_between(source_node['uid'], target_node['uid'], [relation_type])
            
            if existing_edges:
                return {
                    'status': 'exists',
                    'message': 'Relationship already exists',
                    'edge': existing_edges[0],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create relationship
            edge_data = {
                'uid': f"edge_{uuid.uuid4()}",
                'source_id': source_node['uid'],
                'target_id': target_node['uid'],
                'edge_type': relation_type,
                'attributes': attributes or {}
            }
            
            new_edge = self.db_manager.add_edge(edge_data)
            
            return {
                'status': 'success',
                'edge': new_edge,
                'source_pillar': source_result['pillar'],
                'target_pillar': target_result['pillar'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error linking pillars: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error linking pillars: {str(e)}",
                'source_pillar_id': source_pillar_id,
                'target_pillar_id': target_pillar_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_pillar_structure(self, pillar_id: str, include_sublevels: bool = True) -> Dict[str, Any]:
        """
        Get the complete structure of a Pillar Level.
        
        Args:
            pillar_id: Pillar Level ID
            include_sublevels: Whether to include sublevel details
            
        Returns:
            Dict containing pillar structure
        """
        self.logging.info(f"[{datetime.now()}] Getting structure for Pillar Level: {pillar_id}")
        
        try:
            # Get pillar information
            pillar_result = self.get_pillar_level(pillar_id)
            
            if pillar_result['status'] != 'success':
                return pillar_result
            
            pillar = pillar_result['pillar']
            result = {
                'status': 'success',
                'pillar': pillar,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get sublevels if requested
            if include_sublevels and self.db_manager:
                # Query database for sublevel nodes
                sublevel_nodes = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_sublevel',
                    'pillar_id': pillar_id
                })
                
                # Build hierarchy of sublevels
                sublevels = {}
                for node in sublevel_nodes:
                    sublevel_id = node.get('sublevel_id')
                    if sublevel_id:
                        sublevels[sublevel_id] = {
                            'id': sublevel_id,
                            'name': node.get('name', ''),
                            'parent_id': node.get('parent_sublevel_id'),
                            'children': []
                        }
                
                # Build parent-child relationships
                root_sublevels = []
                for sublevel_id, sublevel in sublevels.items():
                    if sublevel['parent_id'] is None:
                        root_sublevels.append(sublevel)
                    elif sublevel['parent_id'] in sublevels:
                        sublevels[sublevel['parent_id']]['children'].append(sublevel)
                
                result['sublevel_hierarchy'] = root_sublevels
                result['all_sublevels'] = sublevels
            
            # Get connected pillars
            if self.db_manager:
                # Find the pillar node in the database
                db_pillars = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_level',
                    'pillar_id': pillar_id
                })
                
                connected_pillars = []
                
                if db_pillars:
                    db_pillar = db_pillars[0]
                    
                    # Get outgoing connections
                    outgoing_edges = self.db_manager.get_outgoing_edges(db_pillar['uid'])
                    for edge in outgoing_edges:
                        target_node = self.db_manager.get_node(edge['target_id'])
                        if target_node and target_node.get('node_type') == 'pillar_level':
                            connected_pillars.append({
                                'direction': 'outgoing',
                                'pillar_id': target_node.get('pillar_id'),
                                'name': target_node.get('name'),
                                'relation_type': edge.get('edge_type'),
                                'edge': edge
                            })
                    
                    # Get incoming connections
                    incoming_edges = self.db_manager.get_incoming_edges(db_pillar['uid'])
                    for edge in incoming_edges:
                        source_node = self.db_manager.get_node(edge['source_id'])
                        if source_node and source_node.get('node_type') == 'pillar_level':
                            connected_pillars.append({
                                'direction': 'incoming',
                                'pillar_id': source_node.get('pillar_id'),
                                'name': source_node.get('name'),
                                'relation_type': edge.get('edge_type'),
                                'edge': edge
                            })
                
                result['connected_pillars'] = connected_pillars
                result['connected_count'] = len(connected_pillars)
            
            return result
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting pillar structure: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting pillar structure: {str(e)}",
                'pillar_id': pillar_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_pillar_experts(self, pillar_id: str, sublevel_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get expert roles associated with a Pillar Level or sublevel.
        
        Args:
            pillar_id: Pillar Level ID
            sublevel_id: Optional sublevel ID to filter by
            
        Returns:
            Dict containing expert roles
        """
        self.logging.info(f"[{datetime.now()}] Getting experts for Pillar Level: {pillar_id}")
        
        try:
            if not self.db_manager:
                return {
                    'status': 'error',
                    'message': 'Database manager not available',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Verify pillar exists
            pillar_result = self.get_pillar_level(pillar_id)
            
            if pillar_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f'Pillar Level {pillar_id} not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get expert roles associated with pillar
            query_params = {
                'node_type': 'expert_role',
                'pillar_id': pillar_id
            }
            
            if sublevel_id:
                query_params['sublevel_id'] = sublevel_id
            
            expert_nodes = self.db_manager.get_nodes_by_properties(query_params)
            
            # For each expert, get associated education, certifications, skills, etc.
            experts = []
            for expert in expert_nodes:
                expert_uid = expert['uid']
                
                # Get outgoing edges for details
                outgoing_edges = self.db_manager.get_outgoing_edges(expert_uid)
                
                education = []
                certifications = []
                skills = []
                training = []
                research = []
                
                for edge in outgoing_edges:
                    if edge['edge_type'] == 'has_education':
                        education_node = self.db_manager.get_node(edge['target_id'])
                        if education_node:
                            education.append(education_node)
                    elif edge['edge_type'] == 'has_certification':
                        cert_node = self.db_manager.get_node(edge['target_id'])
                        if cert_node:
                            certifications.append(cert_node)
                    elif edge['edge_type'] == 'has_skill':
                        skill_node = self.db_manager.get_node(edge['target_id'])
                        if skill_node:
                            skills.append(skill_node)
                    elif edge['edge_type'] == 'has_training':
                        training_node = self.db_manager.get_node(edge['target_id'])
                        if training_node:
                            training.append(training_node)
                    elif edge['edge_type'] == 'has_research':
                        research_node = self.db_manager.get_node(edge['target_id'])
                        if research_node:
                            research.append(research_node)
                
                # Build complete expert profile
                expert_profile = {
                    'expert': expert,
                    'education': education,
                    'certifications': certifications,
                    'skills': skills,
                    'training': training,
                    'research': research
                }
                
                experts.append(expert_profile)
            
            return {
                'status': 'success',
                'pillar': pillar_result['pillar'],
                'sublevel_id': sublevel_id,
                'experts': experts,
                'expert_count': len(experts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logging.error(f"[{datetime.now()}] Error getting pillar experts: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error getting pillar experts: {str(e)}",
                'pillar_id': pillar_id,
                'timestamp': datetime.now().isoformat()
            }