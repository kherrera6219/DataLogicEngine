import importlib
import inspect
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

class KALoader:
    """
    The KALoader is responsible for loading and executing Knowledge Algorithms (KAs).
    It dynamically imports KA classes from the implementations directory and manages
    their execution.
    """
    
    def __init__(self, config, graph_manager, memory_manager, united_system_manager):
        """
        Initialize the KALoader.
        
        Args:
            config (dict): Configuration dictionary
            graph_manager (GraphManager): Reference to the GraphManager
            memory_manager (StructuredMemoryManager): Reference to the StructuredMemoryManager
            united_system_manager (UnitedSystemManager): Reference to the UnitedSystemManager
        """
        self.config = config
        self.gm = graph_manager
        self.smm = memory_manager
        self.usm = united_system_manager
        
        self.ka_implementations_path = config.get('ka_implementations_path', 'core/knowledge_algorithm/implementations')
        self.default_ka_confidence_threshold = config.get('default_ka_confidence_threshold', 0.7)
        
        # Create a dictionary to store loaded KA classes
        self.ka_classes = {}
        
        # Load all KA implementations
        self._load_ka_implementations()
        
        logging.info(f"[{datetime.now()}] KALoader initialized with {len(self.ka_classes)} Knowledge Algorithms")
    
    def _load_ka_implementations(self):
        """Load all KA implementations from the implementations directory."""
        # Convert module path to Python package notation
        module_path = self.ka_implementations_path.replace('/', '.')
        
        # Get the directory path
        dir_path = os.path.join(*self.ka_implementations_path.split('/'))
        
        if not os.path.exists(dir_path):
            logging.warning(f"[{datetime.now()}] KALoader: KA implementations directory not found: {dir_path}")
            return
        
        # Find all Python files in the directory that match the KA naming pattern
        for filename in os.listdir(dir_path):
            if filename.startswith('ka') and filename.endswith('.py'):
                try:
                    # Extract KA number from filename (e.g., 'ka01_query_analyzer.py' -> '01')
                    ka_id_str = filename[2:4]
                    if not ka_id_str.isdigit():
                        continue
                    
                    ka_id = int(ka_id_str)
                    
                    # Import the module
                    module_name = f"{module_path}.{filename[:-3]}"  # Remove .py extension
                    module = importlib.import_module(module_name)
                    
                    # Find the KA class in the module
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and name.startswith('KA') and name.endswith(ka_id_str):
                            self.ka_classes[ka_id] = obj
                            logging.info(f"[{datetime.now()}] KALoader: Loaded KA{ka_id}: {name}")
                            break
                    
                except Exception as e:
                    logging.error(f"[{datetime.now()}] KALoader: Error loading KA from {filename}: {str(e)}")
    
    def execute_ka(self, ka_id, input_data, session_id=None, pass_num=None, layer_num=None):
        """
        Execute a Knowledge Algorithm.
        
        Args:
            ka_id (int): The ID of the KA to execute
            input_data (dict): Input data for the KA
            session_id (str, optional): The session ID
            pass_num (int, optional): Pass number within the session
            layer_num (int, optional): Layer number
            
        Returns:
            dict: The result of the KA execution
        """
        if ka_id not in self.ka_classes:
            error_msg = f"KA{ka_id} not found"
            logging.error(f"[{datetime.now()}] KALoader: {error_msg}")
            return {
                "status": "error",
                "error_message": error_msg,
                "ka_confidence": 0.0,
                "findings": {}
            }
        
        try:
            # Create a new instance of the KA
            ka_instance = self.ka_classes[ka_id](
                config=self.config,
                graph_manager=self.gm,
                memory_manager=self.smm,
                united_system_manager=self.usm
            )
            
            # Execute the KA
            start_time = datetime.now()
            result = ka_instance.run(input_data)
            end_time = datetime.now()
            
            # Log execution time
            execution_time = (end_time - start_time).total_seconds()
            logging.info(f"[{datetime.now()}] KALoader: Executed KA{ka_id} in {execution_time:.3f} seconds")
            
            # Log the execution in SMM if session_id is provided
            if session_id:
                self.smm.add_memory_entry(
                    session_id=session_id,
                    pass_num=pass_num if pass_num is not None else 0,
                    layer_num=layer_num if layer_num is not None else 0,
                    entry_type='ka_execution_log',
                    content={
                        'ka_id': ka_id,
                        'input_data': input_data,
                        'result': result,
                        'execution_time': execution_time
                    },
                    confidence=result.get('ka_confidence', self.default_ka_confidence_threshold)
                )
            
            return result
        
        except Exception as e:
            error_msg = f"Error executing KA{ka_id}: {str(e)}"
            logging.error(f"[{datetime.now()}] KALoader: {error_msg}", exc_info=True)
            return {
                "status": "error",
                "error_message": error_msg,
                "ka_confidence": 0.0,
                "findings": {}
            }
    
    def get_available_kas(self):
        """
        Get a list of available KAs.
        
        Returns:
            list: List of available KA IDs
        """
        return list(self.ka_classes.keys())
