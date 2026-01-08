from flask import Blueprint
from .auth_routes import auth_bp
from .page_routes import page_bp
from .api_routes import api_bp
from .admin_routes import admin_bp
from .knowledge_routes import knowledge_bp
from .simulation_routes import simulation_bp

def register_routes(app):
    """Register all application blueprints."""
    
    # Page Routes (Frontend)
    app.register_blueprint(page_bp)
    
    # Auth Routes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # API Routes
    app.register_blueprint(api_bp)
    
    # Admin Routes
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Knowledge Routes (Core Entities)
    app.register_blueprint(knowledge_bp)
    
    # Simulation Routes
    app.register_blueprint(simulation_bp)
    
    # Replit Auth (if configured)
    # Handled in app.py
