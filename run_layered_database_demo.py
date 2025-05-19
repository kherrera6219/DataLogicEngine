
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Nested Layered Database Demo

This script demonstrates the capabilities of the UKG's nested layered database,
showing the 13-axis system and various ways to query and traverse the knowledge graph.
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

from simulation.layer2_knowledge import NestedLayerDatabase, ThirteenAxisSystem, create_layer2_simulator

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

def show_database_stats(db: NestedLayerDatabase):
    """Display database statistics."""
    print_section("Database Statistics")
    
    # Count nodes per axis
    print("Nodes per axis:")
    for axis_num in range(1, 14):
        axis_info = db.axis_system.get_axis_info(axis_num)
        axis_name = axis_info.get("name", f"Axis {axis_num}")
        count = len(db.get_nodes_by_axis(axis_num))
        print(f"  Axis {axis_num} ({axis_name}): {count} nodes")
    
    # Count relationships by type
    print("\nRelationships by type:")
    rel_counts = {}
    for rel_id, rel in db.relationships.items():
        rel_type = rel.rel_type
        if rel_type not in rel_counts:
            rel_counts[rel_type] = 0
        rel_counts[rel_type] += 1
    
    for rel_type, count in sorted(rel_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")
    
    print(f"\nTotal: {len(db.nodes)} nodes, {len(db.relationships)} relationships")

def demonstrate_basic_search(db: NestedLayerDatabase):
    """Demonstrate basic node search functionality."""
    print_section("Basic Search")
    
    search_terms = ["knowledge", "compliance", "technology", "universal"]
    
    for term in search_terms:
        print(f"\nSearching for '{term}':")
        results = db.search_nodes(term)
        
        if results:
            print(f"Found {len(results)} matching nodes:")
            for i, node in enumerate(results[:5], 1):  # Show first 5 results
                axis_info = db.axis_system.get_axis_info(node["axis_number"])
                axis_name = axis_info.get("name", f"Axis {node['axis_number']}")
                print(f"  {i}. [{axis_name}] {node['label']} (Level {node['level']})")
                if node.get("description"):
                    print(f"     Description: {node['description'][:80]}...")
            
            if len(results) > 5:
                print(f"     ... and {len(results) - 5} more")
        else:
            print(f"No results found for '{term}'")

def demonstrate_neighborhood_traversal(db: NestedLayerDatabase):
    """Demonstrate neighborhood traversal."""
    print_section("Neighborhood Traversal")
    
    # Find a node with relationships to showcase
    all_nodes = []
    for axis_num in range(1, 14):
        nodes = db.get_nodes_by_axis(axis_num)
        if nodes:
            all_nodes.extend(nodes)
    
    target_node = None
    for node in all_nodes:
        node_id = node["node_id"]
        out_rels = db.get_outgoing_relationships(node_id)
        in_rels = db.get_incoming_relationships(node_id)
        
        if len(out_rels) > 0 or len(in_rels) > 0:
            target_node = node
            break
    
    if not target_node:
        print("No suitable node found for neighborhood traversal demo")
        return
    
    # Show node information
    axis_info = db.axis_system.get_axis_info(target_node["axis_number"])
    axis_name = axis_info.get("name", f"Axis {target_node['axis_number']}")
    
    print(f"Selected node: {target_node['label']} ({axis_name}, Level {target_node['level']})")
    print(f"Description: {target_node.get('description', 'N/A')}")
    
    # Get neighborhood
    print("\nExploring neighborhood with depth=1:")
    neighborhood = db.get_neighborhood(target_node["node_id"], depth=1)
    
    # Show neighbor nodes
    print(f"Found {len(neighborhood['nodes'])} nodes and {len(neighborhood['relationships'])} relationships")
    
    print("\nNeighbor nodes:")
    for i, node in enumerate(neighborhood['nodes'][:5], 1):  # Show first 5
        if node["node_id"] == target_node["node_id"]:
            continue  # Skip the origin node
            
        axis_info = db.axis_system.get_axis_info(node["axis_number"])
        axis_name = axis_info.get("name", f"Axis {node['axis_number']}")
        print(f"  {i}. [{axis_name}] {node['label']} (Level {node['level']})")
    
    # Show relationships
    print("\nRelationships:")
    for i, rel in enumerate(neighborhood['relationships'][:5], 1):  # Show first 5
        source_id = rel["source_id"]
        target_id = rel["target_id"]
        
        source_node = None
        target_node = None
        
        for node in neighborhood['nodes']:
            if node["node_id"] == source_id:
                source_node = node
            if node["node_id"] == target_id:
                target_node = node
        
        if source_node and target_node:
            print(f"  {i}. {source_node['label']} --[{rel['rel_type']}]--> {target_node['label']}")

def demonstrate_path_finding(db: NestedLayerDatabase):
    """Demonstrate path finding between nodes."""
    print_section("Path Finding")
    
    # Find nodes connected by paths
    all_nodes = []
    for axis_num in range(1, 14):
        nodes = db.get_nodes_by_axis(axis_num)
        if nodes:
            all_nodes.extend(nodes)
    
    # Find a pair of nodes that have a path between them
    source_node = None
    target_node = None
    
    for i, node1 in enumerate(all_nodes):
        for node2 in all_nodes[i+1:]:
            paths = db.find_paths(node1["node_id"], node2["node_id"], max_depth=3)
            if paths:
                source_node = node1
                target_node = node2
                break
        if source_node:
            break
    
    if not source_node or not target_node:
        print("No suitable node pair found for path finding demo")
        return
    
    # Show nodes
    print(f"Finding paths between:")
    
    axis_info1 = db.axis_system.get_axis_info(source_node["axis_number"])
    axis_name1 = axis_info1.get("name", f"Axis {source_node['axis_number']}")
    print(f"  Source: {source_node['label']} ({axis_name1}, Level {source_node['level']})")
    
    axis_info2 = db.axis_system.get_axis_info(target_node["axis_number"])
    axis_name2 = axis_info2.get("name", f"Axis {target_node['axis_number']}")
    print(f"  Target: {target_node['label']} ({axis_name2}, Level {target_node['level']})")
    
    # Find paths
    paths = db.find_paths(source_node["node_id"], target_node["node_id"], max_depth=3)
    
    print(f"\nFound {len(paths)} paths with max depth 3:")
    
    for i, path in enumerate(paths[:3], 1):  # Show first 3 paths
        print(f"\nPath {i} ({len(path)} steps):")
        
        source_id = source_node["node_id"]
        
        for j, rel in enumerate(path, 1):
            # Get the next node in the path
            target_id = rel["target_id"]
            target = db.get_node(target_id)
            
            if target:
                axis_info = db.axis_system.get_axis_info(target["axis_number"])
                axis_name = axis_info.get("name", f"Axis {target['axis_number']}")
                
                print(f"  Step {j}: --[{rel['rel_type']}]--> {target['label']} ({axis_name})")
            
            # Update source for next iteration
            source_id = target_id

def demonstrate_axis_system(db: NestedLayerDatabase):
    """Demonstrate the 13-axis system."""
    print_section("13-Axis System")
    
    # Show all axes
    print("The 13 axes of the UKG system:")
    for axis_num in range(1, 14):
        axis_info = db.axis_system.get_axis_info(axis_num)
        print(f"  {axis_num}. {axis_info['name']}: {axis_info['description']}")
    
    # Show axis relationships
    print("\nKey axis relationships:")
    axis_graph = db.axis_system.graph
    
    for source, target, data in sorted(axis_graph.edges(data=True), 
                                       key=lambda x: (x[0], x[1])):
        source_info = db.axis_system.get_axis_info(source)
        target_info = db.axis_system.get_axis_info(target)
        
        rel_type = data.get("rel_type", "related")
        weight = data.get("weight", 1.0)
        
        print(f"  Axis {source} ({source_info['name']}) --[{rel_type}]--> "
              f"Axis {target} ({target_info['name']})")

def demonstrate_quad_persona_integration(layer2_simulator):
    """Demonstrate how the database integrates with the Quad Persona Engine."""
    print_section("Quad Persona Integration")
    
    print("The Layer 2 Knowledge Simulator integrates:")
    print("1. The 13-axis nested database")
    print("2. The Quad Persona Engine")
    print("3. The Refinement Workflow")
    
    # Show database stats
    db_stats = layer2_simulator.get_database_stats()
    
    print("\nNestedLayerDatabase statistics:")
    print(f"  Total nodes: {db_stats['total_nodes']}")
    print(f"  Total relationships: {db_stats['total_relationships']}")
    
    print("\nNodes per axis:")
    for axis_num, count in sorted(db_stats['nodes_per_axis'].items()):
        if count > 0:
            axis_info = layer2_simulator.nested_db.axis_system.get_axis_info(int(axis_num))
            axis_name = axis_info.get("name", f"Axis {axis_num}")
            print(f"  Axis {axis_num} ({axis_name}): {count} nodes")
    
    # Show a sample query
    sample_query = "knowledge integration across domains"
    print(f"\nSample query: '{sample_query}'")
    
    query_result = layer2_simulator.query_knowledge_graph(sample_query)
    
    print(f"Found {query_result['count']} matching nodes in the knowledge graph")
    
    if query_result['count'] > 0:
        print("\nTop match:")
        top_result = query_result['results'][0]
        node = top_result['node']
        
        axis_info = layer2_simulator.nested_db.axis_system.get_axis_info(node["axis_number"])
        axis_name = axis_info.get("name", f"Axis {node['axis_number']}")
        
        print(f"  [{axis_name}] {node['label']} (Level {node['level']})")
        print(f"  Description: {node.get('description', 'N/A')}")
        
        neighbor_count = len(top_result['neighborhood']['nodes'])
        rel_count = len(top_result['neighborhood']['relationships'])
        
        print(f"  Connected to {neighbor_count-1} neighboring nodes with {rel_count} relationships")

def main():
    """Run the nested layered database demo."""
    print_header("UKG NESTED LAYERED DATABASE DEMO")
    print("This demo showcases the 13-axis system and in-memory database capabilities.")
    
    start_time = time.time()
    
    try:
        # Create Layer 2 simulator (which contains the nested database)
        layer2_simulator = create_layer2_simulator()
        
        # Show database statistics
        show_database_stats(layer2_simulator.nested_db)
        
        # Demonstrate axis system
        demonstrate_axis_system(layer2_simulator.nested_db)
        
        # Demonstrate basic node search
        demonstrate_basic_search(layer2_simulator.nested_db)
        
        # Demonstrate neighborhood traversal
        demonstrate_neighborhood_traversal(layer2_simulator.nested_db)
        
        # Demonstrate path finding
        demonstrate_path_finding(layer2_simulator.nested_db)
        
        # Demonstrate integration with Quad Persona Engine
        demonstrate_quad_persona_integration(layer2_simulator)
        
        print_header("DEMO COMPLETE")
        print(f"Total time: {time.time() - start_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error in database demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
