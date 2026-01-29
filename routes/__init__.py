from flask import Blueprint
from .auth_routes import auth_bp
from flask import Blueprint
from .auth_routes import auth_bp
# from .page_routes import page_bp
from .api_routes import api_bp
from .admin_routes import admin_bp
from .knowledge_routes import knowledge_bp
from .simulation_routes import simulation_bp
from .ka_routes import ka_bp
from .mcp_routes import mcp_bp
from backend.routes.multimodal_routes import multimodal_bp


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
    
    # Knowledge Algorithm Routes (JSON API)
    app.register_blueprint(ka_bp, url_prefix='/api/v1/ka')
    app.register_blueprint(ka_bp, name='ka_legacy', url_prefix='/api/ka')
    
    # Simulation Routes (JSON API)
    app.register_blueprint(simulation_bp)
    # Add legacy alias for simulations
    app.register_blueprint(simulation_bp, name='simulation_legacy', url_prefix='/api')
    
    # MCP (Multi-Agent Coordination) Routes (JSON API)
    app.register_blueprint(mcp_bp, url_prefix='/api/v1/mcp')
    app.register_blueprint(mcp_bp, name='mcp_legacy', url_prefix='/api/mcp')
    
    # Compliance Routes (JSON API)
    from .compliance_routes import compliance_bp
    app.register_blueprint(compliance_bp)
    
    # User Data Rights
    from .user_data_routes import user_data_bp
    app.register_blueprint(user_data_bp)

    # Multimodal Routes
    app.register_blueprint(multimodal_bp)

    # Storage Routes (Database Health & Configuration)
    from backend.routes.storage_routes import storage_api
    app.register_blueprint(storage_api)
