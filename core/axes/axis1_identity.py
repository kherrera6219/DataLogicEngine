
"""
UKG Axis 1: Knowledge

This module implements the Knowledge axis of the Universal Knowledge Graph (UKG) system.
The Knowledge axis handles the Pillar Levels (PL1-PL100) structure that forms the 
foundation of knowledge organization within the UKG.
"""

import logging
import uuid
import yaml
import os
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
    
    def __init__(self, db_manager=None, graph_manager=None, config=None):
        """
        Initialize the Knowledge Manager.
        
        Args:
            db_manager: Database Manager instance
            graph_manager: Graph Manager instance
            config: Configuration settings
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize pillar level definitions
        self.pillar_levels = self._initialize_pillar_levels()
        
        # Initialize dynamic mapping storage
        self.dynamic_mappings = {}
        
        self.logger.info("Knowledge Manager initialized with %d pillar levels", 
                        len(self.pillar_levels))
    
    def _initialize_pillar_levels(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize the dictionary of all Pillar Levels (PL1-PL100).
        
        Returns:
            Dictionary of pillar level definitions
        """
        pillar_levels = {}
        
        # Load from YAML file if available
        yaml_path = os.path.join("data", "ukg", "pillar_levels_expanded.yaml")
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    if data and 'PillarLevels' in data:
                        for pillar in data['PillarLevels']:
                            pl_id = pillar.get('id')
                            if pl_id:
                                pillar_levels[pl_id] = pillar
                        self.logger.info(f"Loaded {len(pillar_levels)} pillar levels from {yaml_path}")
            except Exception as e:
                self.logger.error(f"Error loading pillar levels from YAML: {str(e)}")
        
        # If no YAML data, use hardcoded examples
        if not pillar_levels:
            self.logger.warning("No pillar levels loaded from YAML, using hardcoded defaults")
            pillar_levels = self._get_default_pillar_levels()
        
        return pillar_levels
    
    def _get_default_pillar_levels(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default pillar level definitions if YAML file is not available.
        
        Returns:
            Dictionary of default pillar level definitions
        """
        pillar_levels = {}
        
        # Example Pillar Levels based on files provided
        pillar_levels["PL01"] = {
            "id": "PL01",
            "label": "U.S. Government Regulatory Systems",
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
            "label": "Physical Sciences",
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
            "label": "Contracting & Procurement Sciences",
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
            "label": "Healthcare Sciences",
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
            "label": "Data Privacy & Security",
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
            "label": "Legal Frameworks",
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
            "label": "Public Policy and Federal Governance",
            "description": "Government policy development and implementation methods",
            "sublevels": {
                "1": "Policy Analysis",
                "2": "Federal Budget Process",
                "3": "Agency Rulemaking",
                "4": "Legislative Process"
            }
        }
        
        return pillar_levels
    
    def get_pillar_level(self, pillar_id: str) -> Dict[str, Any]:
        """
        Get a specific pillar level by ID.
        
        Args:
            pillar_id: Pillar Level ID (e.g., "PL01")
            
        Returns:
            Dict containing pillar level data or error message
        """
        self.logger.info(f"[{datetime.now()}] Retrieving Pillar Level {pillar_id}")
        
        if pillar_id in self.pillar_levels:
            return {
                'status': 'success',
                'pillar': self.pillar_levels[pillar_id],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'error',
                'message': f'Pillar Level {pillar_id} not found',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_all_pillar_levels(self) -> Dict[str, Any]:
        """
        Get all pillar levels.
        
        Returns:
            Dict containing all pillar levels
        """
        self.logger.info(f"[{datetime.now()}] Retrieving all Pillar Levels")
        
        return {
            'status': 'success',
            'pillars': list(self.pillar_levels.values()),
            'count': len(self.pillar_levels),
            'timestamp': datetime.now().isoformat()
        }
    
    def create_pillar_level(self, pillar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new pillar level.
        
        Args:
            pillar_data: Dictionary with pillar level data
            
        Returns:
            Dict containing creation result
        """
        self.logger.info(f"[{datetime.now()}] Creating new Pillar Level")
        
        try:
            pillar_id = pillar_data.get('id')
            if not pillar_id:
                return {
                    'status': 'error',
                    'message': 'Pillar ID is required',
                    'timestamp': datetime.now().isoformat()
                }
            
            if pillar_id in self.pillar_levels:
                return {
                    'status': 'error',
                    'message': f'Pillar Level {pillar_id} already exists',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Add to internal dictionary
            self.pillar_levels[pillar_id] = pillar_data
            
            # If database manager is available, store in DB
            if self.db_manager:
                db_pillars = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_level',
                    'pillar_id': pillar_id
                })
                
                if not db_pillars:
                    # Create pillar node in database
                    pillar_node = {
                        'uid': f"pillar_level_{pillar_id}_{uuid.uuid4().hex[:8]}",
                        'node_type': 'pillar_level',
                        'axis_number': 1,
                        'pillar_id': pillar_id,
                        'name': pillar_data.get('label', f'Pillar {pillar_id}'),
                        'description': pillar_data.get('description', ''),
                        'sublevels': pillar_data.get('sublevels', {})
                    }
                    self.db_manager.add_node(pillar_node)
            
            return {
                'status': 'success',
                'pillar': pillar_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error creating Pillar Level: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating Pillar Level: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def add_sublevel(self, pillar_id: str, sublevel_id: str, sublevel_name: str, 
                   sublevel_description: str = "", parent_sublevel_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a sublevel to a Pillar Level.
        
        Args:
            pillar_id: Pillar Level ID (e.g., "PL01")
            sublevel_id: Sublevel ID (e.g., "1", "1.1", "1.1.1")
            sublevel_name: Name of the sublevel
            sublevel_description: Description of the sublevel
            parent_sublevel_id: Optional parent sublevel ID
            
        Returns:
            Dict containing addition result
        """
        self.logger.info(f"[{datetime.now()}] Adding sublevel {sublevel_id} to {pillar_id}")
        
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
            
            # Create sublevel
            new_sublevel = {
                'id': sublevel_id,
                'label': sublevel_name,
                'description': sublevel_description,
            }
            
            if parent_sublevel_id:
                new_sublevel['parent_id'] = parent_sublevel_id
                
            # Update in memory dictionary (simplified for example)
            if 'sublevels' not in pillar or not isinstance(pillar['sublevels'], list):
                pillar['sublevels'] = []
                
            pillar['sublevels'].append(new_sublevel)
            
            # Update in database if available
            if self.db_manager:
                # Find the pillar in database
                db_pillars = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_level',
                    'pillar_id': pillar_id
                })
                
                if db_pillars:
                    db_pillar = db_pillars[0]
                    
                    # Create sublevel node
                    sublevel_node = {
                        'uid': f"sublevel_{pillar_id}_{sublevel_id}_{uuid.uuid4().hex[:8]}",
                        'node_type': 'pillar_sublevel',
                        'axis_number': 1,
                        'pillar_id': pillar_id,
                        'sublevel_id': sublevel_id,
                        'name': sublevel_name,
                        'description': sublevel_description,
                        'parent_sublevel_id': parent_sublevel_id
                    }
                    new_sublevel = self.db_manager.add_node(sublevel_node)
                    
                    # Create edge from pillar to sublevel
                    edge_data = {
                        'uid': f"edge_{uuid.uuid4()}",
                        'source_id': db_pillar['uid'],
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
                    'description': sublevel_description,
                    'parent_sublevel_id': parent_sublevel_id
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error adding sublevel: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error adding sublevel: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_sublevel(self, pillar_id: str, sublevel_id: str) -> Dict[str, Any]:
        """
        Get a specific sublevel from a Pillar Level.
        
        Args:
            pillar_id: Pillar Level ID (e.g., "PL01")
            sublevel_id: Sublevel ID (e.g., "1", "1.1", "1.1.1")
            
        Returns:
            Dict containing sublevel data or error message
        """
        self.logger.info(f"[{datetime.now()}] Retrieving sublevel {sublevel_id} from {pillar_id}")
        
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
            
            # Recursive function to find sublevel in nested structure
            def find_sublevel(sublevels, target_id):
                if not sublevels or not isinstance(sublevels, list):
                    return None
                
                for sl in sublevels:
                    if sl.get('id') == target_id:
                        return sl
                    
                    # Check nested sublevels
                    if 'sublevels' in sl:
                        nested = find_sublevel(sl['sublevels'], target_id)
                        if nested:
                            return nested
                
                return None
            
            # Search for sublevel
            if 'sublevels' in pillar:
                sublevel = find_sublevel(pillar['sublevels'], sublevel_id)
                
                if sublevel:
                    return {
                        'status': 'success',
                        'pillar_id': pillar_id,
                        'sublevel': sublevel,
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {
                'status': 'error',
                'message': f'Sublevel {sublevel_id} not found in Pillar {pillar_id}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error retrieving sublevel: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error retrieving sublevel: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def create_dynamic_mapping(self, pillar_id: str, sublevel_id: str, 
                             target_pillar_id: str, target_sublevel_id: str,
                             mapping_type: str, strength: float = 0.5,
                             bidirectional: bool = False) -> Dict[str, Any]:
        """
        Create a dynamic mapping between two sublevels from different pillars.
        
        Args:
            pillar_id: Source Pillar Level ID
            sublevel_id: Source Sublevel ID
            target_pillar_id: Target Pillar Level ID
            target_sublevel_id: Target Sublevel ID
            mapping_type: Type of relationship (e.g., "related_to", "depends_on")
            strength: Connection strength (0.0-1.0)
            bidirectional: Whether the mapping is bidirectional
            
        Returns:
            Dict containing mapping result
        """
        self.logger.info(f"[{datetime.now()}] Creating dynamic mapping {pillar_id}.{sublevel_id} -> {target_pillar_id}.{target_sublevel_id}")
        
        try:
            # Check if source sublevel exists
            source_result = self.get_sublevel(pillar_id, sublevel_id)
            
            if source_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f'Source sublevel {pillar_id}.{sublevel_id} not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Check if target sublevel exists
            target_result = self.get_sublevel(target_pillar_id, target_sublevel_id)
            
            if target_result['status'] != 'success':
                return {
                    'status': 'error',
                    'message': f'Target sublevel {target_pillar_id}.{target_sublevel_id} not found',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create mapping ID
            mapping_id = f"{pillar_id}.{sublevel_id}_{target_pillar_id}.{target_sublevel_id}"
            
            # Create mapping object
            mapping = {
                'id': mapping_id,
                'source': {
                    'pillar_id': pillar_id,
                    'sublevel_id': sublevel_id
                },
                'target': {
                    'pillar_id': target_pillar_id,
                    'sublevel_id': target_sublevel_id
                },
                'mapping_type': mapping_type,
                'strength': strength,
                'bidirectional': bidirectional,
                'created_at': datetime.now().isoformat()
            }
            
            # Store in dynamic mappings dictionary
            if 'mappings' not in self.dynamic_mappings:
                self.dynamic_mappings['mappings'] = []
                
            self.dynamic_mappings['mappings'].append(mapping)
            
            # If database manager is available, store in DB
            if self.db_manager:
                # Find source and target nodes
                source_nodes = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_sublevel',
                    'pillar_id': pillar_id,
                    'sublevel_id': sublevel_id
                })
                
                target_nodes = self.db_manager.get_nodes_by_properties({
                    'node_type': 'pillar_sublevel',
                    'pillar_id': target_pillar_id,
                    'sublevel_id': target_sublevel_id
                })
                
                if source_nodes and target_nodes:
                    # Create edge from source to target
                    edge_data = {
                        'uid': f"edge_mapping_{uuid.uuid4()}",
                        'source_id': source_nodes[0]['uid'],
                        'target_id': target_nodes[0]['uid'],
                        'edge_type': mapping_type,
                        'attributes': {
                            'strength': strength,
                            'created_at': datetime.now().isoformat()
                        }
                    }
                    self.db_manager.add_edge(edge_data)
                    
                    # If bidirectional, create reverse edge
                    if bidirectional:
                        reverse_edge_data = {
                            'uid': f"edge_mapping_{uuid.uuid4()}",
                            'source_id': target_nodes[0]['uid'],
                            'target_id': source_nodes[0]['uid'],
                            'edge_type': mapping_type,
                            'attributes': {
                                'strength': strength,
                                'created_at': datetime.now().isoformat()
                            }
                        }
                        self.db_manager.add_edge(reverse_edge_data)
            
            return {
                'status': 'success',
                'mapping': mapping,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error creating dynamic mapping: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error creating dynamic mapping: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_dynamic_mappings(self, pillar_id: Optional[str] = None, 
                           sublevel_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all dynamic mappings, optionally filtered by pillar and sublevel.
        
        Args:
            pillar_id: Optional Pillar Level ID filter
            sublevel_id: Optional Sublevel ID filter
            
        Returns:
            Dict containing mappings
        """
        self.logger.info(f"[{datetime.now()}] Retrieving dynamic mappings")
        
        try:
            if 'mappings' not in self.dynamic_mappings:
                return {
                    'status': 'success',
                    'mappings': [],
                    'count': 0,
                    'timestamp': datetime.now().isoformat()
                }
            
            mappings = self.dynamic_mappings['mappings']
            
            # Apply filters if specified
            if pillar_id:
                filtered_mappings = []
                for m in mappings:
                    if m['source']['pillar_id'] == pillar_id or m['target']['pillar_id'] == pillar_id:
                        if sublevel_id:
                            if (m['source']['pillar_id'] == pillar_id and m['source']['sublevel_id'] == sublevel_id) or \
                               (m['target']['pillar_id'] == pillar_id and m['target']['sublevel_id'] == sublevel_id):
                                filtered_mappings.append(m)
                        else:
                            filtered_mappings.append(m)
                
                return {
                    'status': 'success',
                    'mappings': filtered_mappings,
                    'count': len(filtered_mappings),
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'status': 'success',
                'mappings': mappings,
                'count': len(mappings),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error retrieving dynamic mappings: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error retrieving dynamic mappings: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def analyze_text_for_pillar_context(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to identify relevant pillar levels and sublevels.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict containing identified pillar contexts
        """
        self.logger.info(f"[{datetime.now()}] Analyzing text for pillar context")
        
        try:
            # Simple keyword-based approach for demonstration
            # In a real implementation, this would use NLP/ML techniques
            results = []
            
            for pillar_id, pillar in self.pillar_levels.items():
                pillar_name = pillar.get('label', '')
                pillar_desc = pillar.get('description', '')
                
                # Check if pillar name or description appears in text
                if pillar_name.lower() in text.lower() or pillar_desc.lower() in text.lower():
                    # Found a matching pillar
                    match = {
                        'pillar_id': pillar_id,
                        'pillar_name': pillar_name,
                        'confidence': 0.8,  # Placeholder
                        'sublevels': []
                    }
                    
                    # Check for sublevels
                    if 'sublevels' in pillar and isinstance(pillar['sublevels'], list):
                        for sublevel in pillar['sublevels']:
                            sl_name = sublevel.get('label', '')
                            sl_desc = sublevel.get('description', '')
                            
                            if sl_name.lower() in text.lower() or sl_desc.lower() in text.lower():
                                match['sublevels'].append({
                                    'sublevel_id': sublevel.get('id'),
                                    'sublevel_name': sl_name,
                                    'confidence': 0.7  # Placeholder
                                })
                    
                    results.append(match)
            
            return {
                'status': 'success',
                'context': {
                    'pillars': results,
                    'count': len(results)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error analyzing text for pillar context: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error analyzing text for pillar context: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def dynamic_sublevel_expansion(self, pillar_id: str, context_text: str = None) -> Dict[str, Any]:
        """
        Dynamically expand sublevels for a pillar based on context.
        
        This implements the dynamic mapping engine that can generate
        sublevel mappings based on contextual information.
        
        Args:
            pillar_id: Pillar Level ID to expand
            context_text: Optional context text to guide expansion
            
        Returns:
            Dict containing expanded sublevel structure
        """
        self.logger.info(f"[{datetime.now()}] Dynamically expanding sublevels for {pillar_id}")
        
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
            
            # Create base expansion structure
            expansion = {
                'pillar_id': pillar_id,
                'pillar_name': pillar.get('label', f'Pillar {pillar_id}'),
                'base_sublevels': [],
                'expanded_sublevels': [],
                'related_pillars': []
            }
            
            # Add base sublevels
            if 'sublevels' in pillar and isinstance(pillar['sublevels'], list):
                expansion['base_sublevels'] = pillar['sublevels']
            
            # Generate expanded sublevels based on existing knowledge
            # For demonstration, this is simplified - a real implementation
            # would use more sophisticated techniques
            
            # Check for related pillars via dynamic mappings
            if 'mappings' in self.dynamic_mappings:
                related_pillars = {}
                
                for mapping in self.dynamic_mappings['mappings']:
                    # Check if this pillar is in the mapping
                    if mapping['source']['pillar_id'] == pillar_id:
                        target_pillar = mapping['target']['pillar_id']
                        
                        if target_pillar not in related_pillars:
                            related_pillars[target_pillar] = {
                                'pillar_id': target_pillar,
                                'strength': mapping['strength'],
                                'mappings': []
                            }
                        
                        related_pillars[target_pillar]['mappings'].append({
                            'source_sublevel': mapping['source']['sublevel_id'],
                            'target_sublevel': mapping['target']['sublevel_id'],
                            'mapping_type': mapping['mapping_type']
                        })
                    
                    elif mapping['target']['pillar_id'] == pillar_id:
                        source_pillar = mapping['source']['pillar_id']
                        
                        if source_pillar not in related_pillars:
                            related_pillars[source_pillar] = {
                                'pillar_id': source_pillar,
                                'strength': mapping['strength'],
                                'mappings': []
                            }
                        
                        related_pillars[source_pillar]['mappings'].append({
                            'source_sublevel': mapping['target']['sublevel_id'],
                            'target_sublevel': mapping['source']['sublevel_id'],
                            'mapping_type': mapping['mapping_type']
                        })
                
                expansion['related_pillars'] = list(related_pillars.values())
            
            # Use context text if provided to enhance expansion
            if context_text:
                context_analysis = self.analyze_text_for_pillar_context(context_text)
                
                if context_analysis['status'] == 'success':
                    # Add suggested new sublevels based on context
                    # This is a simplified placeholder implementation
                    # A real system would use more sophisticated NLP/ML
                    expansion['context_pillars'] = context_analysis['context']['pillars']
                    
                    # Look for potential new connections
                    if 'pillars' in context_analysis['context']:
                        for cp in context_analysis['context']['pillars']:
                            if cp['pillar_id'] != pillar_id:
                                # Found another pillar in context - might suggest a connection
                                if 'related_pillars' not in expansion:
                                    expansion['related_pillars'] = []
                                
                                # Check if already in related pillars
                                if not any(rp['pillar_id'] == cp['pillar_id'] for rp in expansion['related_pillars']):
                                    expansion['related_pillars'].append({
                                        'pillar_id': cp['pillar_id'],
                                        'pillar_name': cp['pillar_name'],
                                        'strength': 0.6,  # Placeholder confidence
                                        'suggested': True,
                                        'reason': 'Found in context analysis'
                                    })
            
            return {
                'status': 'success',
                'expansion': expansion,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error expanding sublevels: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error expanding sublevels: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def export_pillar_levels_to_yaml(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export all pillar levels to a YAML file.
        
        Args:
            file_path: Optional file path (defaults to data/ukg/pillar_levels_expanded.yaml)
            
        Returns:
            Dict with export result
        """
        self.logger.info(f"[{datetime.now()}] Exporting pillar levels to YAML")
        
        try:
            if not file_path:
                file_path = os.path.join("data", "ukg", "pillar_levels_expanded.yaml")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Format for export
            export_data = {
                'PillarLevels': list(self.pillar_levels.values())
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(export_data, file, default_flow_style=False, sort_keys=False)
            
            return {
                'status': 'success',
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'message': f"Successfully exported {len(self.pillar_levels)} pillar levels to {file_path}"
            }
            
        except Exception as e:
            self.logger.error(f"[{datetime.now()}] Error exporting pillar levels: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error exporting pillar levels: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
