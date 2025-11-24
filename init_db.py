"""
Universal Knowledge Graph (UKG) System - Database Initialization Script

This script initializes the database with required tables and sample data.

SECURITY WARNING: This script contains hardcoded development credentials.
These should NEVER be used in production. Always use strong, unique passwords
and consider using environment variables or a secrets management system.
"""

import os
import logging
from datetime import datetime
import uuid

from app import app
from extensions import db
from models import User, SimulationSession, KnowledgeGraphNode, KnowledgeGraphEdge

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_admin_user():
    """Create an admin user if one doesn't exist"""
    admin = User.query.filter_by(username='admin').first()
    
    if admin is None:
        logger.info("Creating admin user")
        admin = User()
        admin.username = 'admin'
        admin.email = 'admin@ukg-system.com'
        admin.active = True
        admin.is_admin = True
        admin.created_at = datetime.utcnow()
        # SECURITY WARNING: Change this default password immediately in production!
        admin.set_password('admin123')  # DEVELOPMENT ONLY - Use strong passwords in production
        
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created")
    else:
        logger.info("Admin user already exists")

def create_demo_user():
    """Create a demo user if one doesn't exist"""
    demo = User.query.filter_by(username='demo').first()
    
    if demo is None:
        logger.info("Creating demo user")
        demo = User()
        demo.username = 'demo'
        demo.email = 'demo@ukg-system.com'
        demo.active = True
        demo.is_admin = False
        demo.created_at = datetime.utcnow()
        # SECURITY WARNING: Change this default password immediately in production!
        demo.set_password('demo123')  # DEVELOPMENT ONLY - Use strong passwords in production
        
        db.session.add(demo)
        db.session.commit()
        logger.info("Demo user created")
    else:
        logger.info("Demo user already exists")

def create_sample_simulations():
    """Create sample simulation sessions for demo"""
    demo = User.query.filter_by(username='demo').first()
    
    if demo and SimulationSession.query.count() == 0:
        logger.info("Creating sample simulation sessions")
        
        # Completed simulation
        completed_sim = SimulationSession()
        completed_sim.session_id = str(uuid.uuid4())
        completed_sim.user_id = demo.id
        completed_sim.name = "Knowledge Integration Simulation"
        completed_sim.description = "Multi-perspective knowledge integration across domains with quantum-enhanced reasoning"
        completed_sim.parameters = {
            "simulation_type": "quantum",
            "refinement_steps": 12,
            "confidence_threshold": 0.85,
            "entropy_sampling": True
        }
        completed_sim.status = "completed"
        completed_sim.current_step = 8
        completed_sim.total_steps = 8
        completed_sim.created_at = datetime.utcnow()
        completed_sim.started_at = datetime.utcnow()
        completed_sim.completed_at = datetime.utcnow()
        completed_sim.results = {
            "confidence_score": 0.92,
            "coherence_score": 0.88,
            "entropy_reduction": 0.76,
            "summary": "Successfully integrated knowledge from 4 perspectives with balanced insights"
        }
        
        # Running simulation
        running_sim = SimulationSession()
        running_sim.session_id = str(uuid.uuid4())
        running_sim.user_id = demo.id
        running_sim.name = "Recursive AGI Simulation"
        running_sim.description = "Self-improvement and reasoning optimization using recursive AGI architecture"
        running_sim.parameters = {
            "simulation_type": "recursive",
            "refinement_steps": 16,
            "confidence_threshold": 0.90,
            "entropy_sampling": True
        }
        running_sim.status = "running"
        running_sim.current_step = 5
        running_sim.total_steps = 8
        running_sim.created_at = datetime.utcnow()
        running_sim.started_at = datetime.utcnow()
        
        # Pending simulation
        pending_sim = SimulationSession()
        pending_sim.session_id = str(uuid.uuid4())
        pending_sim.user_id = demo.id
        pending_sim.name = "Quad Persona Analysis"
        pending_sim.description = "Multi-perspective expert simulation for comprehensive domain analysis"
        pending_sim.parameters = {
            "simulation_type": "quad",
            "refinement_steps": 8,
            "confidence_threshold": 0.80,
            "entropy_sampling": False
        }
        pending_sim.status = "pending"
        pending_sim.current_step = 0
        pending_sim.total_steps = 8
        pending_sim.created_at = datetime.utcnow()
        
        db.session.add_all([completed_sim, running_sim, pending_sim])
        db.session.commit()
        logger.info("Sample simulation sessions created")
    else:
        logger.info("Sample simulation sessions already exist or demo user not found")

def create_sample_graph_nodes():
    """Create sample knowledge graph nodes and edges"""
    if KnowledgeGraphNode.query.count() == 0:
        logger.info("Creating sample knowledge graph nodes")
        
        # Create nodes
        center_node = KnowledgeGraphNode()
        center_node.node_id = "kg-central"
        center_node.node_type = "central"
        center_node.label = "Universal Knowledge Graph"
        center_node.description = "Central node representing the entire knowledge graph system"
        center_node.axis_number = 0
        center_node.data = {
            "importance": 1.0,
            "integration_level": "system"
        }
        
        # Sample nodes for different axes
        nodes = []
        
        # Node 1
        node1 = KnowledgeGraphNode()
        node1.node_id = "kg-axis1-pl"
        node1.node_type = "axis"
        node1.label = "Pillar Levels"
        node1.description = "Knowledge organization by depth and complexity (Axis 1)"
        node1.axis_number = 1
        node1.data = {
            "importance": 0.9,
            "levels": 48,
            "integration_level": "primary"
        }
        nodes.append(node1)
        
        # Node 2
        node2 = KnowledgeGraphNode()
        node2.node_id = "kg-axis2-sectors"
        node2.node_type = "axis"
        node2.label = "Sectors"
        node2.description = "Industry and domain categorization (Axis 2)"
        node2.axis_number = 2
        node2.data = {
            "importance": 0.85,
            "sectors": 25,
            "integration_level": "primary"
        }
        nodes.append(node2)
        
        # Node 3
        node3 = KnowledgeGraphNode()
        node3.node_id = "kg-axis8-roles"
        node3.node_type = "axis"
        node3.label = "Professional Roles"
        node3.description = "Role-based perspective and expertise (Axis 8)"
        node3.axis_number = 8
        node3.data = {
            "importance": 0.75,
            "roles": 36,
            "integration_level": "primary"
        }
        nodes.append(node3)
        
        # Add all nodes to session
        db.session.add(center_node)
        db.session.add_all(nodes)
        db.session.commit()
        
        # Now create edges between nodes
        logger.info("Creating sample knowledge graph edges")
        edges = []
        
        # Connect central node to all axis nodes
        for node in nodes:
            edge = KnowledgeGraphEdge()
            edge.edge_id = f"edge-central-{node.node_id}"
            edge.source_id = center_node.id
            edge.target_id = node.id
            edge.edge_type = "hierarchy"
            edge.weight = 1.0
            edge.data = {
                "relationship": "parent-child",
                "bidirectional": True
            }
            edges.append(edge)
        
        # Add some edges between axis nodes
        edge1 = KnowledgeGraphEdge()
        edge1.edge_id = f"edge-axis1-axis2"
        edge1.source_id = nodes[0].id
        edge1.target_id = nodes[1].id
        edge1.edge_type = "association"
        edge1.weight = 0.7
        edge1.data = {
            "relationship": "cross-reference",
            "bidirectional": True
        }
        edges.append(edge1)
        
        edge2 = KnowledgeGraphEdge()
        edge2.edge_id = f"edge-axis2-axis8"
        edge2.source_id = nodes[1].id
        edge2.target_id = nodes[2].id
        edge2.edge_type = "association"
        edge2.weight = 0.8
        edge2.data = {
            "relationship": "cross-reference",
            "bidirectional": True
        }
        edges.append(edge2)
        
        db.session.add_all(edges)
        db.session.commit()
        
        logger.info(f"Created {len(nodes)} nodes and {len(edges)} edges")
    else:
        logger.info("Sample knowledge graph data already exists")

def init_database():
    """Initialize the database with sample data"""
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        logger.info("Database tables created")
        
        # Create users
        create_admin_user()
        create_demo_user()
        
        # Create sample data
        create_sample_simulations()
        create_sample_graph_nodes()
        
        logger.info("Database initialization completed")

if __name__ == "__main__":
    init_database()