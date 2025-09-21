
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import get_config

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    config_obj = get_config()
    app.config.from_object(config_obj)
    
    # Initialize extensions
    from .models import db
    db.init_app(app)
    
    jwt = JWTManager(app)
    CORS(app, origins=app.config.get('CORS_ORIGINS'))
    
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
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
