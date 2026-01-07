#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Layer 1 Database Demo

This script demonstrates the Layer 1 database capabilities of the UKG system.
"""

import os
import sys
import logging
import json
import time
from typing import Dict, Any, List
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.layer1_database import Layer1Database
from simulation.data_generator import generate_sample_data

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(f" {title} ".center(80))
    print("="*80)

def print_section(title):
    """Print a section header."""
    print("\n" + "-"*80)
    print(f" {title} ".center(80))
    print("-"*80)

def initialize_database():
    """Initialize and populate the Layer 1 database."""
    print_section("Initializing Layer 1 Database")

    db = Layer1Database()
    print("Layer 1 database initialized")

    # Generate sample data
    print("Generating sample data for all 13 axes...")
    nodes_by_axis, relationships = generate_sample_data(db, num_nodes=50, num_relationships=75)

    # Export database to JSON
    db.export_to_json()

    return db

def demonstrate_querying(db):
    """Demonstrate querying capabilities of the database."""
    print_section("Database Querying Capabilities")

    # Example 1: Text search
    query = "artificial intelligence"
    print(f"Searching for '{query}':")
    results = db.search(query)
    for i, result in enumerate(results[:5], 1):  # Show first 5 results
        print(f"  {i}. [{result['axis_name']}] {result['label']}")
        print(f"     Description: {result['description']}")

    # Example 2: Get nodes by axis
    print("\nAxis 2 (Sectors):")
    sector_nodes = db.get_nodes_by_axis(2)
    for i, node in enumerate(sector_nodes[:5], 1):  # Show first 5 results
        print(f"  {i}. {node['label']} (Level {node['level']})")
        print(f"     Description: {node['description']}")

    # Example 3: Get nodes by axis and level
    print("\nAxis 1 (Pillar Levels), Level 1:")
    pillar_nodes = db.get_nodes_by_level(1, 1)
    for i, node in enumerate(pillar_nodes[:5], 1):  # Show first 5 results
        print(f"  {i}. {node['label']}")
        print(f"     Description: {node['description']}")

def demonstrate_traversal(db):
    """Demonstrate traversal capabilities of the database."""
    print_section("Database Traversal Capabilities")

    # Find a node with relationships to showcase
    all_nodes = []
    for axis in range(1, 14):
        nodes = db.get_nodes_by_axis(axis)
        if nodes:
            all_nodes.extend(nodes)

    target_node = None
    for node in all_nodes:
        node_id = node["node_id"]
        outgoing = db.get_outgoing_relationships(node_id)
        incoming = db.get_incoming_relationships(node_id)

        if outgoing or incoming:
            target_node = node
            break

    if not target_node:
        print("No suitable node found for traversal demo")
        return

    # Show node information
    print(f"Selected node: {target_node['label']} (Axis {target_node['axis']}, Level {target_node['level']})")
    print(f"Description: {target_node['description']}")

    # Show outgoing relationships
    outgoing = db.get_outgoing_relationships(target_node["node_id"])
    print(f"\nOutgoing relationships ({len(outgoing)}):")
    for i, rel in enumerate(outgoing[:3], 1):  # Show first 3 results
        target = db.get_node(rel["target_id"])
        if target:
            print(f"  {i}. {target_node['label']} --[{rel['rel_type']}]--> {target['label']}")
            print(f"     Weight: {rel['weight']}")

    # Show incoming relationships
    incoming = db.get_incoming_relationships(target_node["node_id"])
    print(f"\nIncoming relationships ({len(incoming)}):")
    for i, rel in enumerate(incoming[:3], 1):  # Show first 3 results
        source = db.get_node(rel["source_id"])
        if source:
            print(f"  {i}. {source['label']} --[{rel['rel_type']}]--> {target_node['label']}")
            print(f"     Weight: {rel['weight']}")

    # Show neighbors
    neighbors = db.get_neighbors(target_node["node_id"])
    print(f"\nNeighbors ({len(neighbors)}):")
    for i, node in enumerate(neighbors[:5], 1):  # Show first 5 results
        print(f"  {i}. {node['label']} (Axis {node['axis']}, Level {node['level']})")

def main():
    """Run the Layer 1 database demo."""
    print_header("UKG LAYER 1 DATABASE DEMO")
    print("This demo showcases the Layer 1 database capabilities of the UKG system.")

    start_time = time.time()

    try:
        # Initialize and populate the database
        db = initialize_database()

        # Demonstrate querying capabilities
        demonstrate_querying(db)

        # Demonstrate traversal capabilities
        demonstrate_traversal(db)

        elapsed_time = time.time() - start_time
        print_header("DEMO COMPLETE")
        print(f"Total time: {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error running demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())