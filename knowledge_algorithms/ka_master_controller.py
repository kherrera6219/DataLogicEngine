"""
Universal Knowledge Graph (UKG) System - Knowledge Algorithm Master Controller

This module provides the master controller for orchestrating and executing
the Knowledge Algorithms (KA) that power the UKG system.
"""

import logging
import importlib
from typing import Dict, List, Any, Optional, Callable
import time

logger = logging.getLogger(__name__)

class KAMasterController:
    """
    Master controller for the Knowledge Algorithms (KA) system.
    
    This controller manages the loading, execution, and orchestration of
    the various Knowledge Algorithms that power the UKG system, providing
    a unified interface for accessing their capabilities.
    """
    
    def __init__(self, registry: Optional[Dict[str, str]] = None):
        """
        Initialize the Knowledge Algorithm Master Controller.
        
        Args:
            registry: Optional pre-defined algorithm registry mapping
                     KA numbers to module paths
        """
        self.registry = registry or self._initialize_registry()
        self.algorithm_cache = {}
        logger.info("Knowledge Algorithm Master Controller initialized")
    
    def _initialize_registry(self) -> Dict[str, str]:
        """Initialize the Knowledge Algorithm registry."""
        return {
            # Format: "KA-N": "knowledge_algorithms.ka_NN_name.run"
            "KA-1": "knowledge_algorithms.ka_01_semantic_mapping.run",
            "KA-4": "knowledge_algorithms.ka_04_honeycomb_expansion.run",
            "KA-20": "knowledge_algorithms.ka_20_quad_persona.run"
        }
    
    def get_algorithm_info(self, ka_number: int) -> Dict[str, Any]:
        """
        Get information about a specific Knowledge Algorithm.
        
        Args:
            ka_number: The Knowledge Algorithm number (1-38)
            
        Returns:
            Dictionary with algorithm information
        """
        ka_id = f"KA-{ka_number}"
        
        if ka_id not in self.registry:
            return {
                "algorithm": ka_id,
                "error": f"Unknown algorithm: {ka_id}",
                "available": False
            }
        
        module_path = self.registry[ka_id]
        module_name = module_path.rsplit(".", 1)[0]
        
        # Get algorithm metadata (if available)
        metadata = self._get_algorithm_metadata(module_name)
        
        return {
            "algorithm": ka_id,
            "module_path": module_path,
            "description": metadata.get("description", "No description available"),
            "available": True
        }
    
    def _get_algorithm_metadata(self, module_name: str) -> Dict[str, Any]:
        """
        Get metadata for a Knowledge Algorithm module.
        
        Args:
            module_name: The name of the module
            
        Returns:
            Dictionary with module metadata
        """
        try:
            module = importlib.import_module(module_name)
            
            # Extract description from module docstring
            description = module.__doc__ or "No description available"
            description = description.strip().split("\n\n")[0].strip()
            
            return {
                "description": description
            }
        except (ImportError, AttributeError):
            return {
                "description": "No description available"
            }
    
    def load_algorithm(self, ka_number: int) -> Optional[Callable]:
        """
        Load a Knowledge Algorithm function.
        
        Args:
            ka_number: The Knowledge Algorithm number (1-38)
            
        Returns:
            The algorithm function or None if not found
        """
        ka_id = f"KA-{ka_number}"
        
        # Check if the algorithm is in the registry
        if ka_id not in self.registry:
            logger.error(f"Unknown algorithm: {ka_id}")
            return None
        
        # Check if the algorithm is already in cache
        if ka_id in self.algorithm_cache:
            return self.algorithm_cache[ka_id]
        
        # Load the algorithm
        module_path = self.registry[ka_id]
        try:
            module_name, func_name = module_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            algorithm_func = getattr(module, func_name)
            
            # Cache the algorithm function
            self.algorithm_cache[ka_id] = algorithm_func
            
            return algorithm_func
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load algorithm {ka_id}: {str(e)}")
            return None
    
    def run_algorithm(self, ka_number: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a Knowledge Algorithm with the provided data.
        
        Args:
            ka_number: The Knowledge Algorithm number (1-38)
            data: The input data for the algorithm
            
        Returns:
            The algorithm result
        """
        ka_id = f"KA-{ka_number}"
        
        # Load the algorithm
        algorithm_func = self.load_algorithm(ka_number)
        
        if algorithm_func is None:
            return {
                "algorithm": ka_id,
                "error": f"Failed to load algorithm {ka_id}",
                "success": False
            }
        
        # Run the algorithm and measure execution time
        try:
            start_time = time.time()
            result = algorithm_func(data)
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Ensure the result is a dictionary and add execution metadata
            if not isinstance(result, dict):
                result = {
                    "algorithm": ka_id,
                    "result": result,
                    "success": True
                }
            
            # Add execution metadata
            result["execution_time_ms"] = execution_time
            
            return result
        except Exception as e:
            logger.error(f"Error executing algorithm {ka_id}: {str(e)}")
            return {
                "algorithm": ka_id,
                "error": f"Error executing algorithm: {str(e)}",
                "success": False
            }
    
    def run_pipeline(self, pipeline: List[Dict[str, Any]], initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a pipeline of Knowledge Algorithms.
        
        Args:
            pipeline: List of pipeline steps, each with 'algorithm' (int) and optional 'transform' (function)
            initial_data: Initial input data for the pipeline
            
        Returns:
            The final pipeline result with intermediate results
        """
        current_data = initial_data.copy()
        pipeline_results = []
        
        for step_idx, step in enumerate(pipeline):
            ka_number = step.get("algorithm")
            
            if ka_number is None:
                return {
                    "error": f"Missing algorithm number in pipeline step {step_idx + 1}",
                    "success": False
                }
            
            # Run the algorithm
            result = self.run_algorithm(ka_number, current_data)
            
            # Store the step result
            pipeline_results.append({
                "step": step_idx + 1,
                "algorithm": f"KA-{ka_number}",
                "result": result
            })
            
            # If the algorithm failed, stop the pipeline
            if not result.get("success", False):
                break
            
            # Transform the result for the next step (if needed)
            transform_func = step.get("transform")
            if transform_func and callable(transform_func):
                try:
                    current_data = transform_func(result, current_data)
                except Exception as e:
                    logger.error(f"Error in transform function at step {step_idx + 1}: {str(e)}")
                    pipeline_results[-1]["transform_error"] = str(e)
                    break
            else:
                # Default transform: use result as next input
                current_data = result
        
        return {
            "pipeline_results": pipeline_results,
            "final_result": current_data,
            "success": True
        }
    
    def get_available_algorithms(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available Knowledge Algorithms.
        
        Returns:
            List of dictionaries with algorithm information
        """
        available_algorithms = []
        
        for ka_id in sorted(self.registry.keys()):
            # Extract algorithm number
            try:
                ka_number = int(ka_id.split("-")[1])
                algorithm_info = self.get_algorithm_info(ka_number)
                available_algorithms.append(algorithm_info)
            except (IndexError, ValueError):
                continue
        
        return available_algorithms


def create_master_controller() -> KAMasterController:
    """
    Create and initialize a Knowledge Algorithm Master Controller.
    
    Returns:
        An initialized KAMasterController instance
    """
    return KAMasterController()