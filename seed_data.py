"""
Seed script for populating the UKG database with sample 17-axis knowledge graph data.
Run this script to populate the database with initial reference data.
"""

import uuid
from datetime import datetime
from app import app, db
from db_models import Node, Edge, PillarLevel, Sector, Domain

def generate_uid(prefix):
    """Generate a unique identifier with prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def seed_pillars():
    """Seed Pillar Levels (Axis 1: Knowledge)."""
    pillars_data = [
        {"pillar_id": "PL-1", "name": "Core Knowledge", "description": "Fundamental knowledge and principles"},
        {"pillar_id": "PL-2", "name": "Applied Sciences", "description": "Practical application of scientific principles"},
        {"pillar_id": "PL-3", "name": "Engineering", "description": "Design and construction of systems"},
        {"pillar_id": "PL-4", "name": "Technology", "description": "Tools, systems, and digital solutions"},
        {"pillar_id": "PL-5", "name": "Business & Commerce", "description": "Commercial and economic activities"},
        {"pillar_id": "PL-6", "name": "Legal & Regulatory", "description": "Laws, regulations, and compliance"},
        {"pillar_id": "PL-7", "name": "Healthcare & Medicine", "description": "Medical and health sciences"},
        {"pillar_id": "PL-8", "name": "Finance & Banking", "description": "Financial systems and services"},
        {"pillar_id": "PL-9", "name": "Government & Public", "description": "Public sector and governance"},
        {"pillar_id": "PL-10", "name": "Education", "description": "Learning and knowledge transfer"},
        {"pillar_id": "PL-11", "name": "Research & Development", "description": "Innovation and discovery"},
        {"pillar_id": "PL-12", "name": "Manufacturing", "description": "Production and fabrication"},
        {"pillar_id": "PL-13", "name": "Defense & Security", "description": "National security and defense"},
        {"pillar_id": "PL-14", "name": "Energy & Utilities", "description": "Power generation and distribution"},
        {"pillar_id": "PL-15", "name": "Transportation", "description": "Movement of goods and people"},
        {"pillar_id": "PL-16", "name": "Communications", "description": "Information exchange systems"},
        {"pillar_id": "PL-17", "name": "Environment", "description": "Ecological and sustainability"},
    ]
    
    created = 0
    for data in pillars_data:
        existing = PillarLevel.query.filter_by(pillar_id=data["pillar_id"]).first()
        if not existing:
            pillar = PillarLevel(
                uid=generate_uid("pillar"),
                pillar_id=data["pillar_id"],
                name=data["name"],
                description=data["description"]
            )
            db.session.add(pillar)
            created += 1
    
    db.session.commit()
    print(f"Seeded {created} pillars")
    return created

def seed_sectors():
    """Seed Sectors (Axis 2: Sectors)."""
    sectors_data = [
        {"sector_code": "GOV", "name": "Government", "description": "Federal, state, and local government"},
        {"sector_code": "FIN", "name": "Financial Services", "description": "Banking, insurance, investments"},
        {"sector_code": "TECH", "name": "Technology", "description": "Software, hardware, IT services"},
        {"sector_code": "HEALTH", "name": "Healthcare", "description": "Medical services and pharmaceuticals"},
        {"sector_code": "MANU", "name": "Manufacturing", "description": "Industrial production"},
        {"sector_code": "RETAIL", "name": "Retail", "description": "Consumer goods and services"},
        {"sector_code": "ENERGY", "name": "Energy", "description": "Oil, gas, renewables, utilities"},
        {"sector_code": "TRANS", "name": "Transportation", "description": "Logistics and mobility"},
        {"sector_code": "TELECOM", "name": "Telecommunications", "description": "Communication networks"},
        {"sector_code": "AERO", "name": "Aerospace & Defense", "description": "Aviation and defense systems"},
        {"sector_code": "EDU", "name": "Education", "description": "Schools, universities, training"},
        {"sector_code": "MEDIA", "name": "Media & Entertainment", "description": "Broadcasting, publishing, gaming"},
        {"sector_code": "AGRI", "name": "Agriculture", "description": "Farming and food production"},
        {"sector_code": "CONSTR", "name": "Construction", "description": "Building and infrastructure"},
        {"sector_code": "PROF", "name": "Professional Services", "description": "Consulting, legal, accounting"},
    ]
    
    created = 0
    for data in sectors_data:
        existing = Sector.query.filter_by(sector_code=data["sector_code"]).first()
        if not existing:
            sector = Sector(
                uid=generate_uid("sector"),
                sector_code=data["sector_code"],
                name=data["name"],
                description=data["description"]
            )
            db.session.add(sector)
            created += 1
    
    db.session.commit()
    print(f"Seeded {created} sectors")
    return created

def seed_domains():
    """Seed Domains (Axis 3: Domains)."""
    domains_data = [
        {"domain_code": "FEDGOV", "name": "Federal Government", "sector_code": "GOV"},
        {"domain_code": "STATEGOV", "name": "State Government", "sector_code": "GOV"},
        {"domain_code": "LOCALGOV", "name": "Local Government", "sector_code": "GOV"},
        {"domain_code": "BANKING", "name": "Banking", "sector_code": "FIN"},
        {"domain_code": "INSURANCE", "name": "Insurance", "sector_code": "FIN"},
        {"domain_code": "INVEST", "name": "Investment Management", "sector_code": "FIN"},
        {"domain_code": "SOFTWARE", "name": "Software Development", "sector_code": "TECH"},
        {"domain_code": "CLOUD", "name": "Cloud Computing", "sector_code": "TECH"},
        {"domain_code": "CYBERSEC", "name": "Cybersecurity", "sector_code": "TECH"},
        {"domain_code": "AI_ML", "name": "AI & Machine Learning", "sector_code": "TECH"},
        {"domain_code": "HOSPITAL", "name": "Hospitals", "sector_code": "HEALTH"},
        {"domain_code": "PHARMA", "name": "Pharmaceuticals", "sector_code": "HEALTH"},
        {"domain_code": "BIOTECH", "name": "Biotechnology", "sector_code": "HEALTH"},
    ]
    
    created = 0
    for data in domains_data:
        existing = Domain.query.filter_by(domain_code=data["domain_code"]).first()
        if not existing:
            sector = Sector.query.filter_by(sector_code=data["sector_code"]).first()
            domain = Domain(
                uid=generate_uid("domain"),
                domain_code=data["domain_code"],
                name=data["name"],
                description=f"{data['name']} domain",
                sector_id=sector.id if sector else None
            )
            db.session.add(domain)
            created += 1
    
    db.session.commit()
    print(f"Seeded {created} domains")
    return created

def seed_nodes():
    """Seed knowledge graph nodes representing the 17 axes."""
    nodes_data = [
        {"node_type": "axis", "label": "Axis 1: Pillar Levels", "axis_number": 1, "description": "Hierarchical knowledge pillars"},
        {"node_type": "axis", "label": "Axis 2: Sectors", "axis_number": 2, "description": "Industry and business sectors"},
        {"node_type": "axis", "label": "Axis 3: Honeycomb Domains", "axis_number": 3, "description": "Specialized knowledge domains"},
        {"node_type": "axis", "label": "Axis 4: Branches", "axis_number": 4, "description": "Topic branches and subdivisions"},
        {"node_type": "axis", "label": "Axis 5: Nodes", "axis_number": 5, "description": "Individual knowledge nodes"},
        {"node_type": "axis", "label": "Axis 6: Octopus Crosswalk", "axis_number": 6, "description": "One-to-many relationships"},
        {"node_type": "axis", "label": "Axis 7: Spiderweb Crosswalk", "axis_number": 7, "description": "Many-to-many relationships"},
        {"node_type": "axis", "label": "Axis 8: Knowledge Expert", "axis_number": 8, "description": "Subject matter experts"},
        {"node_type": "axis", "label": "Axis 9: Qualification Expert", "axis_number": 9, "description": "Certification and credentials"},
        {"node_type": "axis", "label": "Axis 10: Regulatory Expert", "axis_number": 10, "description": "Regulatory frameworks"},
        {"node_type": "axis", "label": "Axis 11: Compliance Expert", "axis_number": 11, "description": "Compliance requirements"},
        {"node_type": "axis", "label": "Axis 12: Location Context", "axis_number": 12, "description": "Geographic and jurisdictional"},
        {"node_type": "axis", "label": "Axis 13: Temporal Context", "axis_number": 13, "description": "Time-based context"},
        {"node_type": "axis", "label": "Axis 14: Risk & Confidence", "axis_number": 14, "description": "Risk assessment and confidence levels"},
        {"node_type": "axis", "label": "Axis 15: Federated Intelligence", "axis_number": 15, "description": "Distributed knowledge sources"},
        {"node_type": "axis", "label": "Axis 16: Arrows of Time", "axis_number": 16, "description": "Temporal flow and causality"},
        {"node_type": "axis", "label": "Axis 17: Observability & Analytics", "axis_number": 17, "description": "Metrics and monitoring"},
        {"node_type": "concept", "label": "FAR Regulations", "axis_number": 6, "description": "Federal Acquisition Regulation"},
        {"node_type": "concept", "label": "DFARS", "axis_number": 6, "description": "Defense Federal Acquisition Regulation Supplement"},
        {"node_type": "concept", "label": "NAICS Codes", "axis_number": 2, "description": "North American Industry Classification System"},
        {"node_type": "concept", "label": "ISO Standards", "axis_number": 9, "description": "International Organization for Standardization"},
        {"node_type": "concept", "label": "NIST Framework", "axis_number": 10, "description": "National Institute of Standards and Technology"},
        {"node_type": "concept", "label": "SOC 2 Compliance", "axis_number": 11, "description": "Service Organization Control 2"},
        {"node_type": "concept", "label": "GDPR", "axis_number": 11, "description": "General Data Protection Regulation"},
        {"node_type": "concept", "label": "HIPAA", "axis_number": 11, "description": "Health Insurance Portability and Accountability Act"},
    ]
    
    created = 0
    for data in nodes_data:
        existing = Node.query.filter_by(label=data["label"]).first()
        if not existing:
            node = Node(
                uid=generate_uid("node"),
                node_type=data["node_type"],
                label=data["label"],
                axis_number=data["axis_number"],
                description=data["description"],
                attributes={"created_by": "seed_script"}
            )
            db.session.add(node)
            created += 1
    
    db.session.commit()
    print(f"Seeded {created} nodes")
    return created

def seed_edges():
    """Seed relationships between nodes."""
    axis_nodes = Node.query.filter_by(node_type="axis").all()
    if len(axis_nodes) < 2:
        print("Not enough axis nodes to create edges")
        return 0
    
    created = 0
    for i, source in enumerate(axis_nodes[:-1]):
        target = axis_nodes[i + 1]
        existing = Edge.query.filter_by(
            source_node_id=source.id,
            target_node_id=target.id
        ).first()
        if not existing:
            edge = Edge(
                uid=generate_uid("edge"),
                edge_type="sequential",
                weight=1.0,
                source_node_id=source.id,
                target_node_id=target.id,
                attributes={"relationship": "follows"}
            )
            db.session.add(edge)
            created += 1
    
    db.session.commit()
    print(f"Seeded {created} edges")
    return created

def run_seed():
    """Run all seed functions."""
    with app.app_context():
        print("Starting database seed...")
        
        print("Creating tables if they don't exist...")
        db.create_all()
        
        pillars = seed_pillars()
        sectors = seed_sectors()
        domains = seed_domains()
        nodes = seed_nodes()
        edges = seed_edges()
        
        total = pillars + sectors + domains + nodes + edges
        print(f"\nSeed complete! Created {total} records total.")
        return total

if __name__ == "__main__":
    run_seed()
