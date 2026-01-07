"""
Universal Knowledge Graph (UKG) System - Quad Persona Demo Runner

This script runs the Quad Persona demo with pre-selected inputs.
"""

import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def run_demo_with_preset():
    """Run the Quad Persona demo with preset inputs."""
    try:
        # Import quad persona components
        from quad_persona.quad_engine import create_quad_persona_engine
        from simulation.simulation_engine import create_simulation_engine
        
        print("\n===== Universal Knowledge Graph - Quad Persona Simulation Demo =====\n")
        
        # Initialize engines
        print("Initializing Quad Persona Engine...")
        quad_engine = create_quad_persona_engine()
        
        print("Initializing Simulation Engine...")
        simulation_engine = create_simulation_engine()
        
        print("\nEngines initialized successfully!\n")
        
        # Pre-selected query
        query = "What are the key considerations for implementing a data governance program?"
        domain = "technology"
        
        # Create context with equal weights
        context = {
            "domain": domain,
            "persona_weights": {
                "knowledge": 0.25,
                "sector": 0.25,
                "regulatory": 0.25,
                "compliance": 0.25
            }
        }
        
        print(f"Running demo with query: '{query}'")
        print(f"Domain: {domain}")
        print(f"Using equal weights for all personas (25% each)")
        
        # Process with Quad Engine
        print("\nProcessing with Quad Persona Engine...")
        quad_result = quad_engine.process_query(query, context)
        
        # Process with Simulation Engine
        print("Processing with Simulation Engine (includes refinement and memory)...")
        sim_result = simulation_engine.process_query(query, context)
        
        print("\n===== RESULTS =====\n")
        print(f"Query: {query}")
        
        # Display results
        if isinstance(sim_result, str):
            # Handle case where sim_result is just a string
            print("\nIntegrated Response:")
            print(sim_result)
        else:
            # Handle case where sim_result is a dictionary
            try:
                # Display persona responses
                persona_results = sim_result.get("persona_results", {})
                
                print("\n==== Individual Persona Responses ====\n")
                
                for persona_type, result in persona_results.items():
                    if result:
                        print(f"=== {persona_type.capitalize()} Expert ===")
                        print(f"Confidence: {result.get('confidence', 0):.2f}")
                        print(f"Response: {result.get('response', 'No response')}\n")
                
                # Display final response
                print("\n==== Integrated Response ====\n")
                final_response = sim_result.get("response", "")
                print(final_response)
                
                # Display metrics
                print("\n==== Performance Metrics ====\n")
                print(f"Processing Time: {sim_result.get('processing_time_ms', 0):.2f}ms")
                print(f"Overall Confidence: {sim_result.get('confidence', 0):.2f}")
                
            except Exception as e:
                print(f"Error parsing results: {e}")
                print("\nRaw Result:")
                print(sim_result)
        
        print("\n===== Demo Complete =====\n")
        
    except Exception as e:
        logger.error(f"Error in Quad Persona Demo: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
        print("Please check the logs for more details.")

if __name__ == "__main__":
    run_demo_with_preset()