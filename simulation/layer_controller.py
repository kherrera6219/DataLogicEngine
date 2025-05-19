"""
Layer Controller

This module provides the orchestration and coordination between different layers
of the UKG/USKD simulation system. It acts as a central control point for
determining which layers should be activated and in what sequence.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from simulation.pov_engine import POVEngine
from simulation.layer5_integration import Layer5IntegrationEngine
from simulation.layer7_agi_system import AGISimulationEngine

class LayerController:
    """
    Layer Controller
    
    Orchestrates the activation and coordination of different simulation layers
    in the UKG/USKD system. Provides methods to run specific layers or sequences
    of layers based on gatekeeper decisions.
    """
    
    def __init__(self, config=None, system_manager=None):
        """
        Initialize the Layer Controller.
        
        Args:
            config (dict, optional): Configuration dictionary
            system_manager: Optional reference to the United System Manager
        """
        self.config = config or {}
        self.system_manager = system_manager
        
        # Layer instances
        self.pov_engine = None
        self.layer5_engine = None
        self.layer7_engine = None
        
        # Layer activation tracking
        self.active_layers = set()
        self.layer_sequence = []
        
        # Layer results storage
        self.layer_results = {}
        
        logging.info(f"[{datetime.now()}] LayerController initialized")
    
    def initialize_layers(self):
        """
        Initialize layer instances if not already created.
        
        Returns:
            bool: True if all layers initialized successfully
        """
        try:
            # Initialize POV Engine (Layer 4)
            if not self.pov_engine:
                self.pov_engine = POVEngine(config=self.config.get('layer4', {}))
                logging.info(f"[{datetime.now()}] POV Engine (Layer 4) initialized")
            
            # Initialize Layer 5 Integration Engine
            if not self.layer5_engine:
                self.layer5_engine = Layer5IntegrationEngine(
                    config=self.config.get('layer5', {}),
                    system_manager=self.system_manager
                )
                logging.info(f"[{datetime.now()}] Layer 5 Integration Engine initialized")
            
            # Initialize Layer 7 AGI Simulation Engine
            if not self.layer7_engine:
                self.layer7_engine = AGISimulationEngine(
                    config=self.config.get('layer7', {}),
                    system_manager=self.system_manager
                )
                logging.info(f"[{datetime.now()}] Layer 7 AGI Simulation Engine initialized")
            
            return True
        
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error initializing layers: {str(e)}")
            return False
    
    def run_layer(self, layer_num: int, context: Dict) -> Dict:
        """
        Run a specific layer of the simulation system.
        
        Args:
            layer_num: Layer number to run (4-10)
            context: Context information for the layer
            
        Returns:
            dict: Layer processing results
        """
        # Ensure layers are initialized
        if not self.initialize_layers():
            return {'error': 'Failed to initialize layers'}
        
        # Track layer activation
        self.active_layers.add(layer_num)
        self.layer_sequence.append(layer_num)
        
        try:
            # Route to appropriate layer
            if layer_num == 4:
                # Layer 4: POV Engine
                if self.pov_engine:
                    result = self.pov_engine.process(context)
                    self.layer_results[layer_num] = result
                    return result
                else:
                    return {'error': 'POV Engine not initialized'}
            
            elif layer_num == 5:
                # Layer 5: Integration Engine
                if self.layer5_engine:
                    result = self.layer5_engine.process(context)
                    self.layer_results[layer_num] = result
                    return result
                else:
                    return {'error': 'Layer 5 Integration Engine not initialized'}
            
            elif layer_num == 7:
                # Layer 7: AGI Simulation Engine
                if self.layer7_engine:
                    result = self.layer7_engine.process(context, self.pov_engine)
                    self.layer_results[layer_num] = result
                    return result
                else:
                    return {'error': 'Layer 7 AGI Simulation Engine not initialized'}
            
            else:
                # Layers not yet implemented
                logging.warning(f"[{datetime.now()}] Layer {layer_num} not yet implemented")
                return {'error': f'Layer {layer_num} not yet implemented'}
        
        except Exception as e:
            error_msg = f"Error running layer {layer_num}: {str(e)}"
            logging.error(f"[{datetime.now()}] {error_msg}")
            return {'error': error_msg}
    
    def run_layer_sequence(self, active_layers: List[int], context: Dict) -> Dict:
        """
        Run a sequence of layers based on gatekeeper decisions.
        
        Args:
            active_layers: List of layer numbers to activate
            context: Initial context for processing
            
        Returns:
            dict: Combined results from all activated layers
        """
        current_context = context.copy()
        final_result = {'layer_activations': {}}
        
        # If Layer 4 is not in the sequence but others are, add it first
        # as it's often needed for higher layers
        if 4 not in active_layers and active_layers:
            active_layers = [4] + active_layers
        
        # Process each layer in sequence
        for layer_num in sorted(active_layers):
            logging.info(f"[{datetime.now()}] Running Layer {layer_num}")
            
            # Run the layer
            layer_result = self.run_layer(layer_num, current_context)
            
            # Store layer result
            final_result['layer_activations'][f'layer_{layer_num}'] = {
                'activated': True,
                'success': 'error' not in layer_result
            }
            
            # Update context for next layer if successful
            if 'error' not in layer_result:
                current_context.update(layer_result)
        
        # Combine final result
        final_result.update(current_context)
        final_result['active_layers'] = active_layers
        
        return final_result
    
    def get_layer_results(self, layer_num: Optional[int] = None) -> Dict:
        """
        Get results from previous layer runs.
        
        Args:
            layer_num: Optional specific layer to retrieve results for
            
        Returns:
            dict: Layer results
        """
        if layer_num is not None:
            return self.layer_results.get(layer_num, {})
        else:
            return self.layer_results
    
    def get_layer_sequence(self) -> List[int]:
        """
        Get sequence of layer activations.
        
        Returns:
            list: Sequence of layer numbers in order of activation
        """
        return self.layer_sequence
    
    def reset(self):
        """
        Reset the layer controller state.
        """
        self.active_layers = set()
        self.layer_sequence = []
        self.layer_results = {}
        logging.info(f"[{datetime.now()}] LayerController reset")