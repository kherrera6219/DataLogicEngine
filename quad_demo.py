"""
Universal Knowledge Graph (UKG) System - Quad Persona Demo

This standalone script demonstrates the Quad Persona Simulation Engine
by directly using the quad_persona and simulation components.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import quad persona components
from quad_persona.quad_engine import create_quad_persona_engine
from simulation.simulation_engine import create_simulation_engine

def run_quad_persona_demo():
    """Run the Quad Persona Simulation Engine demo."""
    print("\n===== Universal Knowledge Graph - Quad Persona Simulation Demo =====\n")
    
    # Initialize engines
    print("Initializing Quad Persona Engine...")
    quad_engine = create_quad_persona_engine()
    
    print("Initializing Simulation Engine...")
    simulation_engine = create_simulation_engine()
    
    print("\nEngines initialized successfully!\n")
    
    # Define sample queries for different domains
    sample_queries = [
        "What are the key considerations for implementing a data governance program?",
        "How do healthcare regulations impact medical device development?",
        "What compliance frameworks should a financial institution implement for cross-border transactions?"
    ]
    
    # Select a query to process
    print("Select a query to process:")
    for i, query in enumerate(sample_queries):
        print(f"{i+1}. {query}")
    print(f"{len(sample_queries)+1}. Enter your own query")
    
    choice = input("\nEnter your choice (1-4): ")
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(sample_queries):
            query = sample_queries[choice_num-1]
        else:
            query = input("\nEnter your query: ")
    except ValueError:
        query = input("\nEnter your query: ")
    
    # Select domain (optional)
    print("\nSelect a domain (optional):")
    print("1. General")
    print("2. Healthcare")
    print("3. Finance")
    print("4. Technology")
    
    domain_choice = input("\nEnter your choice (1-4, default is 1): ")
    
    domain_mapping = {
        "1": "",
        "2": "healthcare",
        "3": "finance",
        "4": "technology"
    }
    
    domain = domain_mapping.get(domain_choice, "")
    
    # Prepare context
    context = {}
    if domain:
        context["domain"] = domain
    
    # Set weights for personas
    print("\nSet weights for each persona (0-100, default is 25 each):")
    try:
        knowledge_weight = int(input("Knowledge Expert weight: ") or "25")
        sector_weight = int(input("Sector Expert weight: ") or "25")
        regulatory_weight = int(input("Regulatory Expert weight: ") or "25")
        compliance_weight = int(input("Compliance Expert weight: ") or "25")
    except ValueError:
        knowledge_weight = sector_weight = regulatory_weight = compliance_weight = 25
    
    # Normalize weights
    total = knowledge_weight + sector_weight + regulatory_weight + compliance_weight
    if total > 0:
        weights = {
            "knowledge": knowledge_weight / total,
            "sector": sector_weight / total,
            "regulatory": regulatory_weight / total,
            "compliance": compliance_weight / total
        }
        context["persona_weights"] = weights
    
    print("\nProcessing query with Quad Persona Engine...")
    start_time = datetime.now()
    
    # Process with direct Quad Engine for comparison
    print("\nDirect Quad Engine processing...")
    quad_result = quad_engine.process_query(query, context)
    
    # Process with Simulation Engine (includes refinement and memory)
    print("Simulation Engine processing...")
    sim_result = simulation_engine.process_query(query, context)
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds() * 1000
    
    # Display results
    print("\n===== Quad Persona Simulation Results =====\n")
    print(f"Query: {query}")
    print(f"Domain: {domain or 'General'}")
    print(f"Processing time: {processing_time:.2f}ms")
    
    print("\n===== Individual Persona Responses =====\n")
    
    # For the simulation engine, the persona results are inside the result object
    persona_results = {}
    try:
        persona_results = sim_result.get("persona_results", {})
    except (AttributeError, KeyError):
        # If simulation engine doesn't return expected format, use simple structure
        persona_results = {
            "knowledge": {"response": "Knowledge Expert analysis not available.", "confidence": 0},
            "sector": {"response": "Sector Expert analysis not available.", "confidence": 0},
            "regulatory": {"response": "Regulatory Expert analysis not available.", "confidence": 0},
            "compliance": {"response": "Compliance Expert analysis not available.", "confidence": 0}
        }
    
    # Display each persona's response
    for persona_type, result in persona_results.items():
        if isinstance(result, dict):
            print(f"== {persona_type.capitalize()} Expert ==")
            print(f"Confidence: {result.get('confidence', 0):.2f}")
            print(f"Response: {result.get('response', 'No response')}\n")
    
    print("\n===== Integrated Response =====\n")
    
    try:
        final_response = sim_result.get("response", "Integrated response not available.")
        print(final_response)
    except (AttributeError, KeyError):
        print("Integrated response not available.")
    
    print("\n===== Demo Complete =====\n")

if __name__ == "__main__":
    try:
        run_quad_persona_demo()
    except Exception as e:
        logger.error(f"Error in Quad Persona Demo: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
        print("Please check the logs for more details.")