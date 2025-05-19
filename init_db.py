"""
Universal Knowledge Graph (UKG) System - Database Initialization Script

This script initializes the database with required tables and sample data.
"""

import os
import logging
from datetime import datetime
import uuid

from app import app, db
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
        admin.set_password('admin123')  # For development only, would use a strong password in production
        
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
        demo.is_active = True
        demo.is_admin = False
        demo.created_at = datetime.utcnow()
        demo.set_password('demo123')  # For development only
        
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
        completed_sim = SimulationSession(
            session_id=str(uuid.uuid4()),
            user_id=demo.id,
            name="Knowledge Integration Simulation",
            description="Multi-perspective knowledge integration across domains with quantum-enhanced reasoning",
            parameters={
                "simulation_type": "quantum",
                "refinement_steps": 12,
                "confidence_threshold": 0.85,
                "entropy_sampling": True
            },
            status="completed",
            current_step=8,
            total_steps=8,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            results={
                "confidence_score": 0.92,
                "coherence_score": 0.88,
                "entropy_reduction": 0.76,
                "summary": "Successfully integrated knowledge from 4 perspectives with balanced insights"
            }
        )
        
        # Running simulation
        running_sim = SimulationSession(
            session_id=str(uuid.uuid4()),
            user_id=demo.id,
            name="Recursive AGI Simulation",
            description="Self-improvement and reasoning optimization using recursive AGI architecture",
            parameters={
                "simulation_type": "recursive",
                "refinement_steps": 16,
                "confidence_threshold": 0.90,
                "entropy_sampling": True
            },
            status="running",
            current_step=5,
            total_steps=8,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow()
        )
        
        # Pending simulation
        pending_sim = SimulationSession(
            session_id=str(uuid.uuid4()),
            user_id=demo.id,
            name="Quad Persona Analysis",
            description="Multi-perspective expert simulation for comprehensive domain analysis",
            parameters={
                "simulation_type": "quad",
                "refinement_steps": 8,
                "confidence_threshold": 0.80,
                "entropy_sampling": False
            },
            status="pending",
            current_step=0,
            total_steps=8,
            created_at=datetime.utcnow()
        )
        
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
        center_node = KnowledgeGraphNode(
            node_id="kg-central",
            node_type="central",
            label="Universal Knowledge Graph",
            description="Central node representing the entire knowledge graph system",
            axis_number=0,
            data={
                "importance": 1.0,
                "integration_level": "system"
            }
        )
        
        # Sample nodes for different axes
        nodes = [
            KnowledgeGraphNode(
                node_id="kg-axis1-pl",
                node_type="axis",
                label="Pillar Levels",
                description="Knowledge organization by depth and complexity (Axis 1)",
                axis_number=1,
                data={
                    "importance": 0.9,
                    "levels": 48,
                    "integration_level": "primary"
                }
            ),
            KnowledgeGraphNode(
                node_id="kg-axis2-sectors",
                node_type="axis",
                label="Sectors",
                description="Industry and domain categorization (Axis 2)",
                axis_number=2,
                data={
                    "importance": 0.85,
                    "sectors": 25,
                    "integration_level": "primary"
                }
            ),
            KnowledgeGraphNode(
                node_id="kg-axis8-roles",
                node_type="axis",
                label="Professional Roles",
                description="Role-based perspective and expertise (Axis 8)",
                axis_number=8,
                data={
                    "importance": 0.75,
                    "roles": 36,
                    "integration_level": "primary"
                }
            )
        ]
        
        # Add all nodes to session
        db.session.add(center_node)
        db.session.add_all(nodes)
        db.session.commit()
        
        # Now create edges between nodes
        logger.info("Creating sample knowledge graph edges")
        edges = []
        
        # Connect central node to all axis nodes
        for node in nodes:
            edge = KnowledgeGraphEdge(
                edge_id=f"edge-central-{node.node_id}",
                source_id=center_node.id,
                target_id=node.id,
                edge_type="hierarchy",
                weight=1.0,
                data={
                    "relationship": "parent-child",
                    "bidirectional": True
                }
            )
            edges.append(edge)
        
        # Add some edges between axis nodes
        edges.append(
            KnowledgeGraphEdge(
                edge_id=f"edge-axis1-axis2",
                source_id=nodes[0].id,
                target_id=nodes[1].id,
                edge_type="association",
                weight=0.7,
                data={
                    "relationship": "cross-reference",
                    "bidirectional": True
                }
            )
        )
        
        edges.append(
            KnowledgeGraphEdge(
                edge_id=f"edge-axis2-axis8",
                source_id=nodes[1].id,
                target_id=nodes[2].id,
                edge_type="association",
                weight=0.8,
                data={
                    "relationship": "cross-reference",
                    "bidirectional": True
                }
            )
        )
        
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