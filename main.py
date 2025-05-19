"""Modified code based on user instructions and provided snippets, including Axis 6 regulatory registration and Axis 11 contextual expert persona."""
import os
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import yaml
from logging.config import dictConfig

# Configure logging
from utils.logging_config import get_logging_config
dictConfig(get_logging_config())
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
app.config.from_pyfile('config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Import models (after db initialization to avoid circular imports)
import db_models 

# Initialize database tables
@app.before_first_request
def initialize_database():
    """Initialize database tables if they don't exist."""
    try:
        db.create_all()
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# Load UKG system components
from core.united_system_manager import UnitedSystemManager
from core.graph_manager import GraphManager
from core.structured_memory_manager import StructuredMemoryManager
from core.axes.axis_system import AxisSystem
from core.simulation.app_orchestrator import AppOrchestrator
from core.axes.axis1_identity import PillarLevelManager
from core.axes.axis2_sector import SectorManager
from core.axes.axis4_methods import MethodsManager
from core.axes.axis5_honeycomb import HoneycombSystem
from core.axes.axis_system import AxisSystem

# Initialize system components
usm = UnitedSystemManager()
graph_manager = GraphManager(app.config, usm)
memory_manager = StructuredMemoryManager(app.config)
axis_system = AxisSystem()
app_orchestrator = AppOrchestrator(
    graph_manager=graph_manager,
    memory_manager=memory_manager,
    axis_system=axis_system,
    usm=usm
)

# Import API routes
from backend.api import init_api
from backend.chat_api import init_chat_api
from backend.pillar_api import pillar_api
from backend.methods_api import methods_api
from backend.honeycomb_api import honeycomb_api
from backend.regulatory_api import regulatory_api
from backend.api import api
from backend.contextual_api import contextual_api

# Import compliance API
from backend.compliance_api import compliance_api

# Import location API
from backend.location_api import location_api

# Initialize API routes
init_api(app, graph_manager, memory_manager, usm, app_orchestrator)
init_chat_api(app, axis_system)

# Register compliance API
app.register_blueprint(compliance_api)

# Routes
@app.route('/')
def index():
    """Render the landing page."""
    return render_template('index.html')

@app.route('/simulation')
def simulation():
    """Render the simulation page."""
    return render_template('simulation.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "online",
        "system": "UKG System Ready",
        "version": "1.0.0",
        "axes_available": len(axis_system.get_all_axes())
    })

# Register API routes
from backend.ukg_api import register_api as register_ukg_api
from backend.pillar_api import register_api as register_pillar_api
register_ukg_api(app)
register_pillar_api(app)

# Initialize Knowledge Manager
knowledge_manager = KnowledgeManager(db_manager=None, graph_manager=graph_manager, config=app.config)
app.config['KNOWLEDGE_MANAGER'] = knowledge_manager

# Register Axis managers
pillar_manager = PillarLevelManager(db_manager=db, graph_manager=graph_manager)
sector_manager = SectorManager(db_manager=db, graph_manager=graph_manager)
methods_manager = MethodsManager(db_manager=db, graph_manager=graph_manager)

axis_system.register_axis_manager(1, pillar_manager)
axis_system.register_axis_manager(2, sector_manager)
axis_system.register_axis_manager(4, methods_manager)
axis_system.register_axis_manager(5, HoneycombSystem(db_manager=db, graph_manager=graph_manager))

# Register API blueprint
app.register_blueprint(api)
app.register_blueprint(pillar_api)
app.register_blueprint(methods_api)
app.register_blueprint(honeycomb_api)
app.register_blueprint(regulatory_api)
app.register_blueprint(location_api)
app.register_blueprint(contextual_api)

# Run the application if executed directly
if __name__ == '__main__':
    logger.info("Starting UKG System...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)