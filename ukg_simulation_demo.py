"""
Universal Knowledge Graph (UKG) System - Simulation Demo

This script demonstrates the Nested Layered In-Memory Simulation Management System
for the UKG, showing the flow of queries through the three-layer architecture.
"""

import logging
import time
from typing import Dict, Any

from simulation.orchestrator import create_simulation_orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_demo_query(orchestrator, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run a demo query through the orchestrator.
    
    Args:
        orchestrator: The simulation orchestrator
        query: The query to process
        context: Optional context for the query
        
    Returns:
        The query result
    """
    print(f"\n{'=' * 80}")
    print(f"QUERY: {query}")
    print(f"{'=' * 80}")
    
    start_time = time.time()
    result = orchestrator.process_query(query, context)
    end_time = time.time()
    
    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    print(f"\nPROCESSING TIME: {processing_time:.2f}ms")
    print(f"CONFIDENCE: {result.get('confidence', 0):.2f}")
    
    # Display the agents involved if any
    if "agents_involved" in result and result["agents_involved"]:
        print(f"AGENTS INVOLVED: {', '.join(result['agents_involved'])}")
    
    print("\nRESPONSE:")
    print(f"{'-' * 80}")
    print(result.get("response", "No response generated"))
    print(f"{'-' * 80}")
    
    return result

def main():
    """Run the UKG simulation demo."""
    print("\nInitializing Universal Knowledge Graph Simulation System...\n")
    
    # Create the orchestrator that connects all three layers
    orchestrator = create_simulation_orchestrator()
    
    print("\nUKG Simulation System initialized. Running demo queries...\n")
    
    # Run a query that will be processed by Layer 2 (Quad Persona Engine)
    data_governance_query = "What are the key considerations for implementing a data governance program in a healthcare organization?"
    data_governance_context = {"domain": "healthcare"}
    
    run_demo_query(orchestrator, data_governance_query, data_governance_context)
    
    # Run a more complex query that will likely escalate to Layer 3 (Research Agents)
    complex_query = (
        "Compare the regulatory requirements for cross-border financial transactions "
        "between the EU, US, and Asia, and provide a framework for ensuring compliance "
        "across these jurisdictions."
    )
    complex_context = {
        "domain": "finance",
        "complexity": "high",
        "require_verification": True
    }
    
    run_demo_query(orchestrator, complex_query, complex_context)
    
    print("\nUKG Simulation Demo complete.")

if __name__ == "__main__":
    main()