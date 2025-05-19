#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Non-interactive Standalone Demo

This script runs the UKG simulation as a non-interactive standalone program
demonstrating both Layer 2 and Layer 3 of the 3-layer architecture.
"""

import os
import sys
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any

# Import the standalone simulator
from run_ukg_standalone import StandaloneSimulator, display_result

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ukg_standalone.log')
    ]
)

logger = logging.getLogger(__name__)

def run_noninteractive_demo():
    """Run a non-interactive demo of the UKG system."""
    print("\n===== Universal Knowledge Graph (UKG) Standalone Demo =====")
    print("This demo simulates the 3-layer Nested Simulation Management System:")
    print("  Layer 1: Simulation Entry Layer - Gateway for queries")
    print("  Layer 2: Nested Simulated Knowledge Database - UKG with Quad Persona Engine")
    print("  Layer 3: Simulated Research Agent Layer - AI agent delegation")
    
    # Create the standalone simulator
    simulator = StandaloneSimulator()
    
    print("\n\n=== DEMO 1: Layer 2 Processing - Data Governance in Healthcare ===\n")
    
    # Demo 1: Data Governance in Healthcare (Layer 2 only)
    query = "What are the key considerations for implementing a data governance program in a healthcare organization?"
    context = {
        "domain": "healthcare",
        "complexity": "medium",
        "require_verification": False
    }
    print(f"QUERY: {query}")
    print(f"CONTEXT: {json.dumps(context, indent=2)}")
    
    # Process the query
    start_time = time.time()
    result = simulator.process_query(query, context)
    end_time = time.time()
    
    # Display results
    display_result(result, end_time - start_time)
    
    print("\n\n=== DEMO 2: Layer 3 Processing - Cross-border Finance Regulation ===\n")
    
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
    print(f"QUERY: {query}")
    print(f"CONTEXT: {json.dumps(context, indent=2)}")
    
    # Process the query
    start_time = time.time()
    result = simulator.process_query(query, context)
    end_time = time.time()
    
    # Display results
    display_result(result, end_time - start_time)
    
    print("\nUKG Simulation Demo complete.")

if __name__ == "__main__":
    # Create necessary folders
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the demo
    run_noninteractive_demo()