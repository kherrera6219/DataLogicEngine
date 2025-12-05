"""
Universal Knowledge Graph (UKG) System - Knowledge Algorithm Master Controller

This module provides a unified controller for orchestrating the execution of
Knowledge Algorithms (KAs) in the UKG system.
"""

import importlib
import logging
import time
import os
import yaml
from typing import Dict, List, Any, Optional, Union
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("UKG-Master-Controller")

class KAMasterController:
    """
    Master controller for Knowledge Algorithms in the UKG system.
    
    This controller manages the registration, discovery, and execution of
    Knowledge Algorithms, providing a unified interface for orchestrating
    complex processing pipelines.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize the Master Controller.
        
        Args:
            registry_path: Optional path to KA registry file (YAML)
        """
        self.algorithms = {}
        self.execution_history = []
        self.registry_path = registry_path or self._find_registry_path()
        
        # Load registry and register algorithms
        self._load_registry()
        logger.info(f"Initialized Master Controller with {len(self.algorithms)} algorithms")
    
    def _find_registry_path(self) -> str:
        """Find registry path based on common locations."""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "ka_registry.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "config", "ka_registry.yaml"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ka_registry.yaml"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "ka_registry.yaml")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # If no registry found, create a new one
        default_path = os.path.join(os.path.dirname(__file__), "ka_registry.yaml")
        self._create_default_registry(default_path)
        return default_path
    
    def _create_default_registry(self, path: str) -> None:
        """Create a default registry if none exists."""
        # Discover algorithms based on naming patterns
        ka_files = self._discover_algorithm_files()
        
        # Create registry entries
        registry = {}
        for ka_id, file_path in ka_files.items():
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            registry[ka_id] = f"knowledge_algorithms.{module_name}.run"
        
        # Save registry
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(registry, f)
        
        logger.info(f"Created default registry at {path} with {len(registry)} entries")
    
    def _discover_algorithm_files(self) -> Dict[str, str]:
        """Discover algorithm files based on naming patterns."""
        ka_files = {}
        current_dir = os.path.dirname(__file__)
        
        # Check all Python files in the directory
        for filename in os.listdir(current_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                # Check if filename follows KA pattern (e.g., ka_01_semantic_mapping.py)
                if filename.startswith('ka_'):
                    parts = filename.split('_')
                    if len(parts) >= 3 and parts[1].isdigit():
                        # Extract KA number
                        ka_num = int(parts[1])
                        ka_id = f"KA-{ka_num}"
                        ka_files[ka_id] = os.path.join(current_dir, filename)
        
        return ka_files
    
    def _load_registry(self) -> None:
        """Load the algorithm registry."""
        if not self.registry_path or not os.path.exists(self.registry_path):
            logger.warning("Registry file not found, using auto-discovery")
            ka_files = self._discover_algorithm_files()
            
            for ka_id, file_path in ka_files.items():
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                self.register_algorithm(ka_id, f"knowledge_algorithms.{module_name}.run")
            
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                registry = yaml.safe_load(f)
            
            if not registry:
                logger.warning("Empty registry file")
                return
            
            for ka_id, function_path in registry.items():
                self.register_algorithm(ka_id, function_path)
            
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
    
    def _save_registry(self) -> None:
        """Save the algorithm registry."""
        if not self.registry_path:
            logger.warning("No registry path specified, not saving")
            return
        
        try:
            registry = {}
            for ka_id, algorithm in self.algorithms.items():
                registry[ka_id] = algorithm["function_path"]
            
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            with open(self.registry_path, 'w') as f:
                yaml.dump(registry, f)
            
            logger.info(f"Saved registry with {len(registry)} entries")
            
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_algorithm(self, ka_id: str, function_path: str) -> bool:
        """
        Register a Knowledge Algorithm.
        
        Args:
            ka_id: Algorithm identifier (e.g., "KA-01")
            function_path: Import path to algorithm function (e.g., "module.submodule.function")
            
        Returns:
            True if registration was successful, False otherwise
        """
        try:
            # Parse module and function names
            module_path, function_name = function_path.rsplit('.', 1)
            
            # Register algorithm info
            self.algorithms[ka_id] = {
                "ka_id": ka_id,
                "function_path": function_path,
                "module_path": module_path,
                "function_name": function_name,
                "loaded": False,
                "function": None
            }
            
            logger.debug(f"Registered algorithm {ka_id} -> {function_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering algorithm {ka_id}: {e}")
            return False
    
    def load_algorithm(self, ka_id: str) -> bool:
        """
        Load a registered algorithm.
        
        Args:
            ka_id: Algorithm identifier
            
        Returns:
            True if loading was successful, False otherwise
        """
        if ka_id not in self.algorithms:
            logger.error(f"Algorithm {ka_id} not registered")
            return False
        
        algorithm = self.algorithms[ka_id]
        
        if algorithm["loaded"] and algorithm["function"] is not None:
            return True
        
        try:
            # Import module
            module = importlib.import_module(algorithm["module_path"])
            
            # Get function
            function = getattr(module, algorithm["function_name"])
            
            # Update algorithm info
            algorithm["loaded"] = True
            algorithm["function"] = function
            
            logger.debug(f"Loaded algorithm {ka_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading algorithm {ka_id}: {e}")
            return False
    
    def execute_algorithm(self, ka_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Knowledge Algorithm.
        
        Args:
            ka_id: Algorithm identifier
            data: Input data for the algorithm
            
        Returns:
            Algorithm result dictionary
        """
        # Check if algorithm is registered
        if ka_id not in self.algorithms:
            error_msg = f"Algorithm {ka_id} not registered"
            logger.error(error_msg)
            return {
                "ka_id": ka_id,
                "success": False,
                "error": error_msg
            }
        
        # Load algorithm if needed
        if not self.algorithms[ka_id]["loaded"]:
            if not self.load_algorithm(ka_id):
                error_msg = f"Failed to load algorithm {ka_id}"
                logger.error(error_msg)
                return {
                    "ka_id": ka_id,
                    "success": False,
                    "error": error_msg
                }
        
        # Execute algorithm
        start_time = time.time()
        execution_id = f"{ka_id}-{int(start_time * 1000)}"
        
        try:
            # Get algorithm function
            function = self.algorithms[ka_id]["function"]
            
            # Execute function
            result = function(data)
            
            # Record execution
            execution_time = time.time() - start_time
            execution_record = {
                "execution_id": execution_id,
                "ka_id": ka_id,
                "timestamp": start_time,
                "duration": execution_time,
                "success": result.get("success", True),
                "input_data_keys": list(data.keys()),
                "result_keys": list(result.keys() if isinstance(result, dict) else [])
            }
            
            self.execution_history.append(execution_record)
            
            # Add execution metadata to result
            if isinstance(result, dict):
                result["execution_id"] = execution_id
                result["execution_time"] = execution_time
            
            logger.info(f"Executed {ka_id} in {execution_time:.3f}s")
            return result
            
        except Exception as e:
            # Handle execution error
            execution_time = time.time() - start_time
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            logger.error(f"Error executing {ka_id}: {error_message}")
            logger.debug(error_traceback)
            
            # Record failed execution
            execution_record = {
                "execution_id": execution_id,
                "ka_id": ka_id,
                "timestamp": start_time,
                "duration": execution_time,
                "success": False,
                "error": error_message,
                "input_data_keys": list(data.keys())
            }
            
            self.execution_history.append(execution_record)
            
            return {
                "ka_id": ka_id,
                "execution_id": execution_id,
                "success": False,
                "error": error_message,
                "execution_time": execution_time
            }
    
    def execute_sequence(self, sequence: List[Dict[str, Any]], 
                       initial_data: Optional[Dict[str, Any]] = None, 
                       return_all_results: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Execute a sequence of Knowledge Algorithms.
        
        Args:
            sequence: List of algorithm execution specifications
            initial_data: Initial data to provide to the first algorithm
            return_all_results: Whether to return all results or just the final one
            
        Returns:
            Either the final result or a list of all results
        """
        current_data = initial_data or {}
        all_results = []
        
        for i, step in enumerate(sequence):
            # Get algorithm ID
            ka_id = step.get("algorithm")
            if not ka_id:
                error_msg = f"Missing algorithm ID in step {i+1}"
                logger.error(error_msg)
                result = {
                    "success": False,
                    "error": error_msg,
                    "step": i+1
                }
                all_results.append(result)
                continue
            
            # Get parameters
            parameters = step.get("parameters", {})
            
            # Merge parameters with current data
            execution_data = {**current_data, **parameters}
            
            # Execute algorithm
            result = self.execute_algorithm(ka_id, execution_data)
            
            # Add step information
            if isinstance(result, dict):
                result["step"] = i+1
                result["algorithm"] = ka_id
            
            # Save result
            all_results.append(result)
            
            # Check for failure
            if isinstance(result, dict) and not result.get("success", True):
                logger.warning(f"Step {i+1} ({ka_id}) failed, stopping sequence")
                break
            
            # Update current data for next algorithm
            current_data = result if isinstance(result, dict) else {}
        
        if return_all_results:
            return all_results
        else:
            return all_results[-1] if all_results else {"success": False, "error": "No steps executed"}
    
    def get_available_algorithms(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about available algorithms.
        
        Returns:
            Dictionary mapping algorithm IDs to information
        """
        return {ka_id: {k: v for k, v in info.items() if k != "function"} 
                for ka_id, info in self.algorithms.items()}
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Args:
            limit: Optional limit on number of records to return
            
        Returns:
            List of execution records
        """
        if limit is None:
            return self.execution_history
        else:
            return self.execution_history[-limit:]
    
    def create_execution_plan(self, task_description: str, 
                           algorithms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Create an execution plan for a task.
        
        Args:
            task_description: Description of the task
            algorithms: Optional list of algorithms to include
            
        Returns:
            List of execution steps
        """
        # In a real implementation, this would use ML to create an optimal plan
        # For this demonstration, we'll use a simplified approach
        
        # Get available algorithms
        available_algorithms = list(self.algorithms.keys())
        if algorithms:
            # Filter to specified algorithms
            available_algorithms = [ka_id for ka_id in available_algorithms if ka_id in algorithms]
        
        # Create simple sequential plan
        plan = []
        
        # For demonstration, create a fixed plan
        if "neural" in task_description.lower() or "activation" in task_description.lower():
            if "KA-40" in available_algorithms:
                plan.append({
                    "algorithm": "KA-40",
                    "parameters": {"input_tokens": task_description.split()}
                })
        
        if "consensus" in task_description.lower() or "agent" in task_description.lower():
            if "KA-41" in available_algorithms:
                plan.append({
                    "algorithm": "KA-41",
                    "parameters": {}
                })
            
            if "KA-42" in available_algorithms:
                plan.append({
                    "algorithm": "KA-42",
                    "parameters": {}
                })
        
        if "confidence" in task_description.lower():
            if "KA-47" in available_algorithms:
                plan.append({
                    "algorithm": "KA-47",
                    "parameters": {"initial_confidence": 0.7}
                })
        
        if "curriculum" in task_description.lower() or "learning" in task_description.lower():
            if "KA-48" in available_algorithms:
                plan.append({
                    "algorithm": "KA-48",
                    "parameters": {"domain": "artificial_intelligence"}
                })
        
        if "explain" in task_description.lower() or "trace" in task_description.lower():
            if "KA-49" in available_algorithms:
                plan.append({
                    "algorithm": "KA-49",
                    "parameters": {}
                })
        
        # Ensure we have at least one step
        if not plan and available_algorithms:
            # Add first available algorithm as fallback
            plan.append({
                "algorithm": available_algorithms[0],
                "parameters": {}
            })
        
        return plan

# Create singleton instance
_instance = None

def get_controller() -> KAMasterController:
    """Get or create the KAMasterController singleton instance."""
    global _instance
    if _instance is None:
        _instance = KAMasterController()
    return _instance


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the KA Master Controller.
    
    Args:
        data: Input data
            - command: Command to execute
                - "execute": Execute an algorithm
                - "sequence": Execute a sequence of algorithms
                - "list": List available algorithms
                - "history": Get execution history
                - "plan": Create an execution plan
            - algorithm: Algorithm ID for "execute" command
            - sequence: Sequence for "sequence" command
            - task: Task description for "plan" command
            - other parameters specific to each algorithm
    
    Returns:
        Command result
    """
    controller = get_controller()
    
    # Get command
    command = data.get("command", "execute")
    
    if command == "execute":
        # Execute single algorithm
        algorithm = data.get("algorithm")
        if not algorithm:
            return {
                "success": False,
                "error": "Missing algorithm parameter"
            }
        
        # Remove command and algorithm from data
        execution_data = {k: v for k, v in data.items() if k not in ["command", "algorithm"]}
        
        # Execute algorithm
        return controller.execute_algorithm(algorithm, execution_data)
    
    elif command == "sequence":
        # Execute sequence of algorithms
        sequence = data.get("sequence")
        if not sequence:
            return {
                "success": False,
                "error": "Missing sequence parameter"
            }
        
        # Get initial data and result preference
        initial_data = data.get("initial_data")
        return_all = data.get("return_all_results", False)
        
        # Execute sequence
        return controller.execute_sequence(sequence, initial_data, return_all)
    
    elif command == "list":
        # List available algorithms
        return {
            "success": True,
            "algorithms": controller.get_available_algorithms()
        }
    
    elif command == "history":
        # Get execution history
        limit = data.get("limit")
        
        return {
            "success": True,
            "history": controller.get_execution_history(limit)
        }
    
    elif command == "plan":
        # Create execution plan
        task = data.get("task")
        if not task:
            return {
                "success": False,
                "error": "Missing task parameter"
            }
        
        algorithms = data.get("algorithms")
        
        return {
            "success": True,
            "plan": controller.create_execution_plan(task, algorithms)
        }
    
    else:
        return {
            "success": False,
            "error": f"Unknown command: {command}"
        }