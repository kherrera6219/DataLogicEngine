
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from backend.utils.cors_policy import resolve_service_cors_policy


def _required_secret_config(name: str, *, pytest_default: str) -> str:
    is_pytest = "PYTEST_CURRENT_TEST" in os.environ
    if is_pytest:
        return os.environ.get(name, pytest_default)

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} must be configured before create_legacy_app starts outside tests")
    return value


def create_legacy_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    # Keep deterministic defaults under pytest only; runtime callers must provide secrets.
    app.config['SECRET_KEY'] = _required_secret_config('SECRET_KEY', pytest_default='dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chatbot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = _required_secret_config('JWT_SECRET_KEY', pytest_default='jwt-secret-key')
    
    # Initialize extensions
    from extensions import db, login_manager
    from models import User
    # In legacy app, we still need to initialize db if it's used elsewhere
    # but models should come from the unified registry.
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    JWTManager(app)  # Initialize JWT extension
    allowed_origins, allow_credentials = resolve_service_cors_policy(
        preferred_env_var="CORS_ORIGINS",
        fallback_env_var="CORS_ORIGINS",
    )
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=allow_credentials,
    )
    
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
    from routes.ka_routes import ka_bp
    from .truth_engine.api import truth_api
    from .tracing.api import trace_bp
    
    # `auth_bp` already defines `/api/v1/auth` as its blueprint prefix.
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(ukg_bp, url_prefix='/api/ukg')
    app.register_blueprint(user_data_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(location_bp, url_prefix='/api/v1/location')
    app.register_blueprint(routes_admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(ka_bp, url_prefix='/api/v1/ka')
    app.register_blueprint(truth_api, url_prefix='/api/v1/truth')
    app.register_blueprint(trace_bp)
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
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'error': 'Not Found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'error': 'Internal Server Error'}), 500

    return app
