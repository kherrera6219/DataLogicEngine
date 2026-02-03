
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

def create_legacy_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chatbot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # Initialize extensions
    from extensions import db
    from models import User
    # In legacy app, we still need to initialize db if it's used elsewhere
    # but models should come from the unified registry.
    db.init_app(app)

    JWTManager(app)  # Initialize JWT extension
    CORS(app)
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from .chat import chat_bp
    from .admin import admin_bp
    from .ukg_api import ukg_api as ukg_bp
    from routes.user_data_routes import user_data_bp
    from .routes.settings_routes import settings_bp
    from .routes.location_routes import location_api as location_bp
    from routes.admin_routes import admin_bp as routes_admin_bp
    from routes.api_routes import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ukg_bp, url_prefix='/api/ukg')
    app.register_blueprint(user_data_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(location_bp, url_prefix='/api/v1/location')
    app.register_blueprint(routes_admin_bp)
    app.register_blueprint(api_bp)
    # Re-register search blueprint from new location if needed, or assume it's covered by imports.
    # Logic note: search_api was not previously in __init__.py imports list in step 1253 view.
    # Let's check if it was registered. It was NOT in the list.
    # I will add it now.
    
    from .routes.search_routes import search_api as search_bp
    app.register_blueprint(search_bp, url_prefix='/api/search')
    
    # LLM Gateway Blueprints
    from .llm_gateway.api import gateway_bp, admin_bp as gateway_admin_bp
    app.register_blueprint(gateway_bp)
    app.register_blueprint(gateway_admin_bp)
    
    # UKG Structural APIs
    from .pillar_api import pillar_api
    from .rest_api import rest_api
    app.register_blueprint(pillar_api, url_prefix='/api/v1/pillars_axis')
    app.register_blueprint(rest_api)
    
    # Create database tables
    # db is already initialized in extensions.py
    # db.create_all() is handled by app.py or init_db.py
    pass
    
    return app
