"""
UKG Simulation Demo

This script demonstrates the UKG system's capabilities by running a sample query
through the multi-layer simulation system, showing how the various components work together.
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import UKG components
from core.system.united_system_manager import UnitedSystemManager
from simulation.gatekeeper_agent import GatekeeperAgent
from simulation.refinement_loop_handler import RefinementLoopHandler
from simulation.pov_engine import POVEngine

def format_json(data: Dict) -> str:
    """Format JSON data with indentation for better readability."""
    return json.dumps(data, indent=2, default=str)

def run_simulation_demo():
    """Run a demonstration of the UKG simulation system."""
    print("\n" + "="*80)
    print("UKG Simulation Demo".center(80))
    print("="*80 + "\n")
    
    # Step 1: Initialize the UKG system
    print("\n--- Step 1: Initializing UKG System ---\n")
    
    # Create a United System Manager manually
    united_system_manager = UnitedSystemManager()
    
    # Create key components
    from core.memory.structured_memory_manager import StructuredMemoryManager
    from core.graph.graph_manager import GraphManager
    from core.engine.ka_engine import KAEngine
    from core.simulation.location_context_engine import LocationContextEngine
    from core.simulation.simulation_engine import SimulationEngine
    from core.self_evolving.sekre_engine import SekreEngine
    
    # Initialize and register components
    memory_manager = StructuredMemoryManager()
    united_system_manager.register_component('memory_manager', memory_manager)
    
    graph_manager = GraphManager()
    united_system_manager.register_component('graph_manager', graph_manager)
    
    ka_engine = KAEngine()
    united_system_manager.register_component('ka_engine', ka_engine)
    
    location_engine = LocationContextEngine()
    united_system_manager.register_component('location_context_engine', location_engine)
    
    simulation_engine = SimulationEngine()
    united_system_manager.register_component('simulation_engine', simulation_engine)
    
    sekre_engine = SekreEngine(
        graph_manager=graph_manager,
        memory_manager=memory_manager,
        united_system_manager=united_system_manager
    )
    united_system_manager.register_component('sekre_engine', sekre_engine)
    
    print(f"UKG System initialized with components:")
    for component_name in united_system_manager.components.keys():
        print(f"  - {component_name}")
    
    # Step 2: Set up the simulation components
    print("\n--- Step 2: Setting up Simulation Components ---\n")
    gatekeeper = GatekeeperAgent()
    refinement_handler = RefinementLoopHandler(
        gatekeeper=gatekeeper,
        system_manager=united_system_manager
    )
    pov_engine = POVEngine(system_manager=united_system_manager)
    
    print("Simulation components initialized:")
    print("  - Gatekeeper Agent")
    print("  - Refinement Loop Handler")
    print("  - POV Engine")
    
    # Step 3: Define a sample query
    print("\n--- Step 3: Sample Query Definition ---\n")
    query = "What are the regulatory implications of using AI for medical diagnostics in the healthcare sector?"
    print(f"Query: {query}")
    
    # Step 4: Start the refinement process
    print("\n--- Step 4: Starting Refinement Process ---\n")
    simulation_init = refinement_handler.start_refinement(query)
    simulation_id = simulation_init['simulation_id']
    print(f"Simulation started with ID: {simulation_id}")
    print(f"Status: {simulation_init['status']}")
    
    # Step 5: Run initial simulation pass and get results
    print("\n--- Step 5: Running Initial Simulation Pass ---\n")
    # Get the simulation from the refinement handler
    simulation = refinement_handler.get_simulation(simulation_id)
    if not simulation:
        print("Error: Simulation not found")
        return
    
    print(f"Initial confidence: {simulation['confidence']}")
    print(f"Initial entropy: {simulation['entropy']}")
    
    # Step 6: Evaluate using the Gatekeeper Agent
    print("\n--- Step 6: Gatekeeper Evaluation ---\n")
    gatekeeper_input = {
        'simulation_id': simulation_id,
        'simulation_pass': 1,
        'confidence_score': simulation['confidence']['overall'],
        'entropy_score': simulation['entropy'],
        'roles_triggered': ['multirole', 'knowledge_gap'],
        'regulatory_flags': ['compliance', 'medical_regulations']
    }
    
    gatekeeper_decision = gatekeeper.evaluate(gatekeeper_input)
    print("Gatekeeper decision:")
    print(f"  - Active layers: {gatekeeper.get_active_layers()}")
    print(f"  - Halt due to entropy: {gatekeeper.should_halt()}")
    
    # Step 7: If POV Engine is activated, expand the context
    print("\n--- Step 7: POV Engine Expansion ---\n")
    active_layers = gatekeeper.get_active_layers()
    
    if 4 in active_layers:  # Layer 4 is the POV Engine
        print("POV Engine activated. Expanding context...")
        
        # Create initial context for POV expansion
        initial_context = {
            'simulation_id': simulation_id,
            'query': query,
            'initial_data': [
                {'node_id': 'node1', 'content': 'AI in healthcare', 'confidence': 0.8},
                {'node_id': 'node2', 'content': 'Medical diagnostics', 'confidence': 0.85},
                {'node_id': 'node3', 'content': 'Regulatory frameworks', 'confidence': 0.75}
            ]
        }
        
        expanded_context = pov_engine.expand_context(query, initial_context)
        
        print(f"Context expanded with:")
        print(f"  - Expanded data nodes: {len(expanded_context.get('expanded_data', []))}")
        print(f"  - Simulated personas: {len(expanded_context.get('simulated_personas', []))}")
        print(f"  - POV confidence: {expanded_context.get('pov_confidence', 0.0):.4f}")
        
        # Update simulation with expanded context
        simulation['pov_context'] = expanded_context
        simulation['confidence']['overall'] = max(
            simulation['confidence']['overall'],
            expanded_context.get('pov_confidence', 0.0)
        )
    else:
        print("POV Engine not activated by Gatekeeper.")
    
    # Step 8: Run the full refinement process
    print("\n--- Step 8: Running Full Refinement Process ---\n")
    print("Starting full refinement process...")
    
    # Start timing
    start_time = time.time()
    
    # Run refinement
    result = refinement_handler.run_refinement(simulation_id)
    
    # End timing
    end_time = time.time()
    
    print(f"Refinement completed in {end_time - start_time:.2f} seconds")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Final confidence: {result.get('confidence', {}).get('overall', 0.0):.4f}")
    print(f"Total passes: {result.get('metrics', {}).get('total_passes', 0)}")
    
    # Step 9: Display final simulation results
    print("\n--- Step 9: Final Simulation Results ---\n")
    
    passes = result.get('passes', [])
    if passes:
        last_pass = passes[-1]
        final_synthesis = last_pass.get('refinement_workflow', {}).get('step_results', {}).get('final_synthesis', {})
        
        if final_synthesis:
            print("Final integrated response from simulation:\n")
            print(final_synthesis.get('integrated_response', 'No response available.'))
            print("\nConfidence score:", final_synthesis.get('final_confidence', 0.0))
            print("Entropy score:", final_synthesis.get('final_entropy', 0.0))
        else:
            print("No final synthesis available.")
    else:
        print("No simulation passes completed.")
    
    # Step 10: Summary
    print("\n--- Step 10: Simulation Summary ---\n")
    print(f"Simulation ID: {simulation_id}")
    print(f"Query: {query}")
    
    if passes:
        print(f"Number of passes: {len(passes)}")
        print(f"Confidence progression:")
        
        for i, p in enumerate(passes):
            print(f"  Pass {i+1}: {p.get('confidence', {}).get('overall', 0.0):.4f}")
        
        print("\nActivated layers:")
        for i, p in enumerate(passes):
            active = p.get('active_layers', [])
            print(f"  Pass {i+1}: {active}")
    
    # Final remarks
    print("\n" + "="*80)
    print("UKG Simulation Demo Complete".center(80))
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        run_simulation_demo()
    except Exception as e:
        logging.error(f"Error running simulation demo: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")