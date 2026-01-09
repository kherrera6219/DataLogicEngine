from flask import Blueprint
from .auth_routes import auth_bp
# from .page_routes import page_bp
from .api_routes import api_bp
from .admin_routes import admin_bp
from .knowledge_routes import knowledge_bp
from .knowledge_routes import knowledge_bp
from .simulation_routes import simulation_bp
from .ka_routes import ka_bp
from .mcp_routes import mcp_bp

def register_routes(app):
    """Register all application blueprints."""
    
    # Page Routes (Legacy/Dead Code - Removed)
    # app.register_blueprint(page_bp)
    
    # Auth Routes (JSON API)
    # Note: url_prefix is defined in the blueprint itself as /api/v1/auth
    app.register_blueprint(auth_bp)
    
    # API Routes (Generic /api/v1)
    app.register_blueprint(api_bp)
    
    # Admin Routes (JSON API)
    # Note: url_prefix is defined in the blueprint itself as /api/v1/admin
    app.register_blueprint(admin_bp)
    
    # Knowledge Routes (Core Entities)
    app.register_blueprint(knowledge_bp)
    
    # Simulation Routes (JSON API)
    app.register_blueprint(simulation_bp)
    
    # Knowledge Algorithm Routes (JSON API)
    app.register_blueprint(ka_bp, url_prefix='/api/v1/ka')
    
    # MCP (Multi-Agent Coordination) Routes (JSON API)
    app.register_blueprint(mcp_bp, url_prefix='/api/v1/mcp')

