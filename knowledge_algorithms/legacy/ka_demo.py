"""
Knowledge Algorithms (KA) Demo Script

This script demonstrates the usage of the Knowledge Algorithms in the UKG system,
showing how they can be used individually and as a pipeline to process queries.
"""

import logging
import json
import time
from typing import Dict, Any

from knowledge_algorithms.ka_master_controller import create_master_controller

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_algorithm(controller, ka_number: int, query: str, domain: str = None) -> Dict[str, Any]:
    """
    Test a single Knowledge Algorithm with a query.
    
    Args:
        controller: The KAMasterController instance
        ka_number: The Knowledge Algorithm number to test
        query: The query text
        domain: Optional domain context
        
    Returns:
        The algorithm result
    """
    # Prepare input data
    input_data = {
        "query": query,
        "context": {
            "domain": domain
        } if domain else {}
    }
    
    # Run the algorithm
    logger.info(f"Running KA-{ka_number} with query: \"{query}\"")
    result = controller.run_algorithm(ka_number, input_data)
    
    # Print result summary
    if result.get("success", False):
        confidence = result.get("confidence", 0)
        logger.info(f"KA-{ka_number} executed successfully with confidence: {confidence:.2f}")
    else:
        error = result.get("error", "Unknown error")
        logger.error(f"KA-{ka_number} failed: {error}")
    
    return result

def test_algorithm_pipeline(controller, query: str, domain: str = None) -> Dict[str, Any]:
    """
    Test a pipeline of Knowledge Algorithms.
    
    Args:
        controller: The KAMasterController instance
        query: The query text
        domain: Optional domain context
        
    Returns:
        The pipeline result
    """
    # Define pipeline steps
    pipeline = [
        {"algorithm": 1},  # KA-1: Semantic Mapping
        {"algorithm": 4},  # KA-4: Honeycomb Expansion
        {"algorithm": 20}  # KA-20: Quad Persona Orchestration
    ]
    
    # Prepare initial input data
    initial_data = {
        "query": query,
        "context": {
            "domain": domain
        } if domain else {}
    }
    
    # Run the pipeline
    logger.info(f"Running KA pipeline with query: \"{query}\"")
    start_time = time.time()
    result = controller.run_pipeline(pipeline, initial_data)
    end_time = time.time()
    
    # Print pipeline summary
    if result.get("success", False):
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        logger.info(f"Pipeline executed successfully in {execution_time:.2f}ms")
        
        # Print step summaries
        for step in result.get("pipeline_results", []):
            step_num = step.get("step")
            step_alg = step.get("algorithm")
            step_success = step.get("result", {}).get("success", False)
            logger.info(f"  Step {step_num} ({step_alg}): {'Success' if step_success else 'Failed'}")
    else:
        error = result.get("error", "Unknown error")
        logger.error(f"Pipeline failed: {error}")
    
    return result

def format_result(result: Dict[str, Any], include_details: bool = False) -> str:
    """
    Format a result dictionary for display.
    
    Args:
        result: The result dictionary
        include_details: Whether to include full details
        
    Returns:
        Formatted string representation
    """
    if include_details:
        return json.dumps(result, indent=2)
    
    # Create a simplified summary
    if not result.get("success", False):
        return f"Error: {result.get('error', 'Unknown error')}"
    
    summary = []
    
    # Algorithm type
    algorithm = result.get("algorithm", "Unknown")
    summary.append(f"Algorithm: {algorithm}")
    
    # Execution time
    exec_time = result.get("execution_time_ms", 0)
    if exec_time > 0:
        summary.append(f"Execution time: {exec_time:.2f}ms")
    
    # Confidence
    confidence = result.get("confidence", 0)
    if confidence > 0:
        summary.append(f"Confidence: {confidence:.2f}")
    
    # Query
    query = result.get("query", "")
    if query:
        summary.append(f"Query: \"{query}\"")
    
    # Domain
    domain = result.get("domain", result.get("original_domain", ""))
    if domain:
        summary.append(f"Domain: {domain}")
    
    # For KA-1
    if algorithm == "KA-1":
        pillar_levels = result.get("pillar_levels", [])
        axes = result.get("axes", [])
        coordinates = result.get("coordinates", [])
        
        if pillar_levels:
            summary.append(f"Pillar Levels: {', '.join(pillar_levels)}")
        if axes:
            summary.append(f"Axes: {', '.join(map(str, axes))}")
        if coordinates:
            summary.append(f"Coordinates: {', '.join(coordinates[:3])}" + 
                          (f" (plus {len(coordinates)-3} more)" if len(coordinates) > 3 else ""))
    
    # For KA-4
    elif algorithm == "KA-4":
        concepts = result.get("original_concepts", [])
        related_sectors = result.get("related_sectors", [])
        paths = result.get("honeycomb_paths", [])
        
        if concepts:
            summary.append(f"Key Concepts: {', '.join(concepts)}")
        if related_sectors:
            summary.append(f"Related Sectors: {', '.join(related_sectors[:3])}" + 
                          (f" (plus {len(related_sectors)-3} more)" if len(related_sectors) > 3 else ""))
        if paths:
            summary.append(f"Honeycomb Paths: {len(paths)}")
    
    # For KA-20
    elif algorithm == "KA-20":
        active_personas = result.get("active_personas", [])
        integrated_result = result.get("integrated_result", {})
        
        if active_personas:
            summary.append(f"Active Personas: {', '.join(active_personas)}")
        
        response_preview = integrated_result.get("response", "")
        if response_preview:
            preview = response_preview[:100] + "..." if len(response_preview) > 100 else response_preview
            summary.append(f"Response Preview: {preview}")
    
    return "\n".join(summary)

def main():
    """Main function to run the demo."""
    logger.info("Starting Knowledge Algorithms (KA) Demo")
    
    # Create the master controller
    controller = create_master_controller()
    
    # Display available algorithms
    available_algorithms = controller.get_available_algorithms()
    logger.info(f"Available algorithms: {len(available_algorithms)}")
    for algo in available_algorithms:
        logger.info(f"  {algo['algorithm']}: {algo['description']}")
    
    # Define test queries for different domains
    test_queries = [
        {"query": "What are the key regulatory considerations for implementing AI in healthcare?", 
         "domain": "healthcare"},
        {"query": "How can financial institutions manage data privacy compliance across international jurisdictions?", 
         "domain": "finance"},
        {"query": "What frameworks exist for evaluating the environmental impact of technology infrastructure?", 
         "domain": "technology"}
    ]
    
    # Test individual algorithms
    logger.info("\n\n===== Testing Individual Algorithms =====")
    for test in test_queries[:1]:  # Use just the first query for individual testing
        query = test["query"]
        domain = test["domain"]
        
        # Test KA-1: Semantic Mapping
        ka1_result = test_single_algorithm(controller, 1, query, domain)
        logger.info(f"\nKA-1 Result Summary:\n{format_result(ka1_result)}")
        
        # Test KA-4: Honeycomb Expansion
        ka4_result = test_single_algorithm(controller, 4, query, domain)
        logger.info(f"\nKA-4 Result Summary:\n{format_result(ka4_result)}")
        
        # Test KA-20: Quad Persona Orchestration
        ka20_result = test_single_algorithm(controller, 20, query, domain)
        logger.info(f"\nKA-20 Result Summary:\n{format_result(ka20_result)}")
    
    # Test pipeline
    logger.info("\n\n===== Testing Algorithm Pipeline =====")
    for test in test_queries:
        query = test["query"]
        domain = test["domain"]
        
        pipeline_result = test_algorithm_pipeline(controller, query, domain)
        
        # Get the final integrated result
        final_result = pipeline_result.get("final_result", {})
        integrated_result = final_result.get("integrated_result", {})
        response = integrated_result.get("response", "No response generated")
        
        logger.info(f"\n----- Pipeline Result for domain '{domain}' -----")
        logger.info(f"Query: \"{query}\"")
        logger.info(f"Final Response:\n{response[:500]}..." if len(response) > 500 else response)
    
    logger.info("\nKnowledge Algorithms (KA) Demo completed")

if __name__ == "__main__":
    main()