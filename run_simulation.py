"""
UKG Simulation Runner

This script runs a standalone Flask server for the Universal Knowledge Graph
simulation system, focusing on the in-memory nested layered simulation for layers 1-3.
"""

import os
import sys
import logging
import json
import pickle
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "ukg_simulation_key"

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import the simulation engine
from core.simulation.memory_simulation import create_sample_simulation

# Routes

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html', title='Universal Knowledge Graph')

@app.route('/simulation')
def simulation_page():
    """Render the simulation page."""
    return render_template('simulation.html', title='UKG Simulation Engine')

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start a new simulation."""
    try:
        # Create simulation engine with sample data
        engine = create_sample_simulation()
        
        # Start simulation
        result = engine.start_simulation()
        
        # Store engine in session
        session['engine'] = pickle.dumps(engine)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error starting simulation: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/simulation/step', methods=['POST'])
def run_simulation_step():
    """Run a simulation step."""
    try:
        engine_pickle = session.get('engine')
        if not engine_pickle:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Unpickle the engine
        engine = pickle.loads(engine_pickle)
        
        # Run simulation step
        result = engine.run_simulation_step()
        
        # Store updated engine in session
        session['engine'] = pickle.dumps(engine)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running simulation step: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error running simulation step: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """Stop the current simulation."""
    try:
        engine_pickle = session.get('engine')
        if not engine_pickle:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Unpickle the engine
        engine = pickle.loads(engine_pickle)
        
        # Stop simulation
        result = engine.stop_simulation()
        
        # Store updated engine in session
        session['engine'] = pickle.dumps(engine)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping simulation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error stopping simulation: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/simulation/results', methods=['GET'])
def get_simulation_results():
    """Get simulation results."""
    try:
        engine_pickle = session.get('engine')
        if not engine_pickle:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Unpickle the engine
        engine = pickle.loads(engine_pickle)
        
        # Get simulation results
        result = engine.get_simulation_results()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting simulation results: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting simulation results: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/simulation/graph', methods=['GET'])
def get_simulation_graph():
    """Get simulation graph."""
    try:
        engine_pickle = session.get('engine')
        if not engine_pickle:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Unpickle the engine
        engine = pickle.loads(engine_pickle)
        
        # Get export format
        format = request.args.get('format', 'json')
        
        # Export graph
        result = engine.export_graph(format)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error exporting simulation graph: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error exporting simulation graph: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

# Sample data endpoints for testing

@app.route('/api/pillars', methods=['GET'])
def get_pillars():
    """Get sample pillar levels data."""
    pillar_levels = [
        {
            "pillar_id": "PL01",
            "name": "U.S. Government Regulatory Systems",
            "description": "Core government regulatory frameworks and legal systems",
            "sublevels": {
                "1": "Federal Regulations",
                "2": "State Regulations",
                "3": "Local Government Codes"
            }
        },
        {
            "pillar_id": "PL04",
            "name": "Contracting & Procurement Sciences",
            "description": "Government and private sector acquisition methodologies",
            "sublevels": {
                "1": "Contract Types",
                "2": "Procurement Procedures"
            }
        },
        {
            "pillar_id": "PL07",
            "name": "Data Privacy & Security",
            "description": "Information security, privacy frameworks, and protection methods",
            "sublevels": {
                "1": "Data Protection Frameworks",
                "2": "Information Security"
            }
        },
        {
            "pillar_id": "PL12",
            "name": "Artificial Intelligence Systems",
            "description": "Machine learning models, neural networks, and AI applications",
            "sublevels": {
                "1": "Machine Learning",
                "2": "Neural Networks",
                "3": "Natural Language Processing"
            }
        },
        {
            "pillar_id": "PL21",
            "name": "Legal Frameworks",
            "description": "Legal systems, frameworks, and judicial processes",
            "sublevels": {
                "1": "Constitutional Law",
                "2": "Civil Law",
                "3": "Criminal Law"
            }
        }
    ]
    
    return jsonify({
        'status': 'success',
        'count': len(pillar_levels),
        'data': pillar_levels,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/sectors', methods=['GET'])
def get_sectors():
    """Get sample sectors data."""
    sectors = [
        {
            "sector_code": "GOV",
            "name": "Government",
            "description": "Public sector, government agencies, and regulatory bodies"
        },
        {
            "sector_code": "TECH",
            "name": "Technology",
            "description": "Information technology, software, hardware, and digital services"
        },
        {
            "sector_code": "FIN",
            "name": "Finance",
            "description": "Financial services, banking, and investment"
        },
        {
            "sector_code": "HEALTH",
            "name": "Healthcare",
            "description": "Medical services, healthcare systems, and pharmaceutical research"
        },
        {
            "sector_code": "EDU",
            "name": "Education",
            "description": "Educational institutions, learning systems, and research"
        }
    ]
    
    return jsonify({
        'status': 'success',
        'count': len(sectors),
        'data': sectors,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Get sample domains data."""
    domains = [
        {
            "domain_code": "FEDGOV",
            "name": "Federal Government",
            "description": "U.S. Federal Government operations and processes",
            "sector_code": "GOV"
        },
        {
            "domain_code": "CSEC",
            "name": "Cybersecurity",
            "description": "Computer and network security, defense against cyber threats",
            "sector_code": "TECH"
        },
        {
            "domain_code": "FINTECH",
            "name": "Financial Technology",
            "description": "Technology applications in finance and banking",
            "sector_code": "FIN"
        },
        {
            "domain_code": "AIML",
            "name": "AI & Machine Learning",
            "description": "Artificial intelligence and machine learning technologies",
            "sector_code": "TECH"
        },
        {
            "domain_code": "MEDRES",
            "name": "Medical Research",
            "description": "Scientific research in medicine and healthcare",
            "sector_code": "HEALTH"
        },
        {
            "domain_code": "HIGHERED",
            "name": "Higher Education",
            "description": "College and university systems and operations",
            "sector_code": "EDU"
        }
    ]
    
    return jsonify({
        'status': 'success',
        'count': len(domains),
        'data': domains,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    # Run the Flask app on port 8080 to avoid conflicts
    app.run(host='0.0.0.0', port=8080, debug=True)