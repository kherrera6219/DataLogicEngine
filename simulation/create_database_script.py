
#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Initialize Layer 1 Database

This script initializes the Layer 1 of the UKG system's nested layered database,
establishing the core structure for the 13-axis knowledge system.
"""

import os
import sys
import logging
import time
import json
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.layer2_knowledge import NestedLayerDatabase, ThirteenAxisSystem

def create_initial_data(db: NestedLayerDatabase) -> Dict[str, int]:
    """
    Create initial seed data for all 13 axes if data files are not available.
    
    Args:
        db: Nested layer database instance
        
    Returns:
        Dictionary with nodes created per axis
    """
    created = {}
    
    # Axis 1: Pillar Levels
    pillar_levels = [
        {"label": "Universal", "level": 1, "description": "Highest level abstractions and universal principles"},
        {"label": "Conceptual", "level": 2, "description": "Broad conceptual frameworks and theories"},
        {"label": "Domain", "level": 3, "description": "Specific knowledge domains and disciplines"},
        {"label": "Applied", "level": 4, "description": "Applied knowledge in specific contexts"},
        {"label": "Specific", "level": 5, "description": "Highly specific implementations and instances"}
    ]
    
    created[1] = 0
    for pillar in pillar_levels:
        db.add_node(
            axis_number=1,
            level=pillar["level"],
            label=pillar["label"],
            description=pillar["description"],
            attributes={"system": "core"}
        )
        created[1] += 1
    
    # Axis 2: Sectors
    sectors = [
        {"label": "Technology", "level": 1, "description": "Information technology and digital systems"},
        {"label": "Healthcare", "level": 1, "description": "Medical and health-related fields"},
        {"label": "Finance", "level": 1, "description": "Financial services and economics"},
        {"label": "Education", "level": 1, "description": "Educational institutions and learning systems"},
        {"label": "Government", "level": 1, "description": "Government agencies and public administration"},
        {"label": "Manufacturing", "level": 1, "description": "Production and industrial processes"}
    ]
    
    created[2] = 0
    for sector in sectors:
        db.add_node(
            axis_number=2,
            level=sector["level"],
            label=sector["label"],
            description=sector["description"],
            attributes={"system": "core"}
        )
        created[2] += 1
    
    # Axis 8-11: The four personas
    personas = [
        {"axis_number": 8, "label": "Knowledge Expert", "level": 1, 
         "description": "Domain knowledge specialist with deep theoretical understanding"},
        {"axis_number": 9, "label": "Sector Expert", "level": 1, 
         "description": "Industry specialist with practical sector experience"},
        {"axis_number": 10, "label": "Regulatory Expert", "level": 1, 
         "description": "Specialist in regulatory frameworks and legal requirements"},
        {"axis_number": 11, "label": "Compliance Expert", "level": 1, 
         "description": "Specialist in implementing compliance measures and standards"}
    ]
    
    for persona in personas:
        axis_num = persona["axis_number"]
        if axis_num not in created:
            created[axis_num] = 0
        
        db.add_node(
            axis_number=axis_num,
            level=persona["level"],
            label=persona["label"],
            description=persona["description"],
            attributes={"system": "core", "persona_type": "quad_persona"}
        )
        created[axis_num] += 1
    
    # Add minimal data for other axes
    other_axes = [
        (3, "Topics", "Subject matters and areas of interest"),
        (4, "Methods", "Methodologies, approaches, and procedures"),
        (5, "Tools", "Software, hardware, and resources used in various domains"),
        (6, "Regulatory Frameworks", "Laws, regulations, and legal frameworks"),
        (7, "Compliance Standards", "Standards, best practices, and compliance requirements"),
        (12, "Locations", "Geographic and jurisdictional locations"),
        (13, "Time", "Temporal dimensions and historical periods")
    ]
    
    for axis_num, label, description in other_axes:
        if axis_num not in created:
            created[axis_num] = 0
        
        db.add_node(
            axis_number=axis_num,
            level=1,
            label=label,
            description=description,
            attributes={"system": "core"}
        )
        created[axis_num] += 1
    
    return created

def create_relationships(db: NestedLayerDatabase) -> int:
    """
    Create fundamental relationships between nodes based on the 13-axis system.
    
    Args:
        db: Nested layer database instance
        
    Returns:
        Number of relationships created
    """
    created = 0
    
    # Connect pillar levels hierarchically (Axis 1)
    pillar_nodes = db.get_nodes_by_axis(1)
    pillar_nodes_by_level = {}
    
    for node in pillar_nodes:
        level = node.get('level', 0)
        if level not in pillar_nodes_by_level:
            pillar_nodes_by_level[level] = []
        pillar_nodes_by_level[level].append(node)
    
    # Connect each level to the next
    levels = sorted(pillar_nodes_by_level.keys())
    for i in range(len(levels) - 1):
        for parent_node in pillar_nodes_by_level[levels[i]]:
            for child_node in pillar_nodes_by_level[levels[i + 1]]:
                db.add_relationship(
                    source_id=parent_node['node_id'],
                    target_id=child_node['node_id'],
                    rel_type="contains",
                    weight=0.9,
                    attributes={"system": "core"}
                )
                created += 1
    
    # Connect Quad Personas in a cycle (Axes 8-11)
    persona_axis_order = [8, 9, 10, 11, 8]  # Repeat 8 to close the cycle
    
    for i in range(len(persona_axis_order) - 1):
        source_axis = persona_axis_order[i]
        target_axis = persona_axis_order[i + 1]
        
        source_nodes = db.get_nodes_by_axis(source_axis)
        target_nodes = db.get_nodes_by_axis(target_axis)
        
        for source_node in source_nodes:
            for target_node in target_nodes:
                db.add_relationship(
                    source_id=source_node['node_id'],
                    target_id=target_node['node_id'],
                    rel_type="informs",
                    weight=0.8,
                    attributes={"system": "quad_persona_cycle"}
                )
                created += 1
    
    # Connect sectors (Axis 2) to Sector Experts (Axis 9)
    sector_nodes = db.get_nodes_by_axis(2)
    expert_nodes = db.get_nodes_by_axis(9)
    
    for sector_node in sector_nodes:
        for expert_node in expert_nodes:
            db.add_relationship(
                source_id=expert_node['node_id'],
                target_id=sector_node['node_id'],
                rel_type="expertise_in",
                weight=0.9,
                attributes={"system": "expertise_mapping"}
            )
            created += 1
    
    return created

def main():
    """Initialize the Layer 1 database and save statistics."""
    logger.info("Starting Layer 1 database creation")
    start_time = time.time()
    
    try:
        # Create the nested database
        db = NestedLayerDatabase()
        logger.info("Created NestedLayerDatabase instance")
        
        # Try to load data from files first
        load_results = db.load_all_data()
        total_loaded = sum(load_results.values())
        
        if total_loaded > 0:
            logger.info(f"Loaded {total_loaded} nodes from data files")
        else:
            logger.info("No data files found or loaded, creating seed data")
            created_results = create_initial_data(db)
            total_created = sum(created_results.values())
            logger.info(f"Created {total_created} seed nodes")
        
        # Create core relationships
        rel_count = create_relationships(db)
        logger.info(f"Created {rel_count} core relationships")
        
        # Save database statistics
        stats = {
            "nodes": len(db.nodes),
            "relationships": len(db.relationships),
            "nodes_per_axis": {str(i): len(db.get_nodes_by_axis(i)) for i in range(1, 14)},
            "time_taken": time.time() - start_time
        }
        
        # Create output directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Save statistics
        with open("data/layer1_database_stats.json", "w") as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Database creation completed in {stats['time_taken']:.2f} seconds")
        logger.info(f"Created {stats['nodes']} nodes and {stats['relationships']} relationships")
        
    except Exception as e:
        logger.error(f"Error creating Layer 1 database: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
