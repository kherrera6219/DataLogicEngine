"""
Universal Knowledge Graph (UKG) Routes

This module defines the routes for the UKG application, handling requests and rendering templates.
"""

import os
import logging
import datetime
import json
import secrets
import uuid
from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, session, abort, send_from_directory
)
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import text, select

from app import app
from extensions import db
from models import APIKey, User, SimulationSession
from db_models import Node, Edge, KnowledgeNode, MethodNode, KnowledgeAlgorithm, Sector, Domain

# Configure logging
logger = logging.getLogger(__name__)

# Public Routes
@app.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        try:
            user = User()
            user.username = username
            user.email = email
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration', 'danger')
    
    return render_template('register.html')

# Authenticated Routes
@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard."""
    # Get some summary statistics
    stats = {
        'knowledge_count': KnowledgeNode.query.count(),
        'sector_count': Sector.query.count(),
        'domain_count': Domain.query.count(),
        'simulation_count': SimulationSession.query.filter_by(user_id=current_user.id).count(),
        'algorithm_count': KnowledgeAlgorithm.query.count()
    }
    
    # Get recent simulations for this user
    recent_simulations = SimulationSession.query.filter_by(
        user_id=current_user.id
    ).order_by(SimulationSession.started_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          stats=stats, 
                          recent_simulations=recent_simulations)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Render the user profile page and manage API keys."""
    new_api_key = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            label = request.form.get('label', 'New API Key').strip() or 'New API Key'
            new_api_key = APIKey(
                user_id=current_user.id,
                name=label,
                key=secrets.token_hex(32)
            )
            db.session.add(new_api_key)
            db.session.commit()
            session['generated_api_key'] = new_api_key.key
            session['generated_api_key_name'] = new_api_key.name
            flash('New API key created. Copy it now; it will only be shown once.', 'success')

        elif action == 'revoke':
            key_id = request.form.get('key_id', type=int)
            api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id, is_active=True).first()
            if api_key:
                api_key.is_active = False
                api_key.revoked_at = datetime.datetime.utcnow()
                db.session.commit()
                flash('API key revoked successfully.', 'info')
            else:
                flash('API key not found or already revoked.', 'warning')

        return redirect(url_for('profile'))

    new_api_key_value = session.pop('generated_api_key', None)
    new_api_key_name = session.pop('generated_api_key_name', None)
    api_keys = APIKey.query.filter_by(user_id=current_user.id).order_by(APIKey.created_at.desc()).all()

    simulation_count = SimulationSession.query.filter_by(user_id=current_user.id).count()
    completed_simulations = SimulationSession.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).count()

    return render_template(
        'profile.html',
        api_keys=api_keys,
        new_api_key=new_api_key_value,
        new_api_key_name=new_api_key_name,
        simulation_count=simulation_count,
        completed_simulations=completed_simulations,
    )

@app.route('/knowledge')
@login_required
def knowledge():
    """Render the knowledge page."""
    # Get knowledge nodes with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    knowledge_nodes = KnowledgeNode.query.order_by(
        KnowledgeNode.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template('knowledge.html', knowledge_nodes=knowledge_nodes)

@app.route('/simulation')
@login_required
def simulation():
    """Render the simulation page."""
    # Get past simulations with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    simulations = SimulationSession.query.filter_by(
        user_id=current_user.id
    ).order_by(SimulationSession.started_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('simulation.html', simulations=simulations)

@app.route('/graph')
@login_required
def graph():
    """Render the graph visualization page."""
    return render_template('graph.html')

@app.route('/chatbot')
@login_required
def chatbot():
    """Render the chatbot interface."""
    return render_template('chatbot.html')

@app.route('/analytics')
@login_required
def analytics():
    """Render the analytics page."""
    # Get some analytics data
    user_count = User.query.count()
    node_count = Node.query.count()
    edge_count = Edge.query.count()
    simulation_count = SimulationSession.query.count()
    
    # Get node distribution by axis
    node_distribution = []
    for i in range(1, 14):
        count = Node.query.filter_by(axis_number=i).count()
        node_distribution.append({
            'axis': i,
            'count': count,
            'label': ['Knowledge', 'Sectors', 'Domains', 'Methods', 'Contexts', 
                     'Problems', 'Solutions', 'Roles', 'Experts', 'Regulations', 
                     'Compliance', 'Location', 'Time'][i-1]
        })
    
    # Get simulation status counts
    simulation_statuses = {}
    status_rows = db.session.query(
        SimulationSession.status, 
        db.func.count(SimulationSession.id)
    ).group_by(SimulationSession.status).all()
    
    for status, count in status_rows:
        simulation_statuses[status] = count
    
    return render_template('analytics.html',
                          user_count=user_count,
                          node_count=node_count,
                          edge_count=edge_count,
                          simulation_count=simulation_count,
                          node_distribution=node_distribution,
                          simulation_statuses=simulation_statuses)

@app.route('/settings')
@login_required
def settings():
    """Render the settings page."""
    return render_template('settings.html')

# Admin Routes
@app.route('/admin')
@login_required
def admin():
    """Render the admin dashboard."""
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get some admin stats
    stats = {
        'user_count': User.query.count(),
        'active_users': User.query.filter_by(active=True).count(),
        'node_count': Node.query.count(),
        'edge_count': Edge.query.count(),
        'simulation_count': SimulationSession.query.count(),
        'algorithm_count': KnowledgeAlgorithm.query.count()
    }
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent simulations
    recent_simulations = SimulationSession.query.order_by(
        SimulationSession.started_at.desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          stats=stats,
                          recent_users=recent_users,
                          recent_simulations=recent_simulations)

# API Routes
@app.route('/api/health')
def api_health():
    """API health check endpoint."""
    try:
        # Check database connection
        db.session.execute(select(text('1')))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    return jsonify({
        "status": "ok" if db_status == "healthy" else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "database": db_status
        }
    })

@app.route('/api/graph')
@login_required
def api_graph():
    """API endpoint to get graph data for visualization."""
    try:
        # Get filter parameters
        axis = request.args.get('axis', type=int)
        node_type = request.args.get('nodeType')
        limit = request.args.get('limit', 100, type=int)
        
        # Build query for nodes
        node_query = Node.query
        
        if axis:
            node_query = node_query.filter_by(axis_number=axis)
        
        if node_type:
            node_query = node_query.filter_by(node_type=node_type)
        
        # Get nodes with limit
        nodes = node_query.limit(limit).all()
        
        # Prepare node data
        node_data = []
        node_ids = []
        
        for node in nodes:
            node_ids.append(node.id)
            node_data.append({
                "id": node.id,
                "label": node.label,
                "axis_number": node.axis_number,
                "node_type": node.node_type,
                "description": node.description,
                "size": 8,  # default size
                "value": 1  # default value for force layout
            })
        
        # Get edges between these nodes
        edges = Edge.query.filter(
            Edge.source_node_id.in_(node_ids),
            Edge.target_node_id.in_(node_ids)
        ).all()
        
        # Prepare edge data
        edge_data = []
        
        for edge in edges:
            edge_data.append({
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "label": edge.label,
                "value": edge.weight,
                "directed": True
            })
        
        # Assemble final data structure
        graph_data = {
            "nodes": node_data,
            "links": edge_data
        }
        
        return jsonify(graph_data)
    
    except Exception as e:
        logger.error(f"Error getting graph data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/query', methods=['POST'])
@login_required
def api_query():
    """API endpoint to process a knowledge query."""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400
        
        query = data['query']
        confidence_threshold = data.get('confidenceThreshold', 0.85)
        max_layer = data.get('maxLayer', 5)
        
        # In a real implementation, this would process the query through the UKG system
        # For now, we'll return a simulated response
        
        # Create a simulation record
        simulation = SimulationSession()
        simulation.session_id = str(uuid.uuid4())
        simulation.user_id = current_user.id
        simulation.parameters = {
            "query": query,
            "confidenceThreshold": confidence_threshold,
            "maxLayer": max_layer
        }
        simulation.status = "completed"
        simulation.current_step = 8
        simulation.total_steps = 8
        simulation.started_at = datetime.datetime.utcnow()
        simulation.completed_at = datetime.datetime.utcnow()
        
        # Generate a simulated response based on the query
        if "knowledge" in query.lower():
            response = f"The Universal Knowledge Graph organizes information across 13 axes, including knowledge domains, sectors, methods, and more. This allows for multi-perspective analysis of complex topics."
            confidence = 0.92
            active_layer = 2
        elif "simulation" in query.lower():
            response = f"Simulations in the UKG system use a 10-layer architecture with recursive processing to generate insights based on integrated knowledge across multiple domains."
            confidence = 0.89
            active_layer = 3
        elif "persona" in query.lower() or "expert" in query.lower():
            response = f"The Quad Persona Engine creates synthetic experts through 7 component structures (job role, education, certifications, skills, training, career path, related jobs). This allows the system to provide multi-perspective expertise on complex topics."
            confidence = 0.94
            active_layer = 4
        else:
            response = f"I understand your query about '{query}'. The Universal Knowledge Graph integrates multiple perspectives on this topic across knowledge domains, sectors, regulatory frameworks, and compliance requirements."
            confidence = 0.85
            active_layer = 1
        
        # Store the response in the simulation
        simulation.results = {
            "response": response,
            "confidenceScore": confidence,
            "activeLayer": active_layer
        }
        
        db.session.add(simulation)
        db.session.commit()
        
        # Return the response
        return jsonify({
            "query": query,
            "response": response,
            "confidenceScore": confidence,
            "activeLayer": active_layer,
            "simulationId": simulation.session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulation/run', methods=['POST'])
@login_required
def api_run_simulation():
    """API endpoint to run a simulation."""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400
        
        query = data['query']
        confidence_threshold = data.get('confidenceThreshold', 0.85)
        max_layer = data.get('maxLayer', 5)
        refinement_steps = data.get('refinementSteps', 8)
        
        # Create a simulation record
        simulation = SimulationSession()
        simulation.session_id = str(uuid.uuid4())
        simulation.name = data.get('name', f"Simulation {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
        simulation.user_id = current_user.id
        simulation.parameters = {
            "query": query,
            "confidenceThreshold": confidence_threshold,
            "maxLayer": max_layer,
            "refinementSteps": refinement_steps
        }
        simulation.status = "running"
        simulation.current_step = 0
        simulation.total_steps = refinement_steps
        simulation.started_at = datetime.datetime.utcnow()
        
        db.session.add(simulation)
        db.session.commit()
        
        # In a real implementation, this would start an asynchronous simulation
        # For now, we'll return a simulated response
        
        # Return the simulation ID and initial status
        return jsonify({
            "simulationId": simulation.session_id,
            "status": "running",
            "message": "Simulation started successfully"
        })
    
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return render_template('errors/500.html'), 500