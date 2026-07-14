import logging

from .admin_routes import admin_bp
from .api_routes import api_bp
from .memory_routes import memory_api
from .auth_routes import auth_bp
from .ka_routes import ka_bp
from .knowledge_routes import knowledge_bp
from .mcp_routes import mcp_bp
from .simulation_routes import simulation_bp
from backend.contextual_api import contextual_bp
from backend.honeycomb_api import honeycomb_api
from backend.methods_api import methods_api
from backend.routes.multimodal_routes import multimodal_bp
from backend.routes.search_routes import search_api


logger = logging.getLogger(__name__)


def register_routes(app):
    """Register application blueprints."""
    # Auth routes (`/api/v1/auth/*`)
    app.register_blueprint(auth_bp)

    # Generic API routes (`/api/v1/*`)
    app.register_blueprint(api_bp)
    app.register_blueprint(memory_api)

    # Admin routes (`/api/v1/admin/*`)
    app.register_blueprint(admin_bp)

    # Core knowledge routes (`/api/v1/knowledge/*`)
    app.register_blueprint(knowledge_bp)

    # Knowledge algorithm routes (`/api/v1/ka/*` + legacy)
    app.register_blueprint(ka_bp, url_prefix="/api/v1/ka")
    app.register_blueprint(ka_bp, name="ka_legacy", url_prefix="/api/ka")

    # Simulation routes (`/api/v1/simulations/*` + legacy)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(simulation_bp, name="simulation_legacy", url_prefix="/api")

    # MCP routes (`/api/v1/mcp/*` + legacy)
    app.register_blueprint(mcp_bp, url_prefix="/api/v1/mcp")
    app.register_blueprint(mcp_bp, name="mcp_legacy", url_prefix="/api/mcp")

    # Compliance routes
    from .compliance_routes import compliance_bp

    app.register_blueprint(compliance_bp)

    # User data rights routes
    from .user_data_routes import user_data_bp

    app.register_blueprint(user_data_bp)

    # Multimodal routes
    app.register_blueprint(multimodal_bp)

    # Storage routes (`/api/v1/storage/*`)
    from backend.routes.storage_routes import storage_api

    app.register_blueprint(storage_api)

    # Local-first knowledge ingestion routes (`/api/v1/ingestion/*`)
    from backend.routes.ingestion_routes import ingestion_api

    app.register_blueprint(ingestion_api)

    # Search routes (`/api/search/*`)
    app.register_blueprint(search_api, url_prefix="/api/search")

    # Contextual experts routes (`/api/contextual/*`)
    app.register_blueprint(contextual_bp)

    # Methods routes (`/api/methods/*`)
    app.register_blueprint(methods_api)

    # Honeycomb routes (`/api/honeycomb/*`)
    app.register_blueprint(honeycomb_api)

    # Notification preference routes (`/api/v1/user/notifications`)
    from .notification_routes import notification_bp
    app.register_blueprint(notification_bp)

    # Feature flag runtime + admin routes
    from .feature_flag_routes import feature_flag_bp
    app.register_blueprint(feature_flag_bp)

    # Optional location routes
    try:
        from backend.routes.location_routes import location_api

        app.register_blueprint(location_api)
    except ImportError:
        logger.warning("Location routes unavailable; skipping registration.")

    # AI settings routes (`/api/v1/settings/*`).
    # analytics, gdpr, retention, and privacy blueprints are registered directly
    # by app.py after register_routes() returns — do not re-register them here.
    from backend.routes.settings_routes import settings_bp
    app.register_blueprint(settings_bp)
