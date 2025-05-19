import os
import logging
from flask import Flask, render_template, request, jsonify
from core.united_system_manager import UnitedSystemManager
from core.graph_manager import GraphManager
from core.structured_memory_manager import StructuredMemoryManager
from core.knowledge_algorithm.ka_loader import KALoader
from core.simulation.simulation_engine import SimulationEngine
from core.simulation.app_orchestrator import AppOrchestrator
from config import AppConfig
from models import db

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

# Load configuration
config = AppConfig()

# Initialize Core Components
united_system_manager = UnitedSystemManager(config=config.ukg_config)
graph_manager = GraphManager(config=config.ukg_config, united_system_manager=united_system_manager)
memory_manager = StructuredMemoryManager(config=config.memory_config)
ka_loader = KALoader(config=config.ka_config, 
                     graph_manager=graph_manager, 
                     memory_manager=memory_manager,
                     united_system_manager=united_system_manager)

# Initialize Simulation Components
simulation_engine = SimulationEngine(
    config=config.simulation_config,
    graph_manager=graph_manager,
    memory_manager=memory_manager,
    united_system_manager=united_system_manager,
    ka_loader=ka_loader
)

# Initialize App Orchestrator
app_orchestrator = AppOrchestrator(
    config=config.orchestration_config,
    graph_manager=graph_manager,
    memory_manager=memory_manager,
    united_system_manager=united_system_manager,
    simulation_engine=simulation_engine,
    ka_loader=ka_loader
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    data = request.json or {}
    query_text = data.get('query', '')
    target_confidence = float(data.get('target_confidence', 0.85))
    
    if not query_text:
        return jsonify({'error': 'Query text is required'}), 400
    
    try:
        # Process the query through the orchestrator
        result = app_orchestrator.process_request(
            query_text=query_text,
            target_confidence=target_confidence
        )
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error processing query: {str(e)}'}), 500

@app.route('/api/graph_stats', methods=['GET'])
def get_graph_stats():
    stats = graph_manager.get_graph_statistics()
    return jsonify(stats)

@app.route('/api/memory_stats', methods=['GET'])
def get_memory_stats():
    stats = memory_manager.get_statistics()
    return jsonify(stats)

# Initialize the UKG on startup
with app.app_context():
    try:
        # Create database tables
        db.create_all()
        logging.info("Database tables created successfully")
        
        # Initialize the graph
        graph_manager.initialize_graph()
        logging.info("UKG initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize: {str(e)}", exc_info=True)
