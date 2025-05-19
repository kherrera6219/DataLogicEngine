
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chatbot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    
    # Initialize extensions
    from .models import db
    db.init_app(app)
    
    jwt = JWTManager(app)
    CORS(app)
    
    # Register blueprints
    from .auth import auth_bp
    from .chat import chat_bp
    from .admin import admin_bp
    from .middleware import log_request_info
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Apply middleware
    log_request_info(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
