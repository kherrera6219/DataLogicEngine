"""
Universal Knowledge Graph (UKG) System - Knowledge Algorithm Integration

This module provides the integration layer between the UKG Knowledge Algorithms (KA)
and the Nested Layered In-Memory Simulation Management System.
"""

import logging
from typing import Dict, List, Any, Optional
import time

from knowledge_algorithms.ka_master_controller import create_master_controller

logger = logging.getLogger(__name__)

class KASystemIntegration:
    """
    Integrates the Knowledge Algorithms (KA) system with the UKG Simulation Layers.
    
    This connector enables the Nested Layered In-Memory Simulation Management System
    to leverage the specialized processing capabilities of the Knowledge Algorithms.
    """
    
    def __init__(self):
        """Initialize the Knowledge Algorithm System Integration."""
        self.controller = create_master_controller()
        self.available_algorithms = {
            algo['algorithm']: algo 
            for algo in self.controller.get_available_algorithms()
        }
        logger.info(f"KA System Integration initialized with {len(self.available_algorithms)} algorithms")
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query through the Knowledge Algorithms system.
        
        Args:
            query: The query text
            context: Optional context information
            
        Returns:
            The processing results
        """
        context = context or {}
        
        # Determine whether to use individual algorithms or pipeline
        use_pipeline = context.get("use_pipeline", True)
        
        if use_pipeline:
            return self._process_with_pipeline(query, context)
        else:
            return self._process_with_individual_algorithms(query, context)
    
    def _process_with_pipeline(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query using the KA pipeline.
        
        Args:
            query: The query text
            context: Context information
            
        Returns:
            The pipeline results
        """
        logger.info(f"Processing query with KA pipeline: \"{query}\"")
        
        # Define standard pipeline steps
        pipeline = [
            {"algorithm": 1},  # KA-1: Semantic Mapping
            {"algorithm": 4},  # KA-4: Honeycomb Expansion
            {"algorithm": 20}  # KA-20: Quad Persona Orchestration
        ]
        
        # Prepare initial input data
        initial_data = {
            "query": query,
            "context": context
        }
        
        # Run the pipeline
        start_time = time.time()
        result = self.controller.run_pipeline(pipeline, initial_data)
        end_time = time.time()
        
        # Add execution metadata
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        result["execution_time_ms"] = execution_time
        
        # Extract key information for simulation layer
        result["ka_system_summary"] = self._create_system_summary(result)
        
        return result
    
    def _process_with_individual_algorithms(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query using individual KA components.
        
        Args:
            query: The query text
            context: Context information
            
        Returns:
            The combined results
        """
        logger.info(f"Processing query with individual KAs: \"{query}\"")
        
        # Specify which algorithms to run
        algorithm_numbers = context.get("algorithms", [1, 4, 20])
        
        # Run each algorithm
        results = {}
        start_time = time.time()
        
        for ka_number in algorithm_numbers:
            ka_id = f"KA-{ka_number}"
            
            if ka_id not in self.available_algorithms:
                logger.warning(f"Skipping unavailable algorithm: {ka_id}")
                continue
            
            # Prepare input data
            input_data = {
                "query": query,
                "context": context
            }
            
            # Run the algorithm
            result = self.controller.run_algorithm(ka_number, input_data)
            results[ka_id] = result
        
        end_time = time.time()
        
        # Combine results
        combined_result = {
            "query": query,
            "context": context,
            "algorithm_results": results,
            "execution_time_ms": (end_time - start_time) * 1000
        }
        
        # Add summary
        combined_result["ka_system_summary"] = self._create_individual_summary(combined_result)
        
        return combined_result
    
    def _create_system_summary(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of pipeline results for use by simulation layers.
        
        Args:
            pipeline_result: The pipeline result
            
        Returns:
            A summary dictionary
        """
        # Start with basic information
        summary = {
            "success": pipeline_result.get("success", False),
            "execution_time_ms": pipeline_result.get("execution_time_ms", 0)
        }
        
        # Extract final result
        final_result = pipeline_result.get("final_result", {})
        
        # Get domain and context from semantic mapping (first step)
        pipeline_steps = pipeline_result.get("pipeline_results", [])
        if pipeline_steps and len(pipeline_steps) > 0:
            ka1_result = pipeline_steps[0].get("result", {})
            if "domain" in ka1_result:
                summary["domain"] = ka1_result["domain"]
            if "pillar_levels" in ka1_result:
                summary["pillar_levels"] = ka1_result["pillar_levels"]
            if "axes" in ka1_result:
                summary["axes"] = ka1_result["axes"]
        
        # Get cross-domain insights from honeycomb expansion (second step)
        if pipeline_steps and len(pipeline_steps) > 1:
            ka4_result = pipeline_steps[1].get("result", {})
            if "related_sectors" in ka4_result:
                summary["related_sectors"] = ka4_result["related_sectors"]
        
        # Get expert analysis from quad persona (third step)
        if pipeline_steps and len(pipeline_steps) > 2:
            ka20_result = pipeline_steps[2].get("result", {})
            if "active_personas" in ka20_result:
                summary["active_personas"] = ka20_result["active_personas"]
        
        # Extract integrated response
        if "integrated_result" in final_result:
            summary["integrated_response"] = final_result["integrated_result"].get("response", "")
            summary["confidence"] = final_result["integrated_result"].get("confidence", 0)
        
        return summary
    
    def _create_individual_summary(self, combined_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of individual algorithm results.
        
        Args:
            combined_result: The combined results
            
        Returns:
            A summary dictionary
        """
        summary = {
            "execution_time_ms": combined_result.get("execution_time_ms", 0)
        }
        
        algorithm_results = combined_result.get("algorithm_results", {})
        
        # Extract domain and context from KA-1 (if available)
        if "KA-1" in algorithm_results:
            ka1_result = algorithm_results["KA-1"]
            if "domain" in ka1_result:
                summary["domain"] = ka1_result["domain"]
            if "pillar_levels" in ka1_result:
                summary["pillar_levels"] = ka1_result["pillar_levels"]
            if "axes" in ka1_result:
                summary["axes"] = ka1_result["axes"]
        
        # Extract cross-domain insights from KA-4 (if available)
        if "KA-4" in algorithm_results:
            ka4_result = algorithm_results["KA-4"]
            if "related_sectors" in ka4_result:
                summary["related_sectors"] = ka4_result["related_sectors"]
        
        # Extract expert analysis from KA-20 (if available)
        if "KA-20" in algorithm_results:
            ka20_result = algorithm_results["KA-20"]
            if "active_personas" in ka20_result:
                summary["active_personas"] = ka20_result["active_personas"]
            
            # Extract integrated response
            if "integrated_result" in ka20_result:
                summary["integrated_response"] = ka20_result["integrated_result"].get("response", "")
                summary["confidence"] = ka20_result["integrated_result"].get("confidence", 0)
        
        return summary

# Singleton instance for global access
_ka_integration = None

def get_ka_integration() -> KASystemIntegration:
    """
    Get the singleton KA System Integration instance.
    
    Returns:
        The KASystemIntegration instance
    """
    global _ka_integration
    
    if _ka_integration is None:
        _ka_integration = KASystemIntegration()
    
    return _ka_integration