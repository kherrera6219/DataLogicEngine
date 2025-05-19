import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class UnitedSystemManager:
    """
    United System Manager (USM)
    
    This component serves as the central coordinator for the UKG system, managing
    the connections between different components and providing system-wide services
    like ID generation, configuration management, and component registration.
    """
    
    def __init__(self, config=None):
        """
        Initialize the United System Manager.
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        logging.info(f"[{datetime.now()}] Initializing UnitedSystemManager...")
        self.config = config or {}
        
        # System component registry
        self.components = {}
        
        # ID namespaces for different entity types
        self.id_namespaces = {
            'Node': 'ND',
            'Edge': 'ED',
            'PillarLevel': 'PL',
            'Pillar': 'P',
            'Principle': 'PR',
            'Perspective': 'PV',
            'Dimension': 'DM',
            'Decision': 'DC',
            'Influence': 'IN',
            'PointOfView': 'POV',
            'ParadigmCase': 'PC',
            'EngagementModel': 'EM',
            'EpistemologicalConstraint': 'EC',
            'EthicalConsideration': 'ET',
            'Location': 'LOC',
            'Temporal': 'TMP',
            'Session': 'SS',
            'Memory': 'MEM',
            'KnowledgeAlgorithm': 'KA',
            'KAExecution': 'KAEX',
            'SimulationPass': 'SP',
            'SimulationLayer': 'SL',
            'OntologyProposal': 'PROP'
        }
        
        logging.info(f"[{datetime.now()}] UnitedSystemManager initialized with {len(self.id_namespaces)} ID namespaces")
    
    def register_component(self, component_name: str, component_instance) -> bool:
        """
        Register a component with the United System Manager.
        
        Args:
            component_name: Name of the component
            component_instance: Reference to the component instance
            
        Returns:
            bool: True if registration was successful
        """
        if component_name in self.components:
            logging.warning(f"[{datetime.now()}] USM: Component {component_name} already registered, replacing...")
        
        self.components[component_name] = component_instance
        logging.info(f"[{datetime.now()}] USM: Registered component {component_name}")
        
        return True
    
    def get_component(self, component_name: str) -> Any:
        """
        Get a registered component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Any: Component instance or None if not registered
        """
        return self.components.get(component_name)
    
    def create_unified_id(self, entity_type: str, entity_label: str = "", 
                        ukg_coords: Optional[Dict] = None) -> Dict:
        """
        Create a new unified ID for an entity.
        
        Args:
            entity_type: Type of entity (Node, PillarLevel, etc.)
            entity_label: Human-readable label for the entity
            ukg_coords: Additional metadata to include in the ID
            
        Returns:
            dict: ID package with various formats of the ID
        """
        namespace = self.id_namespaces.get(entity_type, 'GEN')
        
        # Generate a UUID
        raw_uuid = uuid.uuid4()
        
        # Create a timestamp component
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Create a string representation
        uid_string = f"{namespace}_{timestamp}_{str(raw_uuid)[:8]}"
        
        # Create a short version for display
        short_uid = f"{namespace}_{str(raw_uuid)[:8]}"
        
        # Create a "safe" version for use in URLs, filenames, etc.
        safe_uid = uid_string.replace('-', '_').lower()
        
        # Create the ID package
        id_package = {
            'uid_string': uid_string,
            'short_uid': short_uid,
            'safe_uid': safe_uid,
            'raw_uuid': str(raw_uuid),
            'namespace': namespace,
            'entity_type': entity_type,
            'entity_label': entity_label,
            'timestamp': timestamp,
            'creation_time': datetime.now().isoformat(),
            'ukg_coords': ukg_coords or {}
        }
        
        return id_package
    
    def get_system_health(self) -> Dict:
        """
        Get the health status of the UKG system.
        
        Returns:
            dict: System health information
        """
        # Start with basic health info
        health_info = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'component_count': len(self.components),
            'components': {},
            'registered_components': list(self.components.keys())
        }
        
        # Check components
        for name, component in self.components.items():
            # For components that have a health check method
            if hasattr(component, 'get_health') and callable(getattr(component, 'get_health')):
                try:
                    component_health = component.get_health()
                    health_info['components'][name] = component_health
                except Exception as e:
                    health_info['components'][name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                health_info['components'][name] = {
                    'status': 'unknown',
                    'reason': 'No health check method available'
                }
        
        # Determine overall status
        if any(comp.get('status') == 'error' for comp in health_info['components'].values()):
            health_info['status'] = 'degraded'
        
        return health_info
    
    def load_config_from_file(self, config_file_path: str) -> bool:
        """
        Load configuration from a file.
        
        Args:
            config_file_path: Path to the configuration file
            
        Returns:
            bool: True if loading was successful
        """
        try:
            if not os.path.exists(config_file_path):
                logging.error(f"[{datetime.now()}] USM: Configuration file not found: {config_file_path}")
                return False
            
            file_ext = os.path.splitext(config_file_path)[1].lower()
            
            if file_ext in ('.yaml', '.yml'):
                import yaml
                with open(config_file_path, 'r') as f:
                    new_config = yaml.safe_load(f)
            elif file_ext == '.json':
                import json
                with open(config_file_path, 'r') as f:
                    new_config = json.load(f)
            else:
                logging.error(f"[{datetime.now()}] USM: Unsupported config file format: {file_ext}")
                return False
            
            # Update configuration
            self.config.update(new_config)
            logging.info(f"[{datetime.now()}] USM: Loaded configuration from {config_file_path}")
            
            return True
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] USM: Error loading configuration: {str(e)}")
            return False