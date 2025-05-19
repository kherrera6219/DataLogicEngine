import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import sys
import os
import importlib.util
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

class KAEngine:
    """
    Knowledge Algorithm Engine
    
    This component manages the execution of Knowledge Algorithms (KAs) across all
    axes of the UKG. It handles algorithm discovery, loading, execution, and result
    tracking.
    """
    
    def __init__(self, config=None, graph_manager=None, memory_manager=None):
        """
        Initialize the Knowledge Algorithm Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            graph_manager: Graph Manager reference
            memory_manager: Structured Memory Manager reference
        """
        logging.info(f"[{datetime.now()}] Initializing KAEngine...")
        self.config = config or {}
        self.graph_manager = graph_manager
        self.memory_manager = memory_manager
        
        # Configure KA engine settings
        self.ka_config = self.config.get('ka_engine', {})
        self.ka_directory = self.ka_config.get('algorithms_directory', './core/algorithms')
        self.enable_remote_kas = self.ka_config.get('enable_remote_algorithms', False)
        self.default_timeout = self.ka_config.get('default_timeout_seconds', 30)
        
        # Algorithm registry
        self.registered_algorithms = {}  # ka_id -> algorithm_info
        self.layer_algorithms = {}  # layer_num -> [ka_id]
        
        # Initialize algorithm registry
        self._initialize_algorithm_registry()
        
        logging.info(f"[{datetime.now()}] KAEngine initialized with {len(self.registered_algorithms)} algorithms")
    
    def _initialize_algorithm_registry(self):
        """
        Initialize the algorithm registry from the database and filesystem.
        """
        try:
            # First, load algorithms from the database if graph manager is available
            if self.graph_manager:
                # Get all KnowledgeAlgorithm nodes
                db_algorithms = self.graph_manager.get_nodes_by_type('KnowledgeAlgorithm')
                
                for alg in db_algorithms:
                    ka_id = alg.get('ka_id')
                    if not ka_id:
                        continue
                        
                    self.registered_algorithms[ka_id] = {
                        'ka_id': ka_id,
                        'name': alg.get('name', ''),
                        'description': alg.get('description', ''),
                        'version': alg.get('version', '1.0.0'),
                        'input_schema': alg.get('input_schema', {}),
                        'output_schema': alg.get('output_schema', {}),
                        'source': 'database',
                        'instance': None,
                        'module_path': None,
                        'source_uid': alg.get('uid')
                    }
            
            # Then, load algorithms from the filesystem
            self._load_algorithms_from_filesystem()
            
            # Build layer to algorithm mappings
            for ka_id, alg_info in self.registered_algorithms.items():
                # Get layer associations from algorithm metadata
                layers = alg_info.get('metadata', {}).get('applicable_layers', [])
                
                for layer_num in layers:
                    if layer_num not in self.layer_algorithms:
                        self.layer_algorithms[layer_num] = []
                    
                    if ka_id not in self.layer_algorithms[layer_num]:
                        self.layer_algorithms[layer_num].append(ka_id)
            
            logging.info(f"[{datetime.now()}] KAEngine: Initialized algorithm registry with {len(self.registered_algorithms)} algorithms")
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] KAEngine: Error initializing algorithm registry: {str(e)}")
    
    def _load_algorithms_from_filesystem(self):
        """
        Load algorithm modules from the filesystem.
        """
        if not os.path.isdir(self.ka_directory):
            logging.warning(f"[{datetime.now()}] KAEngine: Algorithm directory not found: {self.ka_directory}")
            return
        
        # Scan all Python files in the algorithm directory
        for root, _, files in os.walk(self.ka_directory):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = os.path.join(root, file)
                    
                    try:
                        # Load algorithm module info
                        module_name = os.path.splitext(file)[0]
                        module_info = self._inspect_algorithm_module(module_path, module_name)
                        
                        if module_info:
                            # Register all algorithms in the module
                            for alg_info in module_info:
                                ka_id = alg_info.get('ka_id')
                                if ka_id:
                                    self.registered_algorithms[ka_id] = alg_info
                                    logging.info(f"[{datetime.now()}] KAEngine: Registered algorithm {ka_id} from {module_path}")
                    
                    except Exception as e:
                        logging.error(f"[{datetime.now()}] KAEngine: Error loading algorithm module {module_path}: {str(e)}")
    
    def _inspect_algorithm_module(self, module_path: str, module_name: str) -> List[Dict]:
        """
        Inspect an algorithm module to extract algorithm information.
        
        Args:
            module_path: Path to the module file
            module_name: Name of the module
            
        Returns:
            list: List of algorithm info dictionaries
        """
        try:
            # Load module spec
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                logging.warning(f"[{datetime.now()}] KAEngine: Could not load module spec for {module_path}")
                return []
            
            # Import the module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for algorithm classes
            algorithm_infos = []
            
            for name in dir(module):
                obj = getattr(module, name)
                
                # Check if it's a class that has the required attributes for a KA
                if (isinstance(obj, type) and 
                    hasattr(obj, 'KA_ID') and 
                    hasattr(obj, 'execute')):
                    
                    # Get algorithm metadata
                    ka_id = getattr(obj, 'KA_ID')
                    name = getattr(obj, 'NAME', name)
                    version = getattr(obj, 'VERSION', '1.0.0')
                    description = getattr(obj, 'DESCRIPTION', '')
                    input_schema = getattr(obj, 'INPUT_SCHEMA', {})
                    output_schema = getattr(obj, 'OUTPUT_SCHEMA', {})
                    metadata = getattr(obj, 'METADATA', {})
                    
                    # Create algorithm info dictionary
                    alg_info = {
                        'ka_id': ka_id,
                        'name': name,
                        'description': description,
                        'version': version,
                        'input_schema': input_schema,
                        'output_schema': output_schema,
                        'metadata': metadata,
                        'source': 'filesystem',
                        'module_path': module_path,
                        'class_name': name,
                        'instance': None
                    }
                    
                    algorithm_infos.append(alg_info)
            
            return algorithm_infos
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] KAEngine: Error inspecting algorithm module {module_path}: {str(e)}")
            return []
    
    def execute_algorithm(self, ka_id: str, input_data: Dict, session_id: Optional[str] = None,
                        pass_num: int = 0, layer_num: int = 0) -> Dict:
        """
        Execute a Knowledge Algorithm.
        
        Args:
            ka_id: Algorithm ID
            input_data: Input data for the algorithm
            session_id: Optional session ID
            pass_num: Simulation pass number
            layer_num: Simulation layer number
            
        Returns:
            dict: Algorithm execution results
        """
        # Check if algorithm exists
        if ka_id not in self.registered_algorithms:
            return {
                'error': f"Algorithm not found: {ka_id}",
                'status': 'error'
            }
        
        alg_info = self.registered_algorithms[ka_id]
        
        # Prepare execution record
        execution_start_time = datetime.now()
        execution_id = f"KAEX_{ka_id}_{str(uuid.uuid4())[:8]}"
        
        # Create execution record in database if memory manager is available
        if self.memory_manager and session_id:
            execution_record = {
                'execution_id': execution_id,
                'ka_id': ka_id,
                'session_id': session_id,
                'pass_num': pass_num,
                'layer_num': layer_num,
                'input_data': input_data,
                'status': 'running',
                'start_time': execution_start_time.isoformat()
            }
            
            # Add execution record to memory
            self.memory_manager.add_memory_entry(
                session_id=session_id,
                entry_type='ka_execution_start',
                content=execution_record,
                pass_num=pass_num,
                layer_num=layer_num
            )
        
        try:
            # Load algorithm instance if needed
            instance = alg_info.get('instance')
            
            if not instance:
                # Create instance
                instance = self._create_algorithm_instance(ka_id)
                if not instance:
                    raise Exception(f"Failed to create algorithm instance for {ka_id}")
                
                # Store instance for reuse
                alg_info['instance'] = instance
            
            # Execute the algorithm
            logging.info(f"[{datetime.now()}] KAEngine: Executing algorithm {ka_id}")
            result = instance.execute(input_data)
            
            # Calculate execution time
            execution_time = (datetime.now() - execution_start_time).total_seconds() * 1000  # ms
            
            # Process result
            if not isinstance(result, dict):
                result = {'result': result}
            
            # Add execution metadata
            result['execution_id'] = execution_id
            result['ka_id'] = ka_id
            result['execution_time'] = execution_time
            result['status'] = 'success'
            
            # Record execution result in database if memory manager is available
            if self.memory_manager and session_id:
                execution_record.update({
                    'output_data': result,
                    'execution_time': execution_time,
                    'status': 'success',
                    'end_time': datetime.now().isoformat()
                })
                
                # Add execution result to memory
                self.memory_manager.add_memory_entry(
                    session_id=session_id,
                    entry_type='ka_execution_complete',
                    content=execution_record,
                    pass_num=pass_num,
                    layer_num=layer_num,
                    confidence=result.get('confidence', 0.0)
                )
            
            return result
        
        except Exception as e:
            logging.error(f"[{datetime.now()}] KAEngine: Error executing algorithm {ka_id}: {str(e)}")
            
            error_result = {
                'execution_id': execution_id,
                'ka_id': ka_id,
                'status': 'error',
                'error': str(e),
                'execution_time': (datetime.now() - execution_start_time).total_seconds() * 1000  # ms
            }
            
            # Record execution error in database if memory manager is available
            if self.memory_manager and session_id:
                execution_record.update({
                    'output_data': error_result,
                    'status': 'error',
                    'error_message': str(e),
                    'end_time': datetime.now().isoformat()
                })
                
                # Add execution error to memory
                self.memory_manager.add_memory_entry(
                    session_id=session_id,
                    entry_type='ka_execution_error',
                    content=execution_record,
                    pass_num=pass_num,
                    layer_num=layer_num,
                    confidence=0.0
                )
            
            return error_result
    
    def _create_algorithm_instance(self, ka_id: str) -> Any:
        """
        Create an instance of a Knowledge Algorithm.
        
        Args:
            ka_id: Algorithm ID
            
        Returns:
            Any: Algorithm instance
        """
        alg_info = self.registered_algorithms.get(ka_id)
        if not alg_info:
            return None
        
        try:
            # If the algorithm is from the database, we need to load it from the filesystem
            if alg_info.get('source') == 'database':
                # Use the graph database to get implementation details
                if self.graph_manager:
                    # Look for the algorithm implementation edge
                    module_info = None
                    # In a full implementation, we would use the graph database to get the module path
                    # For now, assume it's in the standard location
                    
                    if not module_info:
                        # If no implementation edge found, use default location
                        module_name = f"algorithm_{ka_id}"
                        module_path = os.path.join(self.ka_directory, f"{module_name}.py")
                        
                        # Check if file exists
                        if not os.path.exists(module_path):
                            raise Exception(f"Algorithm implementation not found for {ka_id}")
                        
                        alg_info['module_path'] = module_path
                        alg_info['class_name'] = f"Algorithm{ka_id}"
            
            # Load module
            if not alg_info.get('module_path'):
                raise Exception(f"Module path not specified for algorithm {ka_id}")
            
            module_path = alg_info['module_path']
            module_name = os.path.splitext(os.path.basename(module_path))[0]
            
            # Load module spec
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                raise Exception(f"Could not load module spec for {module_path}")
            
            # Import the module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the algorithm class
            class_name = alg_info.get('class_name')
            if not class_name:
                raise Exception(f"Class name not specified for algorithm {ka_id}")
            
            algorithm_class = getattr(module, class_name)
            
            # Create an instance
            instance = algorithm_class()
            
            return instance
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] KAEngine: Error creating algorithm instance for {ka_id}: {str(e)}")
            return None
    
    def get_available_algorithms(self) -> List[Dict]:
        """
        Get a list of all available algorithms.
        
        Returns:
            list: List of algorithm info dictionaries
        """
        return [
            {
                'ka_id': alg_info['ka_id'],
                'name': alg_info['name'],
                'description': alg_info['description'],
                'version': alg_info['version'],
                'source': alg_info['source']
            }
            for alg_info in self.registered_algorithms.values()
        ]
    
    def get_algorithms_for_layer(self, layer_num: int) -> List[Dict]:
        """
        Get algorithms applicable to a specific layer.
        
        Args:
            layer_num: Layer number
            
        Returns:
            list: List of algorithm info dictionaries
        """
        # Get algorithm IDs for this layer
        algorithm_ids = self.layer_algorithms.get(layer_num, [])
        
        # Return algorithm info for each ID
        return [
            {
                'ka_id': self.registered_algorithms[ka_id]['ka_id'],
                'name': self.registered_algorithms[ka_id]['name'],
                'description': self.registered_algorithms[ka_id]['description'],
                'version': self.registered_algorithms[ka_id]['version'],
                'source': self.registered_algorithms[ka_id]['source']
            }
            for ka_id in algorithm_ids if ka_id in self.registered_algorithms
        ]
    
    def execute_layer(self, session_id: str, pass_num: int, layer_num: int,
                    query_text: str, prev_layer_results: Optional[Dict] = None) -> Dict:
        """
        Execute all applicable algorithms for a layer.
        
        Args:
            session_id: Session ID
            pass_num: Pass number
            layer_num: Layer number
            query_text: User query text
            prev_layer_results: Results from the previous layer
            
        Returns:
            dict: Layer execution results
        """
        layer_start_time = datetime.now()
        
        logging.info(f"[{datetime.now()}] KAEngine: Executing layer {layer_num} for session {session_id}, pass {pass_num}")
        
        # Get algorithms for this layer
        algorithms = self.get_algorithms_for_layer(layer_num)
        
        if not algorithms:
            logging.warning(f"[{datetime.now()}] KAEngine: No algorithms found for layer {layer_num}")
            return {
                'layer_num': layer_num,
                'pass_num': pass_num,
                'algorithms_executed': 0,
                'confidence': 0.0,
                'message': f"No algorithms available for layer {layer_num}",
                'status': 'warning'
            }
        
        # Prepare input data for algorithms
        base_input_data = {
            'query_text': query_text,
            'session_id': session_id,
            'pass_num': pass_num,
            'layer_num': layer_num,
            'timestamp': datetime.now().isoformat(),
            'prev_layer_results': prev_layer_results
        }
        
        # Execute algorithms
        algorithm_results = []
        overall_confidence = 0.0
        success_count = 0
        
        for alg_info in algorithms:
            ka_id = alg_info['ka_id']
            
            # Execute the algorithm
            result = self.execute_algorithm(
                ka_id=ka_id,
                input_data=base_input_data,
                session_id=session_id,
                pass_num=pass_num,
                layer_num=layer_num
            )
            
            # Add to results
            algorithm_results.append({
                'ka_id': ka_id,
                'name': alg_info['name'],
                'result': result
            })
            
            # Update confidence and success count
            if result.get('status') == 'success':
                success_count += 1
                confidence = result.get('confidence', 0.0)
                overall_confidence = max(overall_confidence, confidence)
        
        # Calculate layer execution time
        layer_duration = (datetime.now() - layer_start_time).total_seconds()
        
        # Compute final result
        # This is a simplified version; in a full implementation, we would combine results in a more sophisticated way
        if success_count == 0:
            final_status = 'error'
            final_message = f"All {len(algorithms)} algorithms failed"
        elif success_count < len(algorithms):
            final_status = 'partial'
            final_message = f"{success_count} of {len(algorithms)} algorithms succeeded"
        else:
            final_status = 'success'
            final_message = f"All {len(algorithms)} algorithms succeeded"
        
        # Aggregate results
        # In a full implementation, we would have more advanced aggregation logic
        aggregated_data = {}
        for alg_result in algorithm_results:
            if alg_result['result'].get('status') == 'success':
                # Merge result data
                result_data = alg_result['result'].get('result', {})
                if isinstance(result_data, dict):
                    aggregated_data.update(result_data)
        
        # Prepare final layer result
        layer_result = {
            'layer_num': layer_num,
            'pass_num': pass_num,
            'confidence': overall_confidence,
            'status': final_status,
            'message': final_message,
            'duration': layer_duration,
            'algorithms_executed': len(algorithms),
            'algorithms_succeeded': success_count,
            'algorithm_results': algorithm_results,
            'aggregated_data': aggregated_data
        }
        
        logging.info(f"[{datetime.now()}] KAEngine: Completed layer {layer_num} with confidence {overall_confidence:.4f}, status {final_status}")
        
        return layer_result
    
    def get_algorithm_info(self, ka_id: str) -> Optional[Dict]:
        """
        Get information about a specific algorithm.
        
        Args:
            ka_id: Algorithm ID
            
        Returns:
            dict: Algorithm info or None if not found
        """
        alg_info = self.registered_algorithms.get(ka_id)
        
        if not alg_info:
            return None
        
        return {
            'ka_id': alg_info['ka_id'],
            'name': alg_info['name'],
            'description': alg_info['description'],
            'version': alg_info['version'],
            'input_schema': alg_info['input_schema'],
            'output_schema': alg_info['output_schema'],
            'source': alg_info['source'],
            'metadata': alg_info.get('metadata', {})
        }