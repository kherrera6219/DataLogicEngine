#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Master Controller Demo

This script demonstrates the UKG Master Controller orchestrating multiple
Knowledge Algorithms to process complex queries.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UKG-Demo")

# Import Master Controller
from knowledge_algorithms.ka_master_controller import get_controller

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(f" {title} ".center(80))
    print("="*80)

def print_result(result, indent=0):
    """Print a result dictionary in a readable format."""
    if isinstance(result, dict):
        for key, value in result.items():
            if key in ["execution_time", "timestamp"]:
                continue
                
            if isinstance(value, dict):
                print(" " * indent + f"{key}:")
                print_result(value, indent + 2)
            elif isinstance(value, list):
                if not value:
                    print(" " * indent + f"{key}: []")
                else:
                    print(" " * indent + f"{key}:")
                    if isinstance(value[0], (dict, list)):
                        for item in value:
                            print_result(item, indent + 2)
                    else:
                        print(" " * indent + "  " + str(value))
            else:
                print(" " * indent + f"{key}: {value}")
    else:
        print(" " * indent + str(result))

def run_analysis_pipeline(query, domain="artificial_intelligence"):
    """Run a complete analysis pipeline on a query."""
    print_header("RUNNING COMPLETE UKG ANALYSIS PIPELINE")
    print(f"Query: '{query}'")
    print(f"Domain: {domain}")
    
    # Get controller
    controller = get_controller()
    
    # Step 1: Create tokens for neural activation
    tokens = query.split()
    
    # Step 2: Create execution plan
    print("\n>> Creating execution plan...")
    sequence = [
        # Initial neural activation mapping
        {
            "algorithm": "KA-40",  # Neural Activation Mapper
            "parameters": {
                "input_tokens": tokens
            }
        },
        # Apply trust propagation to assess reliability
        {
            "algorithm": "KA-39",  # Quantum Trust Propagation
            "parameters": {
                "initial_trust": 0.95,
                "propagation_steps": 3
            }
        },
        # Generate confidence-optimized reasoning path
        {
            "algorithm": "KA-47",  # Recursive Confidence Optimizer
            "parameters": {
                "initial_confidence": 0.7,
                "passes": 4
            }
        },
        # Check for emergent behaviors that need containment
        {
            "algorithm": "KA-45",  # Emergence Containment Manager
            "parameters": {
                "emergence_flags": ["pattern_formation", "complexity_increase"]
            }
        },
        # Create learning curriculum for domain
        {
            "algorithm": "KA-48",  # Simulated Curriculum Builder
            "parameters": {
                "domain": domain,
                "lesson_count": 5
            }
        },
        # Generate explanation trace for transparency
        {
            "algorithm": "KA-49",  # Explainability Trace Constructor
            "parameters": {
                "decision_steps": [
                    f"Analyze query: '{query}'",
                    f"Identify domain: {domain}",
                    "Map neural activations for key concepts",
                    "Propagate trust through knowledge network",
                    "Optimize confidence through multiple passes",
                    "Check for emergence patterns requiring containment",
                    "Generate domain-specific learning curriculum",
                    "Construct explanatory trace for transparency"
                ],
                "format": "narrative"
            }
        }
    ]
    
    # Step 3: Execute sequence
    print(">> Executing algorithm sequence...")
    start_time = time.time()
    results = controller.execute_sequence(sequence, return_all_results=True)
    total_time = time.time() - start_time
    
    # Step 4: Summarize results
    print(f"\n>> Execution completed in {total_time:.2f} seconds")
    
    # Extract key information from results
    neural_result = results[0] if len(results) > 0 else None
    trust_result = results[1] if len(results) > 1 else None
    confidence_result = results[2] if len(results) > 2 else None
    emergence_result = results[3] if len(results) > 3 else None
    curriculum_result = results[4] if len(results) > 4 else None
    explanation_result = results[5] if len(results) > 5 else None
    
    # Print summary
    print_header("ANALYSIS RESULTS")
    
    if neural_result:
        print(f"\nNeural Activation: {len(neural_result.get('activations', []))} neurons activated")
    
    if trust_result:
        print(f"\nTrust Propagation: {trust_result.get('propagated_trust', 0):.4f} final trust score")
    
    if confidence_result:
        confidence_progress = confidence_result.get('confidence_progression', [])
        print(f"\nConfidence Optimization: Initial {confidence_progress[0] if confidence_progress else 0:.3f} -> Final {confidence_progress[-1] if confidence_progress else 0:.3f}")
    
    if emergence_result:
        print(f"\nEmergence Containment: {'Required' if emergence_result.get('containment', False) else 'Not Required'}")
    
    if curriculum_result:
        print("\nLearning Curriculum:")
        for i, lesson in enumerate(curriculum_result.get('curriculum', [])):
            print(f"  {i+1}. {lesson}")
    
    if explanation_result:
        print(f"\nExplanation Trace:\n  {explanation_result.get('explanation_trace', 'No explanation available')}")
    
    print("\n" + "="*80)
    
    return {
        "query": query,
        "domain": domain,
        "results": {
            "neural_activation": neural_result.get('activations', []) if neural_result else [],
            "trust_score": trust_result.get('propagated_trust', 0) if trust_result else 0,
            "final_confidence": confidence_progress[-1] if confidence_result and confidence_progress else 0,
            "containment_required": emergence_result.get('containment', False) if emergence_result else False,
            "curriculum": curriculum_result.get('curriculum', []) if curriculum_result else [],
            "explanation_trace": explanation_result.get('explanation_trace', '') if explanation_result else ''
        },
        "execution_time": total_time
    }

def run_interactive_demo():
    """Run the master controller demo in interactive mode."""
    print_header("UKG MASTER CONTROLLER DEMO")
    print("This demo showcases the Universal Knowledge Graph Master Controller orchestrating")
    print("multiple Knowledge Algorithms to process and analyze complex queries.")
    
    # Get controller
    controller = get_controller()
    
    # Show available algorithms
    algos = controller.get_available_algorithms()
    print(f"\nAvailable Knowledge Algorithms: {len(algos)}")
    
    for algo_group, algo_ids in [
        ("Core Knowledge (1-10)", [f"KA-{i}" for i in range(1, 11)]),
        ("Advanced Reasoning (11-20)", [f"KA-{i}" for i in range(11, 21)]),
        ("Knowledge Enhancement (21-30)", [f"KA-{i}" for i in range(21, 31)]),
        ("AGI & Emergence (31-38)", [f"KA-{i}" for i in range(31, 39)]),
        ("Quantum & Neural (39-50)", [f"KA-{i}" for i in range(39, 51)])
    ]:
        available = [ka_id for ka_id in algo_ids if ka_id in algos]
        print(f"  {algo_group}: {len(available)}/{len(algo_ids)} available")
    
    # Sample queries
    sample_queries = [
        "What are the best practices for ethical AI deployment?",
        "How do recent regulations affect financial compliance?",
        "What learning path should I follow for quantum computing?",
        "How can we balance innovation and safety in aerospace?"
    ]
    
    print("\nSample Queries:")
    for i, query in enumerate(sample_queries):
        print(f"  {i+1}. {query}")
    
    # Get user input
    try:
        choice = input("\nSelect a query (1-4) or enter your own: ")
        try:
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(sample_queries):
                query = sample_queries[choice_index]
            else:
                query = choice
        except:
            query = choice
        
        domain = input("Enter knowledge domain (e.g., artificial_intelligence, aerospace, finance): ")
        if not domain:
            domain = "artificial_intelligence"
        
        # Run analysis pipeline
        analysis = run_analysis_pipeline(query, domain)
        
        # Option to view execution history
        view_history = input("\nView execution history? (y/n): ").lower().startswith('y')
        if view_history:
            history = controller.get_execution_history()
            print_header("EXECUTION HISTORY")
            for i, entry in enumerate(history):
                print(f"\n[{i+1}] {entry['ka_id']} - {'SUCCESS' if entry['success'] else 'FAILURE'}")
                print(f"    Time: {entry['duration']:.3f}s")
                print(f"    Input keys: {', '.join(entry['input_data_keys'])}")
                if 'result_keys' in entry:
                    print(f"    Result keys: {', '.join(entry['result_keys'])}")
                if 'error' in entry:
                    print(f"    Error: {entry['error']}")
            
            print("\n" + "="*80)
        
    except KeyboardInterrupt:
        print("\nDemo cancelled.")

def run_basic_demo():
    """Run a basic demo with a predefined query."""
    query = "What best practices should we follow for implementing ethical AI systems?"
    domain = "artificial_intelligence"
    run_analysis_pipeline(query, domain)

def main():
    """Main entry point for the script."""
    # Check if interactive mode is requested
    interactive = False
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['-i', '--interactive']:
        interactive = True
    
    try:
        if interactive:
            run_interactive_demo()
        else:
            run_basic_demo()
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()