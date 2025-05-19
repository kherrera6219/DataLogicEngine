#!/usr/bin/env python3
"""
Data Generator Module

This module provides functions to generate sample data for the UKG system.
It populates the Layer 1 database with nodes and relationships across the 13 axes.
"""

import random
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def generate_sample_data(db, num_nodes=50, num_relationships=75):
    """
    Generate sample data for the UKG database.

    Args:
        db: Layer1Database instance
        num_nodes: Number of nodes to generate
        num_relationships: Number of relationships to generate
    """
    logger.info(f"Generating {num_nodes} nodes and {num_relationships} relationships")

    # Step 1: Generate nodes for each axis
    nodes_by_axis = generate_all_axis_data(db, num_nodes)

    # Step 2: Generate relationships between nodes
    relationships = generate_relationships(db, nodes_by_axis, num_relationships)

    logger.info(f"Generated {sum(len(nodes) for nodes in nodes_by_axis.values())} nodes and {len(relationships)} relationships")
    return nodes_by_axis, relationships

def generate_all_axis_data(db, total_nodes=50):
    """
    Generate data for all 13 axes.

    Args:
        db: Layer1Database instance
        total_nodes: Total number of nodes to generate

    Returns:
        Dictionary mapping axis numbers to lists of node data
    """
    # Distribute nodes across axes
    nodes_per_axis = distribute_nodes(total_nodes, 13)
    nodes_by_axis = {}

    # Axis 1: Pillar Levels
    pillar_levels = [
        {"label": "Universal", "level": 1, "description": "Universal principles and concepts"},
        {"label": "Conceptual", "level": 2, "description": "Broad conceptual frameworks"},
        {"label": "Domain", "level": 3, "description": "Specific knowledge domains"},
        {"label": "Applied", "level": 4, "description": "Applied knowledge for specific contexts"},
        {"label": "Implementation", "level": 5, "description": "Concrete implementations"}
    ]

    # Add pillar levels with fixed structure
    for pillar in pillar_levels:
        node_id = db.add_node(
            axis=1,
            label=pillar["label"],
            level=pillar["level"],
            description=pillar["description"],
            attributes={"system": "core"}
        )

    # Generate additional nodes for the remaining allocation
    remaining_axis1 = nodes_per_axis[1] - len(pillar_levels)
    for i in range(remaining_axis1):
        level = random.randint(1, 5)
        node_id = db.add_node(
            axis=1,
            label=f"Pillar Level {level}.{i+1}",
            level=level,
            description=f"Extended pillar level {level}.{i+1}",
            attributes={"system": "extended"}
        )

    # Axis 2: Sectors
    sectors = ["Technology", "Healthcare", "Finance", "Education", "Manufacturing", 
               "Energy", "Transportation", "Retail", "Agriculture", "Government"]

    for i, sector in enumerate(sectors[:nodes_per_axis[2]]):
        level = random.randint(1, 3)  # Different sector categories
        node_id = db.add_node(
            axis=2,
            label=sector,
            level=level,
            description=f"{sector} sector including related industries",
            attributes={"code": f"SEC{i+1:03d}"}
        )

    # Axis 3: Topics
    topics = ["Artificial Intelligence", "Climate Change", "Cryptography", "Quantum Computing",
              "Renewable Energy", "Blockchain", "Genetics", "Neuroscience", "Cybersecurity",
              "Machine Learning", "Data Science", "Robotics", "Internet of Things"]

    for i, topic in enumerate(topics[:nodes_per_axis[3]]):
        level = random.randint(1, 4)  # Topic depth level
        node_id = db.add_node(
            axis=3,
            label=topic,
            level=level,
            description=f"Knowledge topic: {topic}",
            attributes={"keywords": topic.lower().split()}
        )

    # Axis 4: Methods
    methods = ["Statistical Analysis", "Qualitative Research", "Experimental Design",
               "Case Study", "Survey", "Simulation", "Data Mining", "Literature Review",
               "Observational Study", "Interview", "Focus Group", "Meta-Analysis"]

    for i, method in enumerate(methods[:nodes_per_axis[4]]):
        level = random.randint(1, 3)  # Method complexity level
        node_id = db.add_node(
            axis=4,
            label=method,
            level=level,
            description=f"Research method: {method}",
            attributes={"rigor": random.uniform(0.5, 1.0)}
        )

    # Axis 5: Tools
    tools = ["TensorFlow", "Python", "SPSS", "MATLAB", "R", "Jupyter",
             "Power BI", "Excel", "SQL", "Tableau", "SAS", "PyTorch"]

    for i, tool in enumerate(tools[:nodes_per_axis[5]]):
        level = random.randint(1, 3)  # Tool sophistication level
        node_id = db.add_node(
            axis=5,
            label=tool,
            level=level,
            description=f"Tool or software: {tool}",
            attributes={"version": f"{random.randint(1, 10)}.{random.randint(0, 9)}"}
        )

    # Axis 6: Regulatory Frameworks
    regulations = ["GDPR", "HIPAA", "Sarbanes-Oxley", "CCPA", "Basel III",
                   "FDA Regulations", "NIST", "ISO 27001", "PCI DSS", "FSMA"]

    for i, reg in enumerate(regulations[:nodes_per_axis[6]]):
        level = random.randint(1, 3)  # Regulatory scope level
        node_id = db.add_node(
            axis=6,
            label=reg,
            level=level,
            description=f"Regulatory framework: {reg}",
            attributes={"year": random.randint(1990, 2023)}
        )

    # Axis 7: Compliance Standards
    standards = ["ISO 9001", "ISO 14001", "ISO 45001", "ISO 31000", "ISO 22000",
                "CMMI", "Six Sigma", "COBIT", "ITIL", "OSHA Standards"]

    for i, standard in enumerate(standards[:nodes_per_axis[7]]):
        level = random.randint(1, 3)  # Standard rigor level
        node_id = db.add_node(
            axis=7,
            label=standard,
            level=level,
            description=f"Compliance standard: {standard}",
            attributes={"category": random.choice(["Quality", "Security", "Safety", "Environmental"])}
        )

    # Axis 8-11: Expert Roles (4 Quad Personas)
    expert_types = {
        8: "Knowledge Expert",
        9: "Sector Expert",
        10: "Regulatory Expert",
        11: "Compliance Expert"
    }

    domains = ["Technology", "Healthcare", "Finance", "Manufacturing", "Energy"]

    for axis in range(8, 12):
        expert_type = expert_types[axis]
        for i in range(nodes_per_axis[axis]):
            domain = random.choice(domains)
            node_id = db.add_node(
                axis=axis,
                label=f"{domain} {expert_type}",
                level=random.randint(1, 3),  # Expertise level
                description=f"{expert_type} specializing in {domain}",
                attributes={"experience_years": random.randint(3, 20)}
            )

    # Axis 12: Locations
    locations = ["United States", "European Union", "China", "Japan", "India",
                "Brazil", "Australia", "Canada", "United Kingdom", "Germany"]

    for i, location in enumerate(locations[:nodes_per_axis[12]]):
        node_id = db.add_node(
            axis=12,
            label=location,
            level=1,  # Geographic level (1=country, 2=region, 3=city)
            description=f"Geographic location: {location}",
            attributes={"latitude": random.uniform(-90, 90), "longitude": random.uniform(-180, 180)}
        )

    # Axis 13: Time
    # Generate time periods
    now = datetime.now()
    periods = [
        {"label": "Present", "start": now - timedelta(days=30), "end": now},
        {"label": "Recent Past", "start": now - timedelta(days=365), "end": now - timedelta(days=30)},
        {"label": "Near Future", "start": now, "end": now + timedelta(days=365)},
        {"label": "Mid Future", "start": now + timedelta(days=365), "end": now + timedelta(days=365*3)}
    ]

    for i, period in enumerate(periods[:nodes_per_axis[13]]):
        node_id = db.add_node(
            axis=13,
            label=period["label"],
            level=1,
            description=f"Time period: {period['label']}",
            attributes={
                "start_date": period["start"].isoformat(),
                "end_date": period["end"].isoformat()
            }
        )

    # Compile all nodes by axis
    for axis in range(1, 14):
        nodes_by_axis[axis] = db.get_nodes_by_axis(axis)

    return nodes_by_axis

def generate_relationships(db, nodes_by_axis, num_relationships=75):
    """
    Generate relationships between nodes.

    Args:
        db: Layer1Database instance
        nodes_by_axis: Dictionary mapping axis numbers to lists of node data
        num_relationships: Number of relationships to generate

    Returns:
        List of relationship data
    """
    relationships = []

    # Define relationship types based on axis combinations
    rel_types = {
        (1, 2): ["classifies", "applies_to"],  # Pillar Level to Sector
        (1, 3): ["contains", "defines"],  # Pillar Level to Topic
        (2, 3): ["covers", "includes"],  # Sector to Topic
        (3, 4): ["uses", "applies"],  # Topic to Method
        (4, 5): ["employs", "utilizes"],  # Method to Tool
        (3, 6): ["regulated_by", "governed_by"],  # Topic to Regulatory
        (6, 7): ["enforces", "implements"],  # Regulatory to Compliance
        (8, 3): ["specializes_in", "researches"],  # Knowledge Expert to Topic
        (9, 2): ["works_in", "advises_on"],  # Sector Expert to Sector
        (10, 6): ["interprets", "enforces"],  # Regulatory Expert to Regulatory
        (11, 7): ["implements", "manages"],  # Compliance Expert to Compliance
        (12, 2): ["hosts", "contains"],  # Location to Sector
        (13, 6): ["applies_during", "valid_in"]  # Time to Regulatory
    }

    # Generic relationship types for other combinations
    generic_rel_types = ["related_to", "connected_with", "associated_with", "linked_to"]

    # Create relationships between axes based on defined types
    created = 0

    # First create structured axis-to-axis relationships
    for (source_axis, target_axis), types in rel_types.items():
        source_nodes = nodes_by_axis.get(source_axis, [])
        target_nodes = nodes_by_axis.get(target_axis, [])

        if not source_nodes or not target_nodes:
            continue

        # Create 1-3 relationships between each axis pair
        for _ in range(min(3, len(source_nodes), len(target_nodes))):
            source_node = random.choice(source_nodes)
            target_node = random.choice(target_nodes)
            rel_type = random.choice(types)

            try:
                rel_id = db.add_relationship(
                    source_id=source_node["node_id"],
                    target_id=target_node["node_id"],
                    rel_type=rel_type,
                    weight=random.uniform(0.5, 1.0),
                    attributes={"generated": True}
                )
                relationships.append(db.get_relationship(rel_id))
                created += 1
            except Exception as e:
                logger.warning(f"Could not create relationship: {str(e)}")

    # Fill the remaining relationships with random connections
    while created < num_relationships:
        # Choose random axes
        source_axis = random.randint(1, 13)
        target_axis = random.randint(1, 13)

        source_nodes = nodes_by_axis.get(source_axis, [])
        target_nodes = nodes_by_axis.get(target_axis, [])

        if not source_nodes or not target_nodes:
            continue

        source_node = random.choice(source_nodes)
        target_node = random.choice(target_nodes)

        # Determine relationship type
        if (source_axis, target_axis) in rel_types:
            rel_type = random.choice(rel_types[(source_axis, target_axis)])
        else:
            rel_type = random.choice(generic_rel_types)

        try:
            # Don't add duplicate relationships
            source_id = source_node["node_id"]
            target_id = target_node["node_id"]

            # Check if this relationship already exists
            existing = False
            for rel in relationships:
                if rel["source_id"] == source_id and rel["target_id"] == target_id:
                    existing = True
                    break

            if not existing:
                rel_id = db.add_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    rel_type=rel_type,
                    weight=random.uniform(0.5, 1.0),
                    attributes={"generated": True}
                )
                relationships.append(db.get_relationship(rel_id))
                created += 1
        except Exception as e:
            logger.warning(f"Could not create relationship: {str(e)}")

    return relationships

def distribute_nodes(total_nodes, num_axes):
    """
    Distribute a total number of nodes across axes.

    Args:
        total_nodes: Total number of nodes
        num_axes: Number of axes

    Returns:
        Dictionary mapping axis numbers to node counts
    """
    # Ensure each axis gets at least one node
    base_nodes = total_nodes // num_axes
    extra_nodes = total_nodes % num_axes

    distribution = {i: base_nodes for i in range(1, num_axes + 1)}

    # Distribute extra nodes, prioritizing more important axes
    priority_axes = [1, 2, 3, 8, 9, 10, 11]  # Priority axes

    for axis in priority_axes:
        if extra_nodes > 0:
            distribution[axis] += 1
            extra_nodes -= 1

    # Distribute any remaining extra nodes
    for axis in range(1, num_axes + 1):
        if extra_nodes > 0:
            distribution[axis] += 1
            extra_nodes -= 1

    return distribution