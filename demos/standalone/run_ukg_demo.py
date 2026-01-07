#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Integrated Simulation Demo

This script demonstrates the complete Nested Layered In-Memory Simulation Management System
with the integrated Quad Persona Engine and 13-axis coordination system.
"""

import os
import sys
import logging
import time
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ukg_demo.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_folders():
    """Create necessary folders for the UKG system."""
    folders = ['data', 'logs']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created folder: {folder}")

def run_demo():
    """Run the main UKG simulation demo."""
    try:
        # Import the orchestrator to bring together all three layers
        logger.info("Importing UKG simulation orchestrator...")
        from simulation.orchestrator import create_simulation_orchestrator
        
        # Create the full orchestrator
        logger.info("Creating UKG simulation orchestrator...")
        orchestrator = create_simulation_orchestrator()
        
        # Display demo options
        print("\n===== Universal Knowledge Graph (UKG) Simulation Demo =====")
        print("This demo showcases the 3-layer Nested Simulation Management System:")
        print("  Layer 1: Simulation Entry Layer - Gateway for queries")
        print("  Layer 2: Nested Simulated Knowledge Database - UKG with Quad Persona Engine")
        print("  Layer 3: Simulated Research Agent Layer - AI agent delegation")
        print("\nAvailable demo options:")
        print("1. Data Governance in Healthcare (Layer 2 only)")
        print("2. Cross-border Finance Regulation (Layer 2 + Layer 3)")
        print("3. Custom query (Your own question)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            # Demo 1: Data Governance in Healthcare (Layer 2)
            query = "What are the key considerations for implementing a data governance program in a healthcare organization?"
            context = {
                "domain": "healthcare",
                "complexity": "medium",
                "require_verification": False
            }
            print(f"\nProcessing query: {query}")
            print("Context:", json.dumps(context, indent=2))
            
            # Process the query
            start_time = time.time()
            result = orchestrator.process_query(query, context)
            end_time = time.time()
            
            # Display results
            display_result(result, end_time - start_time)
            
        elif choice == "2":
            # Demo 2: Cross-border Finance Regulation (Layer 2 + Layer 3)
            query = (
                "Compare the regulatory requirements for cross-border financial transactions "
                "between the EU, US, and Asia, and provide a framework for ensuring compliance "
                "across these jurisdictions."
            )
            context = {
                "domain": "finance",
                "complexity": "high",
                "require_verification": True
            }
            print(f"\nProcessing query: {query}")
            print("Context:", json.dumps(context, indent=2))
            
            # Process the query
            start_time = time.time()
            result = orchestrator.process_query(query, context)
            end_time = time.time()
            
            # Display results
            display_result(result, end_time - start_time)
            
        elif choice == "3":
            # Demo 3: Custom query
            query = input("\nEnter your query: ")
            domain = input("Enter domain (e.g., technology, healthcare, finance): ")
            complexity = input("Enter complexity (low, medium, high): ")
            verify = input("Require verification? (y/n): ").lower() == 'y'
            
            context = {
                "domain": domain.lower() if domain else "general",
                "complexity": complexity.lower() if complexity else "medium",
                "require_verification": verify
            }
            
            print(f"\nProcessing query: {query}")
            print("Context:", json.dumps(context, indent=2))
            
            # Process the query
            start_time = time.time()
            result = orchestrator.process_query(query, context)
            end_time = time.time()
            
            # Display results
            display_result(result, end_time - start_time)
            
        elif choice == "4":
            print("\nExiting demo.")
            return
        else:
            print("\nInvalid choice. Please run the demo again.")
            return
        
        # Ask if the user wants to continue
        continue_demo = input("\nWould you like to run another demo? (y/n): ")
        if continue_demo.lower() == 'y':
            run_demo()
    
    except Exception as e:
        logger.error(f"Error running demo: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
        print("Please check the logs for more details.")

def display_result(result: Dict[str, Any], processing_time: float):
    """
    Display the result of a query.
    
    Args:
        result: The query result
        processing_time: The time taken to process the query
    """
    print("\n" + "="*80)
    print(f"QUERY RESULTS (ID: {result.get('query_id', 'Unknown')})")
    print("="*80)
    
    # Display processing information
    print(f"\nProcessing Time: {processing_time*1000:.2f}ms")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    
    # Display processing level and agents involved
    processing_level = result.get("processing_level", "layer2")
    if processing_level == "layer3":
        print("\nProcessing Level: Layer 3 (Research Agent Layer)")
        if "agents_involved" in result:
            print(f"Agents Involved: {', '.join(result.get('agents_involved', []))}")
    else:
        print("\nProcessing Level: Layer 2 (Knowledge Database)")
    
    # Display the response
    print("\nRESPONSE:")
    print("-"*80)
    response = result.get("response", "No response generated")
    print(response)
    print("-"*80)
    
    # Save result to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/ukg_result_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nDetailed results saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        print(f"\nError saving detailed results: {str(e)}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UKG Simulation Demo")
    parser.add_argument("--setup", action="store_true", help="Create necessary folders")
    args = parser.parse_args()
    
    if args.setup:
        setup_folders()
    
    # Run the demo
    run_demo()