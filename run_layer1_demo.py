
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
from simulation.data_generator import (
    generate_all_axis_data,
    generate_relationships
)

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
    
    # Generate and add data for all axes
    print("Generating sample data for all 13 axes...")
    axis_data = generate_all_axis_data()
    
    # Add nodes to database and track by axis
    nodes_by_axis = {i: [] for i in range(1, 14)}
    
    for axis_num, nodes in axis_data.items():
        print(f"Adding data for Axis {axis_num}: {db.axes[axis_num]['name']}...")
        
        for node_data in nodes:
            node_id = db.add_node(
                axis=axis_num,
                label=node_data["label"],
                level=node_data.get("level", 1),
                description=node_data.get("description", ""),
                attributes=node_data.get("attributes", {})
            )
            
            # Add to tracking with node_id
            node = db.get_node(node_id)
            if node:
                nodes_by_axis[axis_num].append(node)
    
    # Generate and add relationships
    print("Generating relationships between nodes...")
    relationships = generate_relationships(nodes_by_axis)
    
    for rel_data in relationships:
        db.add_relationship(
            source_id=rel_data["source_id"],
            target_id=rel_data["target_id"],
            rel_type=rel_data["rel_type"],
            weight=rel_data.get("weight", 1.0),
            attributes=rel_data.get("attributes", {})
        )
    
    # Print stats
    stats = db.get_stats()
    print(f"\nDatabase populated with {stats['total_nodes']} nodes and {stats['total_relationships']} relationships")
    print("\nNodes per axis:")
    for axis_num, count in sorted(stats['nodes_per_axis'].items()):
        if count > 0:
            print(f"  Axis {axis_num} ({db.axes[axis_num]['name']}): {count} nodes")
    
    print("\nRelationship types:")
    for rel_type, count in sorted(stats['relationship_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count} relationships")
    
    # Save database to file
    os.makedirs("data", exist_ok=True)
    db.export_data("data/layer1_database.json")
    print("\nDatabase exported to data/layer1_database.json")
    
    return db

def demonstrate_querying(db):
    """Demonstrate database querying capabilities."""
    print_section("Database Querying Capabilities")
    
    # Search for AI-related nodes
    print("Searching for 'artificial intelligence':")
    ai_nodes = db.search_nodes("artificial intelligence")
    
    for i, node in enumerate(ai_nodes, 1):
        axis_info = db.axes[node["axis"]]
        print(f"  {i}. [{axis_info['name']}] {node['label']}")
        print(f"     {node['description']}")
    
    # Get nodes for a specific axis
    print("\nGetting all nodes for Axis 6 (Regulatory Frameworks):")
    reg_nodes = db.get_nodes_by_axis(6)
    
    for i, node in enumerate(reg_nodes, 1):
        print(f"  {i}. {node['label']}: {node['description']}")
    
    # Get relationships for a specific node
    if reg_nodes:
        node = reg_nodes[0]
        print(f"\nGetting relationships for {node['label']}:")
        
        rels = db.get_node_relationships(node["node_id"])
        
        for i, rel in enumerate(rels, 1):
            source = db.get_node(rel["source_id"])
            target = db.get_node(rel["target_id"])
            
            if source and target:
                direction = "→" if source["node_id"] == node["node_id"] else "←"
                other_node = target if direction == "→" else source
                
                axis_info = db.axes[other_node["axis"]]
                print(f"  {i}. {direction} [{axis_info['name']}] {other_node['label']} "
                     f"({rel['rel_type']}, weight: {rel['weight']})")

def demonstrate_traversal(db):
    """Demonstrate traversal capabilities."""
    print_section("Graph Traversal")
    
    # Find a starting node from Axis 2 (Sectors)
    sectors = db.get_nodes_by_axis(2)
    if not sectors:
        print("No sector nodes found for traversal demo")
        return
    
    start_node = sectors[0]
    print(f"Starting traversal from {start_node['label']} (Axis 2: Sectors)")
    
    # Get outgoing relationships
    outgoing = db.get_node_relationships(start_node["node_id"], direction="outgoing")
    
    if outgoing:
        print(f"\nFound {len(outgoing)} outgoing relationships:")
        
        for i, rel in enumerate(outgoing, 1):
            target = db.get_node(rel["target_id"])
            
            if target:
                axis_info = db.axes[target["axis"]]
                print(f"  {i}. → [{axis_info['name']}] {target['label']} "
                     f"({rel['rel_type']}, weight: {rel['weight']})")
                
                # For the first relationship, demonstrate second-level traversal
                if i == 1:
                    second_level = db.get_node_relationships(target["node_id"], direction="outgoing")
                    
                    if second_level:
                        print(f"\n    Found {len(second_level)} second-level relationships from {target['label']}:")
                        
                        for j, level2_rel in enumerate(second_level[:3], 1):  # Show first 3
                            level2_target = db.get_node(level2_rel["target_id"])
                            
                            if level2_target:
                                level2_axis_info = db.axes[level2_target["axis"]]
                                print(f"    {j}. → [{level2_axis_info['name']}] {level2_target['label']} "
                                     f"({level2_rel['rel_type']}, weight: {level2_rel['weight']})")
                        
                        if len(second_level) > 3:
                            print(f"    (and {len(second_level) - 3} more...)")

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
#!/usr/bin/env python
"""
UKG Layer 1 Database Demo

This script demonstrates the Layer 1 database capabilities of the UKG system.
"""

import os
import time
import logging
from datetime import datetime
from simulation.layer1_database import Layer1Database
from simulation.data_generator import generate_sample_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(text, width=80):
    """Print a formatted header."""
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width)

def print_section(text, width=80):
    """Print a formatted section header."""
    print("\n" + "-" * width)
    print(text.center(width))
    print("-" * width)

def run_demo():
    """Run the UKG Layer 1 Database Demo."""
    start_time = time.time()
    
    print_header("UKG LAYER 1 DATABASE DEMO")
    print("This demo showcases the Layer 1 database capabilities of the UKG system.")
    
    # Initialize the database
    print_section("Initializing Layer 1 Database")
    db = Layer1Database()
    print("Layer 1 database initialized")
    
    # Generate sample data
    print("Generating sample data for all 13 axes...")
    generate_sample_data(db, num_nodes=50, num_relationships=75)
    
    # Export database to JSON
    db.export_to_json()
    
    # Print statistics
    stats = db.get_statistics()
    
    print(f"\nDatabase populated with {stats['total_nodes']} nodes and {stats['total_relationships']} relationships")
    
    print("\nNodes per axis:")
    for axis, count in stats['nodes_per_axis'].items():
        axis_name = stats['axis_names'].get(axis, 'Unknown')
        print(f"  Axis {axis} ({axis_name}): {count} nodes")
    
    print("\nRelationship types:")
    for rel_type, count in stats['relationships_per_type'].items():
        print(f"  {rel_type}: {count} relationships")
    
    # Demonstrate querying capabilities
    print_section("Database Querying Capabilities")
    
    # Example 1: Text search
    query = "artificial intelligence"
    print(f"Searching for '{query}':")
    results = db.search(query)
    for i, result in enumerate(results, 1):
        print(f"  {i}. [{result['axis_name']}] {result['label']}")
        print(f"     {result['description']}")
    
    # Example 2: Get nodes by axis
    axis_id = 6  # Regulatory Frameworks
    print(f"\nGetting all nodes for Axis {axis_id} ({db.get_axis_name(axis_id)}):")
    nodes = db.get_nodes_by_axis(axis_id)
    for i, node in enumerate(nodes, 1):
        print(f"  {i}. {node['label']}: {node['description']}")
    
    # Example 3: Get relationships for a node
    if nodes:
        node = nodes[0]
        print(f"\nGetting relationships for {node['label']}:")
        rels = db.get_relationships_for_node(node['id'])
        for i, rel in enumerate(rels, 1):
            direction = "→" if rel['direction'] == 'outgoing' else "←"
            print(f"  {i}. {direction} [{rel['other_node_axis_name']}] {rel['other_node_label']} "
                  f"({rel['type']}, weight: {rel['weight']})")
    
    # Example 4: Graph traversal
    print_section("Graph Traversal")
    
    # Find a sector node to start with
    sectors = db.get_nodes_by_axis(2)  # Axis 2: Sectors
    if sectors:
        start_node = sectors[0]
        print(f"Starting traversal from {start_node['label']} (Axis {start_node['axis_id']}: {db.get_axis_name(start_node['axis_id'])})")
        
        # Get outgoing relationships
        outgoing = db.get_outgoing_relationships(start_node['id'])
        print(f"\nFound {len(outgoing)} outgoing relationships:")
        
        for i, rel in enumerate(outgoing, 1):
            target_node = db.get_node(rel['target'])
            print(f"  {i}. → [{db.get_axis_name(target_node['axis_id'])}] {target_node['label']} "
                  f"({rel['type']}, weight: {rel['weight']})")
            
            # Get second-level relationships
            second_level = db.get_outgoing_relationships(target_node['id'])
            if second_level:
                print(f"\n    Found {len(second_level)} second-level relationships from {target_node['label']}:")
                for j, rel2 in enumerate(second_level, 1):
                    target2 = db.get_node(rel2['target'])
                    print(f"    {j}. → [{db.get_axis_name(target2['axis_id'])}] {target2['label']} "
                          f"({rel2['type']}, weight: {rel2['weight']})")
    
    # Demo completion
    end_time = time.time()
    print_header("DEMO COMPLETE")
    print(f"Total time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    run_demo()
