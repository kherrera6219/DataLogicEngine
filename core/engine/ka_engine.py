"""
Knowledge Algorithm Engine

This module provides the core functionality for managing and executing
Knowledge Algorithms (KAs) within the UKG system.
"""

import logging
import json
import uuid
import importlib
import os
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

class KAEngine:
    """
    Knowledge Algorithm Engine
    
    This component manages the registration, execution, and tracking of
    Knowledge Algorithms (KAs) in the UKG system.
    """
    
    def __init__(self, config=None, graph_manager=None, memory_manager=None):
        """
        Initialize the KA Engine.
        
        Args:
            config (dict, optional): Configuration dictionary
            graph_manager: Graph Manager instance
            memory_manager: Memory Manager instance
        """
        logging.info(f"[{datetime.now()}] Initializing KAEngine...")
        self.config = config or {}
        self.graph_manager = graph_manager
        self.memory_manager = memory_manager
        
        # KA registry
        self.ka_registry = {}
        
        # Load KA configurations
        self._load_ka_registry()
        
        # Execution history
        self.execution_history = []
        
        # Stats
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0
        }
        
        logging.info(f"[{datetime.now()}] KAEngine initialized with {len(self.ka_registry)} KAs registered")
    
    def _load_ka_registry(self):
        """
        Load Knowledge Algorithm registry from configuration files.
        """
        # Get the KA registry path
        registry_path = self.config.get('ka_registry_path', 'knowledge_algorithms/ka_registry.yaml')
        
        try:
            # Check if file exists
            if not os.path.exists(registry_path):
                logging.warning(f"[{datetime.now()}] KA registry file not found: {registry_path}")
                return
            
            # Load the registry
            with open(registry_path, 'r') as f:
                ka_config = yaml.safe_load(f)
            
            # Process each KA
            for ka_id, ka_info in ka_config.get('algorithms', {}).items():
                self.register_algorithm(
                    ka_id=ka_id,
                    name=ka_info.get('name'),
                    description=ka_info.get('description'),
                    module_path=ka_info.get('module_path'),
                    class_name=ka_info.get('class_name'),
                    version=ka_info.get('version', '1.0.0'),
                    parameters=ka_info.get('parameters', {})
                )
            
            logging.info(f"[{datetime.now()}] Loaded {len(self.ka_registry)} KAs from registry")
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error loading KA registry: {str(e)}")
    
    def register_algorithm(self, ka_id: str, name: str, description: str, 
                         module_path: str, class_name: str, version: str = '1.0.0',
                         parameters: Dict = None) -> bool:
        """
        Register a Knowledge Algorithm.
        
        Args:
            ka_id: Algorithm ID
            name: Algorithm name
            description: Algorithm description
            module_path: Python module path
            class_name: Algorithm class name
            version: Algorithm version
            parameters: Parameter defaults
            
        Returns:
            bool: True if registration was successful
        """
        # Check if already registered
        if ka_id in self.ka_registry:
            logging.warning(f"[{datetime.now()}] KA with ID {ka_id} already registered")
            return False
        
        # Create KA entry
        ka_entry = {
            'ka_id': ka_id,
            'name': name,
            'description': description,
            'module_path': module_path,
            'class_name': class_name,
            'version': version,
            'parameters': parameters or {},
            'registered_at': datetime.now().isoformat(),
            'instance': None
        }
        
        # Add to registry
        self.ka_registry[ka_id] = ka_entry
        logging.info(f"[{datetime.now()}] Registered KA: {ka_id} - {name} (v{version})")
        
        return True
    
    def get_algorithm_info(self, ka_id: str) -> Optional[Dict]:
        """
        Get information about a registered Knowledge Algorithm.
        
        Args:
            ka_id: Algorithm ID
            
        Returns:
            dict: Algorithm information or None if not found
        """
        if ka_id not in self.ka_registry:
            return None
        
        # Return a copy without the instance
        ka_info = self.ka_registry[ka_id].copy()
        ka_info.pop('instance', None)
        
        return ka_info
    
    def list_algorithms(self) -> List[Dict]:
        """
        List all registered Knowledge Algorithms.
        
        Returns:
            list: List of algorithm information dictionaries
        """
        result = []
        
        for ka_id, ka_info in self.ka_registry.items():
            # Create a copy without the instance
            info = ka_info.copy()
            info.pop('instance', None)
            result.append(info)
        
        return result
    
    def execute_algorithm(self, ka_id: str, params: Optional[Dict] = None, 
                        session_id: Optional[str] = None) -> Dict:
        """
        Execute a Knowledge Algorithm.
        
        Args:
            ka_id: Algorithm ID
            params: Execution parameters
            session_id: Optional session ID
            
        Returns:
            dict: Execution results
        """
        execution_id = f"EXEC_{ka_id}_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        # Initialize execution record
        execution_record = {
            'execution_id': execution_id,
            'ka_id': ka_id,
            'session_id': session_id,
            'params': params or {},
            'status': 'started',
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_ms': None,
            'results': None,
            'error': None
        }
        
        # Check if KA exists
        if ka_id not in self.ka_registry:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            execution_record.update({
                'status': 'failed',
                'end_time': end_time.isoformat(),
                'duration_ms': duration,
                'error': f"KA with ID {ka_id} not found"
            })
            
            self.execution_history.append(execution_record)
            self.stats['total_executions'] += 1
            self.stats['failed_executions'] += 1
            
            return execution_record
        
        try:
            # Get KA info
            ka_info = self.ka_registry[ka_id]
            
            # Load KA class if not already loaded
            if not ka_info.get('instance'):
                module = importlib.import_module(ka_info['module_path'])
                ka_class = getattr(module, ka_info['class_name'])
                
                # Initialize with dependencies
                ka_instance = ka_class(
                    graph_manager=self.graph_manager,
                    memory_manager=self.memory_manager
                )
                
                ka_info['instance'] = ka_instance
            
            # Merge parameters with defaults
            merged_params = ka_info['parameters'].copy()
            if params:
                merged_params.update(params)
            
            # Execute the algorithm
            results = ka_info['instance'].execute(
                execution_id=execution_id,
                params=merged_params,
                session_id=session_id
            )
            
            # Record successful execution
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            execution_record.update({
                'status': 'completed',
                'end_time': end_time.isoformat(),
                'duration_ms': duration,
                'results': results
            })
            
            self.stats['total_executions'] += 1
            self.stats['successful_executions'] += 1
            
        except Exception as e:
            # Record failed execution
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            execution_record.update({
                'status': 'failed',
                'end_time': end_time.isoformat(),
                'duration_ms': duration,
                'error': str(e)
            })
            
            self.stats['total_executions'] += 1
            self.stats['failed_executions'] += 1
            
            logging.error(f"[{datetime.now()}] Error executing KA {ka_id}: {str(e)}")
        
        # Add to execution history
        self.execution_history.append(execution_record)
        
        # Update execution record in database if connected
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.create_ka_execution(execution_record)
        
        return execution_record
    
    def execute_pipeline(self, pipeline: List[Dict], session_id: Optional[str] = None) -> Dict:
        """
        Execute a pipeline of Knowledge Algorithms.
        
        Args:
            pipeline: List of pipeline steps with 'ka_id' and 'params'
            session_id: Optional session ID
            
        Returns:
            dict: Pipeline execution results
        """
        pipeline_id = f"PIPE_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"
        start_time = datetime.now()
        
        # Initialize pipeline results
        pipeline_results = {
            'pipeline_id': pipeline_id,
            'session_id': session_id,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration_ms': None,
            'steps': [],
            'overall_status': 'started',
            'error': None
        }
        
        try:
            # Execute each step in the pipeline
            for i, step in enumerate(pipeline):
                ka_id = step.get('ka_id')
                params = step.get('params', {})
                
                if not ka_id:
                    raise ValueError(f"Pipeline step {i+1} missing required 'ka_id'")
                
                # Execute the algorithm
                execution_result = self.execute_algorithm(
                    ka_id=ka_id,
                    params=params,
                    session_id=session_id
                )
                
                # Add to pipeline steps
                pipeline_results['steps'].append(execution_result)
                
                # If step failed and not configured to continue on failure, stop pipeline
                if execution_result['status'] == 'failed' and not step.get('continue_on_failure', False):
                    pipeline_results['overall_status'] = 'failed'
                    pipeline_results['error'] = f"Pipeline failed at step {i+1}: {execution_result['error']}"
                    break
            
            # If we completed all steps and haven't already marked as failed
            if pipeline_results['overall_status'] != 'failed':
                pipeline_results['overall_status'] = 'completed'
            
        except Exception as e:
            pipeline_results['overall_status'] = 'failed'
            pipeline_results['error'] = str(e)
            logging.error(f"[{datetime.now()}] Error executing pipeline: {str(e)}")
        
        # Record end time and duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000
        
        pipeline_results['end_time'] = end_time.isoformat()
        pipeline_results['duration_ms'] = duration
        
        return pipeline_results
    
    def get_execution_history(self, ka_id: Optional[str] = None, 
                           session_id: Optional[str] = None,
                           limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get execution history for Knowledge Algorithms.
        
        Args:
            ka_id: Optional Algorithm ID to filter by
            session_id: Optional session ID to filter by
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            list: List of execution records
        """
        # If connected to database, query from there
        if hasattr(self, 'db_manager') and self.db_manager:
            filters = {}
            if ka_id:
                filters['ka_id'] = ka_id
            if session_id:
                filters['session_id'] = session_id
            
            return self.db_manager.get_ka_executions(filters, limit, offset)
        
        # Otherwise, use in-memory history
        filtered = self.execution_history
        
        if ka_id:
            filtered = [r for r in filtered if r.get('ka_id') == ka_id]
        
        if session_id:
            filtered = [r for r in filtered if r.get('session_id') == session_id]
        
        # Apply pagination
        paginated = filtered[offset:offset+limit]
        
        return paginated
    
    def clear_execution_history(self) -> bool:
        """
        Clear execution history.
        
        Returns:
            bool: True if successful
        """
        self.execution_history = []
        return True
    
    def get_algorithm_stats(self, ka_id: Optional[str] = None) -> Dict:
        """
        Get execution statistics for Knowledge Algorithms.
        
        Args:
            ka_id: Optional Algorithm ID to filter by
            
        Returns:
            dict: Statistics dictionary
        """
        if not ka_id:
            return self.stats
        
        # Calculate stats for a specific KA
        executions = [r for r in self.execution_history if r.get('ka_id') == ka_id]
        
        total = len(executions)
        successful = len([r for r in executions if r.get('status') == 'completed'])
        failed = len([r for r in executions if r.get('status') == 'failed'])
        
        avg_duration = 0
        if total > 0:
            durations = [r.get('duration_ms', 0) for r in executions]
            avg_duration = sum(durations) / total
        
        return {
            'ka_id': ka_id,
            'total_executions': total,
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': (successful / total) * 100 if total > 0 else 0,
            'avg_duration_ms': avg_duration
        }