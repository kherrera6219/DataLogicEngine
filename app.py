"""
Universal Knowledge Graph (UKG) System - Main Application

This is the main application file for the UKG system,
handling database setup and application initialization.
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
# setup a secret key, required by sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ukg_development_key")
# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In-memory simulation classes (simplified version)
class SimulationNode:
    """Node in the simulation graph."""
    def __init__(self, node_id, name, node_type, axis, data=None):
        self.id = node_id
        self.name = name
        self.type = node_type
        self.axis = axis
        self.data = data or {}
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'axis': self.axis,
            'data': self.data
        }

class SimulationEdge:
    """Edge in the simulation graph."""
    def __init__(self, source_id, target_id, edge_type, weight=1.0, data=None):
        self.source = source_id
        self.target = target_id
        self.type = edge_type
        self.weight = weight
        self.data = data or {}
        
    def to_dict(self):
        return {
            'source': self.source,
            'target': self.target,
            'type': self.type,
            'weight': self.weight,
            'data': self.data
        }

class MemorySimulation:
    """Simplified in-memory simulation for UKG layers 1-3."""
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.pillar_levels = {}
        self.sectors = {}
        self.domains = {}
        self.active = False
        self.step_count = 0
        self.simulation_id = None
        self.results = []
    
    def load_sample_data(self):
        """Load sample data for the simulation."""
        # Add pillar levels (Axis 1: Knowledge)
        self._add_node("PL01", "U.S. Government Regulatory Systems", "pillar_level", 1, {
            "description": "Core government regulatory frameworks and legal systems",
            "sublevels": {
                "1": "Federal Regulations",
                "2": "State Regulations",
                "3": "Local Government Codes"
            }
        })
        self._add_node("PL04", "Contracting & Procurement Sciences", "pillar_level", 1, {
            "description": "Government and private sector acquisition methodologies",
            "sublevels": {
                "1": "Contract Types",
                "2": "Procurement Procedures"
            }
        })
        self._add_node("PL07", "Data Privacy & Security", "pillar_level", 1, {
            "description": "Information security, privacy frameworks, and protection methods",
            "sublevels": {
                "1": "Data Protection Frameworks",
                "2": "Information Security"
            }
        })
        
        # Add sectors (Axis 2: Sectors)
        self._add_node("GOV", "Government", "sector", 2, {
            "description": "Public sector, government agencies, and regulatory bodies"
        })
        self._add_node("TECH", "Technology", "sector", 2, {
            "description": "Information technology, software, hardware, and digital services"
        })
        self._add_node("FIN", "Finance", "sector", 2, {
            "description": "Financial services, banking, and investment"
        })
        
        # Add domains (Axis 3: Domains)
        self._add_node("FEDGOV", "Federal Government", "domain", 3, {
            "description": "U.S. Federal Government operations and processes",
            "sector_code": "GOV"
        })
        self._add_node("CSEC", "Cybersecurity", "domain", 3, {
            "description": "Computer and network security, defense against cyber threats",
            "sector_code": "TECH"
        })
        self._add_node("FINTECH", "Financial Technology", "domain", 3, {
            "description": "Technology applications in finance and banking",
            "sector_code": "FIN"
        })
        
        # Connect sectors to domains
        self._add_edge("GOV", "FEDGOV", "has_domain", 0.9)
        self._add_edge("TECH", "CSEC", "has_domain", 0.9)
        self._add_edge("FIN", "FINTECH", "has_domain", 0.9)
        
        # Connect pillars to sectors
        self._add_edge("PL01", "GOV", "pillar_to_sector", 0.9)
        self._add_edge("PL01", "FIN", "pillar_to_sector", 0.4)
        self._add_edge("PL04", "GOV", "pillar_to_sector", 0.8)
        self._add_edge("PL07", "TECH", "pillar_to_sector", 0.9)
        self._add_edge("PL07", "FIN", "pillar_to_sector", 0.6)
        
        # Connect domains to pillars (cross-connections)
        self._add_edge("FEDGOV", "PL01", "domain_to_pillar", 0.9)
        self._add_edge("CSEC", "PL07", "domain_to_pillar", 0.9)
        self._add_edge("FINTECH", "PL07", "domain_to_pillar", 0.7)
        self._add_edge("FINTECH", "PL01", "domain_to_pillar", 0.4)
    
    def _add_node(self, node_id, name, node_type, axis, data=None):
        """Add a node to the simulation."""
        node = SimulationNode(node_id, name, node_type, axis, data)
        self.nodes[node_id] = node
        
        # Categorize by type
        if node_type == "pillar_level":
            self.pillar_levels[node_id] = node
        elif node_type == "sector":
            self.sectors[node_id] = node
        elif node_type == "domain":
            self.domains[node_id] = node
    
    def _add_edge(self, source_id, target_id, edge_type, weight=1.0, data=None):
        """Add an edge to the simulation."""
        edge = SimulationEdge(source_id, target_id, edge_type, weight, data)
        self.edges.append(edge)
    
    def start_simulation(self):
        """Start a new simulation."""
        self.active = True
        self.step_count = 0
        import uuid
        self.simulation_id = f"sim-{uuid.uuid4().hex[:8]}"
        self.results = []
        
        # Return initial state
        return {
            "status": "success",
            "simulation_id": self.simulation_id,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "timestamp": datetime.now().isoformat()
        }
    
    def run_step(self):
        """Run a simulation step."""
        if not self.active:
            return {"status": "error", "message": "No active simulation."}
        
        self.step_count += 1
        
        # Layer 1: Knowledge diffusion
        pillar_activations = self._run_knowledge_diffusion()
        
        # Layer 2: Sector influence
        sector_activities = self._run_sector_influence(pillar_activations)
        
        # Layer 3: Domain specialization
        domain_activities = self._run_domain_specialization(sector_activities)
        
        # Store results
        step_result = {
            "step": self.step_count,
            "pillar_activations": pillar_activations,
            "sector_activities": sector_activities,
            "domain_activities": domain_activities,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(step_result)
        
        return {
            "status": "success",
            "simulation_id": self.simulation_id,
            "simulation_step": self.step_count,
            "results": step_result
        }
    
    def _run_knowledge_diffusion(self):
        """Run Layer 1: Knowledge diffusion."""
        pillar_activations = {}
        
        # Simple activation algorithm based on connectivity
        for pillar_id, pillar in self.pillar_levels.items():
            # Count connected edges
            connected_edges = [e for e in self.edges if e.source == pillar_id or e.target == pillar_id]
            
            # Calculate activation based on connectivity and step number
            base_activation = 0.1
            connection_factor = 0.05 * len(connected_edges)
            step_factor = 0.02 * self.step_count
            
            activation = min(0.95, base_activation + connection_factor + step_factor)
            pillar_activations[pillar_id] = activation
        
        return pillar_activations
    
    def _run_sector_influence(self, pillar_activations):
        """Run Layer 2: Sector influence."""
        sector_activities = {}
        
        for sector_id, sector in self.sectors.items():
            # Find all pillars connected to this sector
            connected_pillars = []
            for edge in self.edges:
                if edge.type == "pillar_to_sector" and edge.target == sector_id:
                    connected_pillars.append({
                        "pillar_id": edge.source,
                        "weight": edge.weight
                    })
            
            # Calculate sector influence based on connected pillar activations
            influence = 0.0
            knowledge_sources = []
            
            for conn in connected_pillars:
                pillar_id = conn["pillar_id"]
                weight = conn["weight"]
                
                if pillar_id in pillar_activations:
                    activation = pillar_activations[pillar_id]
                    contribution = activation * weight
                    influence += contribution
                    
                    # Record this knowledge source
                    knowledge_sources.append({
                        "pillar_id": pillar_id,
                        "name": self.nodes[pillar_id].name,
                        "activation": activation,
                        "weight": weight,
                        "contribution": contribution
                    })
            
            # Normalize influence
            if connected_pillars:
                influence /= len(connected_pillars)
            
            # Record sector activity
            sector_activities[sector_id] = {
                "sector_id": sector_id,
                "name": sector.name,
                "influence": influence,
                "knowledge_sources": knowledge_sources
            }
        
        return sector_activities
    
    def _run_domain_specialization(self, sector_activities):
        """Run Layer 3: Domain specialization."""
        domain_activities = {}
        
        for domain_id, domain in self.domains.items():
            # Get the sector this domain belongs to
            sector_id = domain.data.get("sector_code")
            
            # Find direct connections to pillars
            direct_pillar_connections = []
            for edge in self.edges:
                if edge.type == "domain_to_pillar" and edge.source == domain_id:
                    direct_pillar_connections.append({
                        "pillar_id": edge.target,
                        "weight": edge.weight
                    })
            
            # Calculate specialization based on sector influence and direct connections
            specialization = 0.0
            knowledge_adaptations = []
            
            # Factor 1: Sector influence (60%)
            if sector_id and sector_id in sector_activities:
                sector_influence = sector_activities[sector_id]["influence"]
                sector_contribution = sector_influence * 0.6
                specialization += sector_contribution
                
                knowledge_adaptations.append({
                    "type": "sector_influence",
                    "sector_id": sector_id,
                    "name": self.nodes[sector_id].name,
                    "influence": sector_influence,
                    "contribution": sector_contribution
                })
            
            # Factor 2: Direct pillar connections (40%)
            pillar_contribution = 0.0
            if direct_pillar_connections:
                for conn in direct_pillar_connections:
                    pillar_id = conn["pillar_id"]
                    weight = conn["weight"]
                    
                    individual_contribution = weight * 0.4 / len(direct_pillar_connections)
                    pillar_contribution += individual_contribution
                    
                    knowledge_adaptations.append({
                        "type": "direct_pillar_connection",
                        "pillar_id": pillar_id,
                        "name": self.nodes[pillar_id].name,
                        "weight": weight,
                        "contribution": individual_contribution
                    })
                
                specialization += pillar_contribution
            
            # Record domain activity
            domain_activities[domain_id] = {
                "domain_id": domain_id,
                "name": domain.name,
                "specialization": specialization,
                "knowledge_adaptations": knowledge_adaptations
            }
        
        return domain_activities
    
    def stop_simulation(self):
        """Stop the current simulation."""
        if not self.active:
            return {"status": "error", "message": "No active simulation."}
        
        self.active = False
        return {
            "status": "success",
            "simulation_id": self.simulation_id,
            "steps_completed": self.step_count,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_results(self):
        """Get the results of the current simulation."""
        if not self.simulation_id:
            return {"status": "error", "message": "No simulation has been run."}
        
        return {
            "status": "success",
            "simulation_id": self.simulation_id,
            "steps_completed": self.step_count,
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_graph(self):
        """Export the simulation graph as JSON."""
        nodes_json = []
        for node_id, node in self.nodes.items():
            nodes_json.append(node.to_dict())
        
        edges_json = [edge.to_dict() for edge in self.edges]
        
        return {
            "status": "success",
            "graph": {
                "nodes": nodes_json,
                "edges": edges_json,
                "metadata": {
                    "node_count": len(nodes_json),
                    "edge_count": len(edges_json),
                    "simulation_id": self.simulation_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }

# Initialize the simulation
simulation = MemorySimulation()
simulation.load_sample_data()

# Routes

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/simulation')
def simulation_page():
    """Render the simulation page."""
    return render_template('simulation.html')

# API Routes for Simulation

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start a new simulation."""
    try:
        result = simulation.start_simulation()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error starting simulation: {str(e)}"
        }), 500

@app.route('/api/simulation/step', methods=['POST'])
def run_simulation_step():
    """Run a simulation step."""
    try:
        result = simulation.run_step()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running simulation step: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error running simulation step: {str(e)}"
        }), 500

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """Stop the current simulation."""
    try:
        result = simulation.stop_simulation()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping simulation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error stopping simulation: {str(e)}"
        }), 500

@app.route('/api/simulation/results', methods=['GET'])
def get_simulation_results():
    """Get simulation results."""
    try:
        result = simulation.get_results()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting simulation results: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting simulation results: {str(e)}"
        }), 500

@app.route('/api/simulation/graph', methods=['GET'])
def get_simulation_graph():
    """Get simulation graph."""
    try:
        result = simulation.export_graph()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error exporting simulation graph: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error exporting simulation graph: {str(e)}"
        }), 500

# Sample data endpoints

@app.route('/api/pillars', methods=['GET'])
def get_pillars():
    """Get all pillar levels."""
    pillars = []
    for pillar_id, pillar in simulation.pillar_levels.items():
        pillars.append(pillar.to_dict())
    
    return jsonify({
        'status': 'success',
        'count': len(pillars),
        'data': pillars
    })

@app.route('/api/sectors', methods=['GET'])
def get_sectors():
    """Get all sectors."""
    sectors = []
    for sector_id, sector in simulation.sectors.items():
        sectors.append(sector.to_dict())
    
    return jsonify({
        'status': 'success',
        'count': len(sectors),
        'data': sectors
    })

@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Get all domains."""
    domains = []
    for domain_id, domain in simulation.domains.items():
        domains.append(domain.to_dict())
    
    return jsonify({
        'status': 'success',
        'count': len(domains),
        'data': domains
    })

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=8080, debug=True)