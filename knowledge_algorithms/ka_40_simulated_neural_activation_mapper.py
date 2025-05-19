"""
KA-40: Simulated Neural Activation Mapper

This algorithm simulates neural-like activation patterns across input tokens,
mapping conceptual relationships in a simplified neural network style.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import time
import random
import math

logger = logging.getLogger(__name__)

class SimulatedNeuralActivationMapper:
    """
    KA-40: Maps simulated neural activations across input tokens.
    
    This algorithm creates a simplified neural activation map for inputs,
    simulating how concepts might activate related neurons in a network.
    """
    
    def __init__(self):
        """Initialize the Simulated Neural Activation Mapper."""
        self.neuron_types = self._initialize_neuron_types()
        self.activation_functions = self._initialize_activation_functions()
        logger.info("KA-40: Simulated Neural Activation Mapper initialized")
    
    def _initialize_neuron_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize different types of simulated neurons."""
        return {
            "concept": {
                "description": "Represents high-level conceptual understanding",
                "activation_threshold": 0.6,
                "decay_rate": 0.1,
                "connections": "semantic"
            },
            "pattern": {
                "description": "Recognizes patterns in input sequences",
                "activation_threshold": 0.4,
                "decay_rate": 0.2,
                "connections": "sequential"
            },
            "feature": {
                "description": "Extracts specific features from inputs",
                "activation_threshold": 0.3,
                "decay_rate": 0.15,
                "connections": "hierarchical"
            },
            "context": {
                "description": "Maintains context across inputs",
                "activation_threshold": 0.5,
                "decay_rate": 0.05,
                "connections": "recurrent"
            },
            "memory": {
                "description": "Stores and recalls previous inputs",
                "activation_threshold": 0.7,
                "decay_rate": 0.01,
                "connections": "associative"
            }
        }
    
    def _initialize_activation_functions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize activation functions for neurons."""
        return {
            "sigmoid": {
                "description": "Standard sigmoid activation function",
                "formula": lambda x: 1 / (1 + math.exp(-x)),
                "derivative": lambda x: x * (1 - x)
            },
            "relu": {
                "description": "Rectified Linear Unit",
                "formula": lambda x: max(0, x),
                "derivative": lambda x: 1 if x > 0 else 0
            },
            "tanh": {
                "description": "Hyperbolic tangent activation",
                "formula": lambda x: math.tanh(x),
                "derivative": lambda x: 1 - x**2
            },
            "leaky_relu": {
                "description": "Leaky Rectified Linear Unit",
                "formula": lambda x: max(0.1 * x, x),
                "derivative": lambda x: 1 if x > 0 else 0.1
            },
            "gaussian": {
                "description": "Gaussian activation for radial basis functions",
                "formula": lambda x: math.exp(-(x**2)),
                "derivative": lambda x: -2 * x * math.exp(-(x**2))
            }
        }
    
    def map_activations(self, input_tokens: List[str], 
                       activation_function: str = "sigmoid",
                       neuron_count: int = 10,
                       seed_value: Optional[int] = None) -> Dict[str, Any]:
        """
        Map simulated neural activations for input tokens.
        
        Args:
            input_tokens: List of input tokens to process
            activation_function: Name of activation function to use
            neuron_count: Number of neurons per token
            seed_value: Optional seed for reproducibility
            
        Returns:
            Dictionary with neural activation mapping
        """
        # Set random seed if provided
        if seed_value is not None:
            random.seed(seed_value)
        
        # Validate inputs
        if not input_tokens:
            return {
                "error": "No input tokens provided",
                "success": False
            }
        
        # Get activation function
        if activation_function not in self.activation_functions:
            activation_function = "sigmoid"  # Default to sigmoid
        
        activation_func = self.activation_functions[activation_function]["formula"]
        
        # Generate neurons
        neurons = []
        for i in range(len(input_tokens)):
            token = input_tokens[i]
            token_neurons = []
            
            # Create neurons for this token
            for j in range(neuron_count):
                # Determine neuron type
                neuron_type = random.choice(list(self.neuron_types.keys()))
                neuron_info = self.neuron_types[neuron_type]
                
                # Calculate base activation
                # This would involve complex neural modeling in a real system
                # For simulation, we'll use token characteristics + randomness
                token_weight = (len(token) % 5) / 10 + 0.5  # Token-based weight
                position_weight = (i / len(input_tokens)) * 0.5  # Position-based weight
                random_component = random.random() * 0.3  # Random component
                
                base_activation = token_weight + position_weight + random_component
                
                # Apply activation function
                activation = activation_func(base_activation)
                
                # Round to reasonable precision
                activation = round(activation, 4)
                
                # Create neuron
                neuron = {
                    "id": f"neuron_{i}_{j}",
                    "token": token,
                    "token_index": i,
                    "neuron_index": j,
                    "type": neuron_type,
                    "activation": activation,
                    "threshold": neuron_info["activation_threshold"]
                }
                
                token_neurons.append(neuron)
            
            neurons.append(token_neurons)
        
        # Generate connections between neurons
        connections = self._generate_connections(neurons)
        
        # Calculate network properties
        network_properties = self._calculate_network_properties(neurons, connections)
        
        # Create activation map
        activation_map = {
            "input_tokens": input_tokens,
            "neuron_count": neuron_count,
            "activation_function": activation_function,
            "neurons": neurons,
            "connections": connections,
            "network_properties": network_properties
        }
        
        return activation_map
    
    def _generate_connections(self, neurons: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Generate connections between neurons.
        
        Args:
            neurons: Nested list of neuron dictionaries
            
        Returns:
            List of connection dictionaries
        """
        connections = []
        
        # Flatten neurons for easier processing
        flat_neurons = [neuron for token_neurons in neurons for neuron in token_neurons]
        
        # Generate connections
        for i, source_neuron in enumerate(flat_neurons):
            # Determine number of connections for this neuron
            connection_count = random.randint(1, min(5, len(flat_neurons) // 4))
            
            # Create connections
            for _ in range(connection_count):
                # Select random target neuron (that's not the source)
                target_indices = [j for j in range(len(flat_neurons)) if j != i]
                if not target_indices:
                    continue
                
                target_index = random.choice(target_indices)
                target_neuron = flat_neurons[target_index]
                
                # Calculate connection weight
                # Again, this would be complex in a real system
                # For simulation, we'll use neuron properties + randomness
                type_compatibility = 0.5  # Base compatibility
                if source_neuron["type"] == target_neuron["type"]:
                    type_compatibility = 0.8  # Same type bonus
                
                activation_similarity = 1 - abs(source_neuron["activation"] - target_neuron["activation"])
                
                random_component = random.random() * 0.4
                
                weight = (type_compatibility + activation_similarity + random_component) / 3
                weight = round(weight, 4)
                
                # Create connection
                connection = {
                    "source": source_neuron["id"],
                    "target": target_neuron["id"],
                    "weight": weight,
                    "type": "excitatory" if weight > 0.5 else "inhibitory"
                }
                
                connections.append(connection)
        
        return connections
    
    def _calculate_network_properties(self, neurons: List[List[Dict[str, Any]]], 
                                   connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate properties of the neural network.
        
        Args:
            neurons: Nested list of neuron dictionaries
            connections: List of connection dictionaries
            
        Returns:
            Dictionary with network properties
        """
        # Flatten neurons for easier processing
        flat_neurons = [neuron for token_neurons in neurons for neuron in token_neurons]
        
        # Count neurons by type
        neuron_type_counts = {}
        for neuron in flat_neurons:
            neuron_type = neuron["type"]
            neuron_type_counts[neuron_type] = neuron_type_counts.get(neuron_type, 0) + 1
        
        # Calculate average activation
        total_activation = sum(neuron["activation"] for neuron in flat_neurons)
        avg_activation = total_activation / len(flat_neurons) if flat_neurons else 0
        
        # Calculate connection density
        max_connections = len(flat_neurons) * (len(flat_neurons) - 1)
        connection_density = len(connections) / max_connections if max_connections > 0 else 0
        
        # Count connection types
        excitatory_count = sum(1 for conn in connections if conn["type"] == "excitatory")
        inhibitory_count = len(connections) - excitatory_count
        
        # Calculate network properties
        network_properties = {
            "neuron_count": len(flat_neurons),
            "connection_count": len(connections),
            "neuron_type_distribution": neuron_type_counts,
            "average_activation": round(avg_activation, 4),
            "connection_density": round(connection_density, 4),
            "excitatory_connections": excitatory_count,
            "inhibitory_connections": inhibitory_count,
            "excitatory_ratio": round(excitatory_count / len(connections), 4) if connections else 0
        }
        
        return network_properties


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Simulated Neural Activation Mapper (KA-40) on the provided data.
    
    Args:
        data: A dictionary containing input tokens and mapping parameters
        
    Returns:
        Dictionary with neural activation mapping
    """
    input_tokens = data.get("input_tokens", [])
    activation_function = data.get("activation_function", "sigmoid")
    neuron_count = data.get("neuron_count", 5)
    seed_value = data.get("seed_value")
    
    mapper = SimulatedNeuralActivationMapper()
    result = mapper.map_activations(input_tokens, activation_function, neuron_count, seed_value)
    
    # If error occurred
    if "error" in result:
        return {
            "algorithm": "KA-40",
            "error": result["error"],
            "success": False
        }
    
    # Extract a simplified view for the result
    activations = []
    for token_neurons in result["neurons"]:
        token_activations = [neuron["id"] for neuron in token_neurons]
        activations.extend(token_activations)
    
    return {
        "algorithm": "KA-40",
        "activations": activations,
        "activation_map": result,
        "timestamp": time.time(),
        "success": True
    }