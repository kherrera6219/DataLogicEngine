from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
from datetime import datetime

class KnowledgeAlgorithm(ABC):
    """
    Base class for all Knowledge Algorithms (KAs).
    
    KAs are specialized algorithms that perform specific tasks within the UKG system.
    They can access the UKG, memory store, and other system components to perform
    their tasks.
    """
    
    def __init__(self, config, graph_manager, memory_manager, united_system_manager):
        """
        Initialize the Knowledge Algorithm.
        
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
        self.ka_name = self.__class__.__name__
    
    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Knowledge Algorithm.
        
        Args:
            input_data (dict): Input data for the KA
            
        Returns:
            dict: The result of the KA execution
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: list) -> bool:
        """
        Validate that the input data contains all required fields.
        
        Args:
            input_data (dict): Input data to validate
            required_fields (list): List of required field names
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not input_data or not isinstance(input_data, dict):
            logging.error(f"[{datetime.now()}] {self.ka_name}: Input data is not a dictionary")
            return False
        
        for field in required_fields:
            if field not in input_data:
                logging.error(f"[{datetime.now()}] {self.ka_name}: Required field '{field}' missing from input")
                return False
        
        return True
    
    def log_execution_step(self, step_name: str, details: Dict[str, Any] = None):
        """
        Log an execution step for debugging and tracing.
        
        Args:
            step_name (str): Name of the execution step
            details (dict, optional): Additional details to log
        """
        log_message = f"{self.ka_name}: {step_name}"
        if details:
            log_message += f" - {details}"
        logging.debug(f"[{datetime.now()}] {log_message}")
    
    def calculate_confidence(self, confidence_factors: Dict[str, float], weights: Dict[str, float] = None) -> float:
        """
        Calculate an overall confidence score from individual factors.
        
        Args:
            confidence_factors (dict): Dictionary of confidence factors (name -> score)
            weights (dict, optional): Dictionary of weights for each factor (name -> weight)
            
        Returns:
            float: The calculated confidence score (0.0 to 1.0)
        """
        if not confidence_factors:
            return 0.5  # Default mid-range confidence
        
        if not weights:
            # Equal weights if not specified
            weights = {name: 1.0 / len(confidence_factors) for name in confidence_factors}
        
        # Calculate weighted average
        total_weight = sum(weights.get(name, 1.0) for name in confidence_factors)
        if total_weight == 0:
            return 0.5  # Avoid division by zero
        
        weighted_sum = sum(
            confidence_factors[name] * weights.get(name, 1.0)
            for name in confidence_factors
        )
        
        confidence = weighted_sum / total_weight
        
        # Ensure result is between 0 and 1
        return max(0.0, min(1.0, confidence))
