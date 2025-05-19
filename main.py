"""
Universal Knowledge Graph (UKG) System

This is the main application file for the UKG system.
It initializes the Flask application, database, and routes.
"""

import os
import logging
import json
import pickle
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ukg_development_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
import uuid
import json

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from app import app, db
import models

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize database tables
@app.before_request
def initialize_database():
    """Initialize database tables and seed initial data."""
    logger.info("Initializing database tables...")
    db.create_all()
    
    # Check if we need to seed initial data
    if models.PillarLevel.query.count() == 0:
        logger.info("Seeding initial data for Pillar Levels...")
        seed_pillar_levels()
    
    if models.Sector.query.count() == 0:
        logger.info("Seeding initial data for Sectors...")
        seed_sectors()
    
    if models.Domain.query.count() == 0:
        logger.info("Seeding initial data for Domains...")
        seed_domains()
    
    if models.Location.query.count() == 0:
        logger.info("Seeding initial data for Locations...")
        seed_locations()
    
    logger.info("Database initialization complete.")

# Home route
@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html', title='Universal Knowledge Graph')

# Simulation Routes

@app.route('/simulation')
def simulation_page():
    """Render the simulation page."""
    return render_template('simulation.html', title='UKG Simulation Engine')

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start a new simulation."""
    try:
        from core.simulation.memory_simulation import create_sample_simulation
        
        # Create simulation engine with sample data
        engine = create_sample_simulation()
        
        # Start simulation
        result = engine.start_simulation()
        
        # Store engine in session
        session['engine'] = engine
        
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
        engine = session.get('engine')
        if not engine:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Run simulation step
        result = engine.run_simulation_step()
        
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
        engine = session.get('engine')
        if not engine:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Stop simulation
        result = engine.stop_simulation()
        
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
        engine = session.get('engine')
        if not engine:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
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
        engine = session.get('engine')
        if not engine:
            return jsonify({
                'status': 'error',
                'message': 'No active simulation found',
                'timestamp': datetime.now().isoformat()
            }), 400
        
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

# API Routes

@app.route('/api/pillars', methods=['GET'])
def get_pillars():
    """Get all pillar levels."""
    pillars = models.PillarLevel.query.all()
    return jsonify({
        'status': 'success',
        'pillars': [pillar.to_dict() for pillar in pillars]
    })

@app.route('/api/pillars/<pillar_id>', methods=['GET'])
def get_pillar(pillar_id):
    """Get a specific pillar level."""
    pillar = models.PillarLevel.query.filter_by(pillar_id=pillar_id).first()
    if not pillar:
        return jsonify({
            'status': 'error',
            'message': f'Pillar Level {pillar_id} not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'pillar': pillar.to_dict()
    })

@app.route('/api/sectors', methods=['GET'])
def get_sectors():
    """Get all sectors."""
    sectors = models.Sector.query.all()
    return jsonify({
        'status': 'success',
        'sectors': [sector.to_dict() for sector in sectors]
    })

@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Get all domains."""
    domains = models.Domain.query.all()
    return jsonify({
        'status': 'success',
        'domains': [domain.to_dict() for domain in domains]
    })

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all knowledge nodes."""
    nodes = models.KnowledgeNode.query.all()
    return jsonify({
        'status': 'success',
        'nodes': [node.to_dict() for node in nodes]
    })

# Data seeding functions

def seed_pillar_levels():
    """Seed initial pillar level data."""
    pillar_levels = [
        {
            "pillar_id": "PL01",
            "name": "U.S. Government Regulatory Systems",
            "description": "Core government regulatory frameworks and legal systems",
            "sublevels": {
                "1": "Federal Regulations",
                "2": "State Regulations",
                "3": "Local Government Codes",
                "4": "Regulatory Authorities"
            }
        },
        {
            "pillar_id": "PL02",
            "name": "Physical Sciences",
            "description": "Core physical science disciplines and applied research",
            "sublevels": {
                "1": "Physics",
                "1.1": "Astrophysics",
                "1.1.1": "Space Propulsion",
                "2": "Chemistry", 
                "3": "Earth Sciences",
                "4": "Materials Science"
            }
        },
        {
            "pillar_id": "PL04",
            "name": "Contracting & Procurement Sciences",
            "description": "Government and private sector acquisition methodologies",
            "sublevels": {
                "1": "Contract Types",
                "2": "Procurement Procedures",
                "3": "Source Selection",
                "4": "Contract Administration"
            }
        },
        {
            "pillar_id": "PL05",
            "name": "Healthcare Sciences",
            "description": "Medical disciplines, healthcare administration, and clinical practices",
            "sublevels": {
                "1": "Clinical Medicine",
                "2": "Healthcare Administration",
                "3": "Public Health",
                "4": "Medical Research"
            }
        },
        {
            "pillar_id": "PL07",
            "name": "Data Privacy & Security",
            "description": "Information security, privacy frameworks, and protection methods",
            "sublevels": {
                "1": "Data Protection Frameworks",
                "2": "Information Security",
                "3": "Privacy Engineering",
                "4": "Compliance Management"
            }
        },
        {
            "pillar_id": "PL20",
            "name": "Legal Frameworks",
            "description": "Legal disciplines, practices, and specializations",
            "sublevels": {
                "1": "Constitutional Law",
                "2": "Administrative Law",
                "3": "Contract Law",
                "3.2": "Government Contracting",
                "3.2.1": "FAR-Based Contracting",
                "4": "Criminal Law"
            }
        },
        {
            "pillar_id": "PL48",
            "name": "Public Policy and Federal Governance",
            "description": "Government policy development and implementation methods",
            "sublevels": {
                "1": "Policy Analysis",
                "2": "Federal Budget Process",
                "3": "Agency Rulemaking",
                "4": "Legislative Process"
            }
        },
        {
            "pillar_id": "PL87",
            "name": "Cybersecurity Law",
            "description": "Legal frameworks governing digital security and cyber operations",
            "sublevels": {
                "1": "Data Breach Notification Laws",
                "2": "Critical Infrastructure Protection",
                "3": "International Cyber Law",
                "4": "Digital Privacy Laws"
            }
        }
    ]
    
    for pillar_data in pillar_levels:
        pillar = models.PillarLevel(
            uid=f"pillar_level_{pillar_data['pillar_id']}_{uuid.uuid4().hex[:8]}",
            pillar_id=pillar_data['pillar_id'],
            name=pillar_data['name'],
            description=pillar_data['description'],
            sublevels=pillar_data['sublevels']
        )
        db.session.add(pillar)
    
    db.session.commit()
    logger.info(f"Added {len(pillar_levels)} pillar levels to database.")

def seed_sectors():
    """Seed initial sector data."""
    sectors = [
        {
            "sector_code": "GOV",
            "name": "Government",
            "description": "Public sector, government agencies, and regulatory bodies"
        },
        {
            "sector_code": "TECH",
            "name": "Technology",
            "description": "Information technology, software, hardware, and digital services",
            "parent_sector_id": None
        },
        {
            "sector_code": "TECH-SW",
            "name": "Software Development",
            "description": "Software engineering, development, and applications",
            "parent_sector_name": "Technology"
        },
        {
            "sector_code": "TECH-HW",
            "name": "Hardware Manufacturing",
            "description": "Computer and technology hardware manufacturing",
            "parent_sector_name": "Technology"
        },
        {
            "sector_code": "HC",
            "name": "Healthcare",
            "description": "Healthcare providers, services, and medical industry",
            "parent_sector_id": None
        },
        {
            "sector_code": "HC-PROV",
            "name": "Healthcare Providers",
            "description": "Hospitals, clinics, and healthcare service providers",
            "parent_sector_name": "Healthcare"
        },
        {
            "sector_code": "FIN",
            "name": "Finance",
            "description": "Financial services, banking, and investment",
            "parent_sector_id": None
        },
        {
            "sector_code": "DEF",
            "name": "Defense",
            "description": "Defense industry, contractors, and military organizations",
            "parent_sector_id": None
        }
    ]
    
    # First pass: add top-level sectors
    for sector_data in sectors:
        if not sector_data.get('parent_sector_name'):
            sector = models.Sector(
                uid=f"sector_{sector_data['sector_code']}_{uuid.uuid4().hex[:8]}",
                sector_code=sector_data['sector_code'],
                name=sector_data['name'],
                description=sector_data['description']
            )
            db.session.add(sector)
    
    db.session.commit()
    
    # Second pass: add sub-sectors
    for sector_data in sectors:
        if sector_data.get('parent_sector_name'):
            parent_sector = models.Sector.query.filter_by(name=sector_data['parent_sector_name']).first()
            if parent_sector:
                sector = models.Sector(
                    uid=f"sector_{sector_data['sector_code']}_{uuid.uuid4().hex[:8]}",
                    sector_code=sector_data['sector_code'],
                    name=sector_data['name'],
                    description=sector_data['description'],
                    parent_sector_id=parent_sector.id
                )
                db.session.add(sector)
    
    db.session.commit()
    logger.info(f"Added {len(sectors)} sectors to database.")

def seed_domains():
    """Seed initial domain data."""
    domains = [
        {
            "domain_code": "CSEC",
            "name": "Cybersecurity",
            "description": "Computer and network security, defense against cyber threats",
            "sector_code": "TECH"
        },
        {
            "domain_code": "AI",
            "name": "Artificial Intelligence",
            "description": "Machine learning, neural networks, and AI systems",
            "sector_code": "TECH"
        },
        {
            "domain_code": "FEDGOV",
            "name": "Federal Government",
            "description": "U.S. Federal Government operations and processes",
            "sector_code": "GOV"
        },
        {
            "domain_code": "HCIT",
            "name": "Healthcare IT",
            "description": "Information technology systems for healthcare",
            "sector_code": "HC"
        },
        {
            "domain_code": "FINTECH",
            "name": "Financial Technology",
            "description": "Technology applications in finance and banking",
            "sector_code": "FIN"
        }
    ]
    
    for domain_data in domains:
        sector = models.Sector.query.filter_by(sector_code=domain_data['sector_code']).first()
        if sector:
            domain = models.Domain(
                uid=f"domain_{domain_data['domain_code']}_{uuid.uuid4().hex[:8]}",
                domain_code=domain_data['domain_code'],
                name=domain_data['name'],
                description=domain_data['description'],
                sector_id=sector.id
            )
            db.session.add(domain)
    
    db.session.commit()
    logger.info(f"Added {len(domains)} domains to database.")

def seed_locations():
    """Seed initial location data."""
    locations = [
        {
            "location_code": "US",
            "name": "United States",
            "description": "United States of America",
            "location_type": "country",
            "country": "United States"
        },
        {
            "location_code": "EU",
            "name": "European Union",
            "description": "European Union member states",
            "location_type": "region",
            "region": "Europe"
        },
        {
            "location_code": "APAC",
            "name": "Asia-Pacific",
            "description": "Asia-Pacific region",
            "location_type": "region",
            "region": "Asia-Pacific"
        },
        {
            "location_code": "DC",
            "name": "Washington DC",
            "description": "Washington, District of Columbia",
            "location_type": "city",
            "country": "United States",
            "city": "Washington DC",
            "latitude": 38.9072,
            "longitude": -77.0369
        }
    ]
    
    for location_data in locations:
        location = models.Location(
            uid=f"location_{location_data['location_code']}_{uuid.uuid4().hex[:8]}",
            location_code=location_data['location_code'],
            name=location_data['name'],
            description=location_data['description'],
            location_type=location_data['location_type'],
            country=location_data.get('country'),
            region=location_data.get('region'),
            city=location_data.get('city'),
            latitude=location_data.get('latitude'),
            longitude=location_data.get('longitude')
        )
        db.session.add(location)
    
    db.session.commit()
    logger.info(f"Added {len(locations)} locations to database.")

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)