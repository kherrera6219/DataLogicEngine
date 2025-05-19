import logging
import os
import yaml
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Import core components
from core.graph.graph_manager import GraphManager
from core.memory.structured_memory_manager import StructuredMemoryManager 
from core.system.united_system_manager import UnitedSystemManager
from core.engine.ka_engine import KAEngine
from core.simulation.simulation_engine import SimulationEngine
from core.simulation.location_context_engine import LocationContextEngine
from core.self_evolving.sekre_engine import SekreEngine

class SystemInitializer:
    """
    System Initializer
    
    This component is responsible for initializing and connecting all the components
    of the UKG system. It loads configurations, creates component instances, and
    sets up the connections between them.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the System Initializer.
        
        Args:
            config_path (str, optional): Path to the configuration file
        """
        logging.info(f"[{datetime.now()}] Starting UKG System initialization...")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.usm = None
        self.gm = None
        self.smm = None
        self.ka_engine = None
        self.simulation_engine = None
        self.location_context_engine = None
        self.sekre_engine = None
        
        # Initialize the system
        self._initialize_system()
        
        logging.info(f"[{datetime.now()}] UKG System initialization complete")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        Load system configuration from file or use defaults.
        
        Args:
            config_path (str, optional): Path to the configuration file
            
        Returns:
            dict: Configuration dictionary
        """
        # Default configuration
        default_config = {
            "system_name": "Universal Knowledge Graph",
            "version": "1.0.0",
            "log_level": "INFO",
            "data_directory": "./data",
            "max_simulation_passes": 3,
            "target_confidence_overall": 0.90,
            "enable_gatekeeper": True,
            "layer_progression": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "axis12_location_logic": {
                "default_location_context_uid": "LOC_COUNTRY_USA",
                "location_extraction": {
                    "use_nlp": False,
                    "confidence_threshold": 0.75
                }
            }
        }
        
        # If no config path provided, use defaults
        if not config_path:
            logging.info(f"[{datetime.now()}] No configuration file provided. Using default configuration.")
            return default_config
        
        try:
            # Check if file exists
            if not os.path.exists(config_path):
                logging.warning(f"[{datetime.now()}] Configuration file not found: {config_path}. Using default configuration.")
                return default_config
            
            # Load configuration based on file extension
            file_ext = os.path.splitext(config_path)[1].lower()
            
            if file_ext in ('.yaml', '.yml'):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            elif file_ext == '.json':
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                logging.warning(f"[{datetime.now()}] Unsupported configuration file format: {file_ext}. Using default configuration.")
                return default_config
            
            # Merge with defaults (keeping custom values where provided)
            merged_config = default_config.copy()
            self._merge_dicts(merged_config, config)
            
            logging.info(f"[{datetime.now()}] Loaded configuration from {config_path}")
            return merged_config
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error loading configuration: {str(e)}. Using default configuration.")
            return default_config
    
    def _merge_dicts(self, target: Dict, source: Dict) -> None:
        """
        Recursively merge source dictionary into target dictionary.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dicts(target[key], value)
            else:
                target[key] = value
    
    def _initialize_system(self) -> None:
        """
        Initialize all system components and connect them.
        """
        # 1. Create United System Manager (the central coordinator)
        self.usm = UnitedSystemManager(self.config)
        
        # 2. Create Graph Manager
        self.gm = GraphManager(self.config)
        self.usm.register_component("graph_manager", self.gm)
        
        # 3. Create Structured Memory Manager
        self.smm = StructuredMemoryManager(self.config)
        self.usm.register_component("memory_manager", self.smm)
        
        # 4. Create Knowledge Algorithm Engine
        self.ka_engine = KAEngine(self.config, self.gm, self.smm)
        self.usm.register_component("ka_engine", self.ka_engine)
        
        # 5. Create Location Context Engine
        self.location_context_engine = LocationContextEngine(self.config, self.gm, self.usm)
        self.usm.register_component("location_context_engine", self.location_context_engine)
        
        # 6. Create Simulation Engine
        self.simulation_engine = SimulationEngine(self.config, self.gm, self.smm, self.ka_engine)
        self.usm.register_component("simulation_engine", self.simulation_engine)
        
        # 7. Create SEKRE Engine (Self-Evolving Knowledge Refinement Engine)
        self.sekre_engine = SekreEngine(self.config, self.gm, self.smm, self.usm, None)  # No simulation validator yet
        self.usm.register_component("sekre_engine", self.sekre_engine)
        
        logging.info(f"[{datetime.now()}] All core UKG system components initialized and connected")
    
    def get_components(self) -> Dict[str, Any]:
        """
        Get all initialized components.
        
        Returns:
            dict: Dictionary of component references
        """
        return {
            "usm": self.usm,
            "gm": self.gm,
            "smm": self.smm,
            "ka_engine": self.ka_engine,
            "simulation_engine": self.simulation_engine,
            "location_context_engine": self.location_context_engine,
            "sekre_engine": self.sekre_engine
        }