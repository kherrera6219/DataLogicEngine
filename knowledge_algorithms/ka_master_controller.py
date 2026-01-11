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
import hashlib
import json
from typing import Dict, List, Any, Optional, Union, Set
import traceback
from datetime import datetime, timedelta
from collections import defaultdict

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
    
    def __init__(self, registry_path: Optional[str] = None, enable_caching: bool = True, cache_ttl: int = 3600):
        """
        Initialize the Master Controller.

        Args:
            registry_path: Optional path to KA registry file (YAML)
            enable_caching: Enable result caching
            cache_ttl: Cache time-to-live in seconds (default: 3600)
        """
        self.algorithms = {}
        self.execution_history = []
        self.registry_path = registry_path or self._find_registry_path()
        self.registry_format = "json" if self.registry_path.endswith(".json") else "yaml"

        # Caching configuration
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self.cache = {}  # Simple in-memory cache (can be replaced with Redis)
        self.cache_hits = 0
        self.cache_misses = 0

        # Dependency tracking
        self.dependencies = defaultdict(set)  # ka_id -> set of dependency ka_ids
        self.dependents = defaultdict(set)  # ka_id -> set of dependent ka_ids

        # Versioning
        self.algorithm_versions = {}  # ka_id -> version string

        # Metrics
        self.metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_execution_time': 0.0,
            'cache_hit_rate': 0.0,
            'algorithms_by_usage': defaultdict(int)
        }

        # Load registry and register algorithms
        self._load_registry()
        logger.info(f"Initialized Master Controller with {len(self.algorithms)} algorithms (caching: {enable_caching})")
    
    def _find_registry_path(self) -> str:
        """Find registry path based on common locations."""
        # Try to find JSON registry first (Enterprise standard)
        json_path = os.path.join(os.path.dirname(__file__), "..", "core", "data", "ka_registry.json")
        if os.path.exists(json_path):
            return json_path
            
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "ka_registry.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "config", "ka_registry.yaml")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # If no registry found, create a new one (legacy behavior)
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
                        ka_id = f"KA-{ka_num:03d}"
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
            if self.registry_format == "json":
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
                
                # Registry data is a list of objects in JSON format
                for ka_data in registry_data:
                    ka_id = ka_data.get("KA_ID", "")
                    if ka_id:
                        # Construct implementation path based on ID
                        # Legacy modules are like knowledge_algorithms.ka_01_...
                        # We try to find the actual module if possible, otherwise use a placeholder
                        num_part = ka_id.split('-')[1]
                        ka_num = int(num_part)
                        
                        # Find the module filename
                        module_name = None
                        current_dir = os.path.dirname(__file__)
                        for filename in os.listdir(current_dir):
                            if filename.startswith(f'ka_{ka_num:02d}_') or filename.startswith(f'ka_{ka_num:03d}_'):
                                module_name = os.path.splitext(filename)[0]
                                break
                        
                        if module_name:
                            function_path = f"knowledge_algorithms.{module_name}.run"
                        else:
                            # Default fallback
                            function_path = f"knowledge_algorithms.ka_{ka_num:02d}.run"
                            
                        self.register_algorithm(ka_id, function_path)
                        
                        # Store metadata
                        self.algorithms[ka_id]["metadata"] = ka_data
                        
                        # Register dependencies
                        deps = ka_data.get("Dependencies")
                        if deps:
                            dep_list = [d.strip() for d in str(deps).split(',') if d.strip()]
                            for dep in dep_list:
                                self.add_dependency(ka_id, dep)
            else:
                with open(self.registry_path, 'r') as f:
                    registry = yaml.safe_load(f)
                
                if not registry:
                    logger.warning("Empty registry file")
                    return
                
                for ka_id, function_path in registry.items():
                    norm_id = self._normalize_ka_id(ka_id)
                    self.register_algorithm(norm_id, function_path)
            
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            traceback.print_exc()

    def _normalize_ka_id(self, ka_id: str) -> str:
        """Normalize KA-1 to KA-001 format."""
        if not ka_id:
            return ka_id
        if ka_id.startswith("KA-"):
            parts = ka_id.split('-')
            if len(parts) == 2 and parts[1].isdigit():
                return f"KA-{int(parts[1]):03d}"
        return ka_id
    
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
    
    def add_dependency(self, ka_id: str, depends_on: Union[str, List[str]]) -> bool:
        """
        Add dependency for a Knowledge Algorithm.

        Args:
            ka_id: Algorithm identifier
            depends_on: Algorithm ID(s) that ka_id depends on

        Returns:
            True if successful
        """
        if ka_id not in self.algorithms:
            logger.error(f"Algorithm {ka_id} not registered")
            return False

        # Convert to list if single string
        if isinstance(depends_on, str):
            depends_on = [depends_on]

        # Add dependencies
        for dep_id in depends_on:
            if dep_id not in self.algorithms:
                logger.warning(f"Dependency {dep_id} not registered, skipping")
                continue

            self.dependencies[ka_id].add(dep_id)
            self.dependents[dep_id].add(ka_id)

        logger.debug(f"Added dependencies for {ka_id}: {depends_on}")
        return True

    def get_dependencies(self, ka_id: str, recursive: bool = False) -> Set[str]:
        """
        Get dependencies for a Knowledge Algorithm.

        Args:
            ka_id: Algorithm identifier
            recursive: Include transitive dependencies

        Returns:
            Set of dependency algorithm IDs
        """
        if ka_id not in self.algorithms:
            return set()

        if not recursive:
            return self.dependencies.get(ka_id, set())

        # Recursively get all dependencies
        all_deps = set()
        to_process = list(self.dependencies.get(ka_id, set()))

        while to_process:
            dep_id = to_process.pop(0)
            if dep_id not in all_deps:
                all_deps.add(dep_id)
                to_process.extend(self.dependencies.get(dep_id, set()))

        return all_deps

    def resolve_dependencies(self, ka_ids: List[str]) -> List[str]:
        """
        Resolve dependencies and return execution order.

        Args:
            ka_ids: List of algorithm IDs to execute

        Returns:
            Ordered list of algorithm IDs (dependencies first)
        """
        # Build execution order using topological sort
        result = []
        visited = set()
        temp_mark = set()

        def visit(ka_id: str):
            if ka_id in temp_mark:
                raise ValueError(f"Circular dependency detected involving {ka_id}")

            if ka_id not in visited:
                temp_mark.add(ka_id)

                # Visit dependencies first
                for dep_id in self.dependencies.get(ka_id, set()):
                    visit(dep_id)

                temp_mark.remove(ka_id)
                visited.add(ka_id)
                result.append(ka_id)

        # Visit all requested algorithms
        for ka_id in ka_ids:
            if ka_id not in visited:
                visit(ka_id)

        return result

    def set_version(self, ka_id: str, version: str) -> bool:
        """
        Set version for a Knowledge Algorithm.

        Args:
            ka_id: Algorithm identifier
            version: Version string (e.g., "1.0.0")

        Returns:
            True if successful
        """
        if ka_id not in self.algorithms:
            logger.error(f"Algorithm {ka_id} not registered")
            return False

        self.algorithm_versions[ka_id] = version
        logger.debug(f"Set version for {ka_id}: {version}")
        return True

    def get_version(self, ka_id: str) -> Optional[str]:
        """
        Get version for a Knowledge Algorithm.

        Args:
            ka_id: Algorithm identifier

        Returns:
            Version string or None
        """
        return self.algorithm_versions.get(ka_id)

    def _get_cache_key(self, ka_id: str, data: Dict[str, Any]) -> str:
        """
        Generate cache key for algorithm execution.

        Args:
            ka_id: Algorithm identifier
            data: Input data

        Returns:
            Cache key string
        """
        # Create deterministic hash of input data
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]

        # Include version in cache key
        version = self.algorithm_versions.get(ka_id, "1.0.0")

        return f"{ka_id}:v{version}:{data_hash}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get result from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None
        """
        if not self.enable_caching:
            return None

        cache_entry = self.cache.get(cache_key)
        if cache_entry is None:
            self.cache_misses += 1
            return None

        # Check if cache entry is still valid
        cached_time, result = cache_entry
        if time.time() - cached_time > self.cache_ttl:
            # Cache expired
            del self.cache[cache_key]
            self.cache_misses += 1
            return None

        self.cache_hits += 1
        logger.debug(f"Cache hit for {cache_key}")
        return result

    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Save result to cache.

        Args:
            cache_key: Cache key
            result: Result to cache
        """
        if not self.enable_caching:
            return

        self.cache[cache_key] = (time.time(), result)
        logger.debug(f"Cached result for {cache_key}")

    def clear_cache(self, ka_id: Optional[str] = None) -> int:
        """
        Clear cache.

        Args:
            ka_id: Optional algorithm ID to clear cache for (clears all if None)

        Returns:
            Number of cache entries cleared
        """
        if ka_id is None:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared all cache ({count} entries)")
            return count

        # Clear cache for specific algorithm
        count = 0
        keys_to_delete = [key for key in self.cache.keys() if key.startswith(f"{ka_id}:")]
        for key in keys_to_delete:
            del self.cache[key]
            count += 1

        logger.info(f"Cleared cache for {ka_id} ({count} entries)")
        return count

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get controller metrics.

        Returns:
            Dictionary of metrics
        """
        # Update cache hit rate
        total_requests = self.cache_hits + self.cache_misses
        if total_requests > 0:
            self.metrics['cache_hit_rate'] = self.cache_hits / total_requests

        # Calculate average execution time
        if self.metrics['total_executions'] > 0:
            self.metrics['average_execution_time'] = (
                self.metrics['total_execution_time'] / self.metrics['total_executions']
            )
        else:
            self.metrics['average_execution_time'] = 0.0

        return {
            **self.metrics,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_size': len(self.cache),
            'registered_algorithms': len(self.algorithms),
            'loaded_algorithms': sum(1 for alg in self.algorithms.values() if alg['loaded'])
        }

    def load_algorithm(self, ka_id: str) -> bool:
        """
        Load a registered algorithm.

        Args:
            ka_id: Algorithm identifier

        Returns:
            True if loading was successful, False otherwise
        """
        algorithm = self.algorithms[ka_id]

        if algorithm["loaded"] and algorithm["function"] is not None:
            return True
        
        # Try KARegistry first (modern class-based system)
        try:
            from backend.knowledge_algorithm.registry import KARegistry
            ka_class = KARegistry.get_ka(ka_id)
            if ka_class:
                algorithm["loaded"] = True
                algorithm["function"] = ka_class()
                algorithm["is_class"] = True
                logger.info(f"Loaded algorithm {ka_id} from KARegistry")
                return True
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Error checking KARegistry for {ka_id}: {e}")

        try:
            # Import module
            module = importlib.import_module(algorithm["module_path"])
            
            # Get function
            function = getattr(module, algorithm["function_name"])
            
            # Update algorithm info
            algorithm["loaded"] = True
            algorithm["function"] = function
            algorithm["is_class"] = False
            
            logger.debug(f"Loaded algorithm {ka_id} from module {algorithm['module_path']}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading algorithm {ka_id}: {e}")
            return False
    
    def execute_algorithm(self, ka_id: str, data: Dict[str, Any], use_cache: bool = True, context: Any = None) -> Dict[str, Any]:
        """
        Execute a Knowledge Algorithm.

        Args:
            ka_id: Algorithm identifier
            data: Input data for the algorithm
            use_cache: Whether to use caching (default: True)
            context: Optional execution context

        Returns:
            Algorithm result dictionary
        """
        ka_id = self._normalize_ka_id(ka_id)
        
        # Check if algorithm is registered
        if ka_id not in self.algorithms:
            error_msg = f"Algorithm {ka_id} not registered"
            logger.error(error_msg)
            return {
                "ka_id": ka_id,
                "success": False,
                "error": error_msg
            }

        # Check cache first
        cache_key = self._get_cache_key(ka_id, data)
        if use_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                cached_result["from_cache"] = True
                return cached_result

        # Load algorithm if needed
        info = self.algorithms[ka_id]
        if not info["loaded"]:
            if not self.load_algorithm(ka_id):
                error_msg = f"Failed to load algorithm {ka_id}"
                logger.error(error_msg)
                self.metrics['failed_executions'] += 1
                return {
                    "ka_id": ka_id,
                    "success": False,
                    "error": error_msg
                }

        # Prepare trace if run_id is in context
        run_id = None
        if isinstance(context, dict):
            run_id = context.get('run_id')
        elif hasattr(context, 'run_id'):
            run_id = getattr(context, 'run_id', None)
            
        start_time = time.time()
        success = True
        error_msg = None
        result_data = {}
        
        try:
            # Get algorithm function/instance
            obj = self.algorithms[ka_id]["function"]
            is_class = self.algorithms[ka_id].get("is_class", False)

            # Execute based on type and signature
            if is_class or hasattr(obj, 'execute'):
                # Modern class-based KA or object with execute method
                try:
                    # Try execute(state, context)
                    result_raw = obj.execute(data, context)
                except TypeError:
                    try:
                        # Try execute(params, context) / execute(params)
                        import inspect
                        sig = inspect.signature(obj.execute)
                        if 'context' in sig.parameters:
                            result_raw = obj.execute(data, context=context)
                        else:
                            result_raw = obj.execute(data)
                    except Exception:
                        # Fallback
                        result_raw = obj.execute(data)
            else:
                # Plain function
                try:
                    import inspect
                    sig = inspect.signature(obj)
                    if 'context' in sig.parameters:
                        result_raw = obj(data, context=context)
                    else:
                        result_raw = obj(data)
                except Exception:
                    # Fallback
                    result_raw = obj(data)

            # Normalize result to dictionary
            if hasattr(result_raw, 'to_dict'):
                result_data = result_raw.to_dict()
            elif hasattr(result_raw, 'output') and hasattr(result_raw, 'log'):
                # KAResult object
                result_data = {
                    "success": getattr(result_raw, 'success', True),
                    "output": result_raw.output,
                    "log": result_raw.log,
                    "ka_id": ka_id
                }
            elif isinstance(result_raw, dict):
                result_data = result_raw
            else:
                result_data = {"output": result_raw, "success": True, "ka_id": ka_id}
            
            # Record execution
            execution_time = time.time() - start_time
            success = result_data.get("success", True) if isinstance(result_data, dict) else True

            # Update metrics
            self._record_metrics(ka_id, execution_time, success)

            # Record in execution history
            self.execution_history.append({
                "ka_id": ka_id,
                "timestamp": datetime.now().isoformat(),
                "duration": execution_time,
                "success": success,
                "run_id": run_id
            })

            # Cache the result if successful
            if success and use_cache and self.enable_caching:
                self.cache[cache_key] = (result_data, time.time())

            # Log to trace if available
            self._log_to_trace(ka_id, data, result_data, run_id, execution_time * 1000, success, None)

            logger.info(f"Executed {ka_id} in {execution_time:.3f}s (success: {success})")
            return result_data
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Fatal error in execute_algorithm for {ka_id}: {e}")
            self._record_metrics(ka_id, execution_time, False)
            return {"success": False, "error": str(e)}

    def _log_to_trace(self, ka_id, inputs, outputs, run_id, duration_ms, success, error=None):
        """Helper to log execution to the trace system."""
        if not run_id:
            return
            
        try:
            from backend.tracing.logger import TraceLogger
            TraceLogger.log_ka_invocation(
                ka_id=ka_id,
                inputs=inputs,
                outputs=outputs,
                run_id=run_id,
                duration_ms=duration_ms,
                success=success,
                error=error
            )
        except Exception as e:
            # Don't fail the algorithm execution if tracing fails
            logger.debug(f"Could not log to trace for {ka_id}: {e}")
    
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

    elif command == "metrics":
        # Get controller metrics
        return {
            "success": True,
            "metrics": controller.get_metrics()
        }

    elif command == "cache":
        # Cache management
        cache_action = data.get("action", "status")

        if cache_action == "clear":
            ka_id = data.get("algorithm")
            count = controller.clear_cache(ka_id)
            return {
                "success": True,
                "cleared": count
            }
        elif cache_action == "status":
            return {
                "success": True,
                "enabled": controller.enable_caching,
                "ttl": controller.cache_ttl,
                "size": len(controller.cache),
                "hits": controller.cache_hits,
                "misses": controller.cache_misses
            }
        else:
            return {
                "success": False,
                "error": f"Unknown cache action: {cache_action}"
            }

    elif command == "dependency":
        # Dependency management
        dep_action = data.get("action", "get")

        if dep_action == "add":
            ka_id = data.get("algorithm")
            depends_on = data.get("depends_on")

            if not ka_id or not depends_on:
                return {
                    "success": False,
                    "error": "Missing algorithm or depends_on parameter"
                }

            success = controller.add_dependency(ka_id, depends_on)
            return {
                "success": success,
                "algorithm": ka_id,
                "dependencies": list(controller.get_dependencies(ka_id))
            }

        elif dep_action == "get":
            ka_id = data.get("algorithm")

            if not ka_id:
                return {
                    "success": False,
                    "error": "Missing algorithm parameter"
                }

            recursive = data.get("recursive", False)
            dependencies = controller.get_dependencies(ka_id, recursive)

            return {
                "success": True,
                "algorithm": ka_id,
                "dependencies": list(dependencies),
                "recursive": recursive
            }

        elif dep_action == "resolve":
            algorithms = data.get("algorithms")

            if not algorithms:
                return {
                    "success": False,
                    "error": "Missing algorithms parameter"
                }

            try:
                execution_order = controller.resolve_dependencies(algorithms)
                return {
                    "success": True,
                    "algorithms": algorithms,
                    "execution_order": execution_order
                }
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e)
                }

        else:
            return {
                "success": False,
                "error": f"Unknown dependency action: {dep_action}"
            }

    elif command == "version":
        # Version management
        version_action = data.get("action", "get")

        if version_action == "set":
            ka_id = data.get("algorithm")
            version = data.get("version")

            if not ka_id or not version:
                return {
                    "success": False,
                    "error": "Missing algorithm or version parameter"
                }

            success = controller.set_version(ka_id, version)
            return {
                "success": success,
                "algorithm": ka_id,
                "version": version
            }

        elif version_action == "get":
            ka_id = data.get("algorithm")

            if not ka_id:
                return {
                    "success": False,
                    "error": "Missing algorithm parameter"
                }

            version = controller.get_version(ka_id)
            return {
                "success": True,
                "algorithm": ka_id,
                "version": version or "unknown"
            }

        else:
            return {
                "success": False,
                "error": f"Unknown version action: {version_action}"
            }

    else:
        return {
            "success": False,
            "error": f"Unknown command: {command}"
        }