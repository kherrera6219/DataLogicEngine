
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chatbot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # Initialize extensions
    from .models import db
    db.init_app(app)

    JWTManager(app)  # Initialize JWT extension
    CORS(app)
    
    # Register blueprints
    from .auth import auth_bp
    from .chat import chat_bp
    from .admin import admin_bp
    from .ukg_api import ukg_bp
    from .middleware import log_request_info
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ukg_bp, url_prefix='/api/ukg')
    
    # Apply middleware
    log_request_info(app)

    # Note: Database tables are managed through Flask-Migrate migrations
    # Use: python manage_db.py upgrade to apply migrations

    return app
