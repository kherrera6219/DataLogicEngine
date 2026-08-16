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


def _legacy_api_prefixes_enabled(app) -> bool:
    """Honor app config from create_app, else env (default off)."""
    if app is not None and "DLE_LEGACY_API_PREFIXES" in app.config:
        return bool(app.config.get("DLE_LEGACY_API_PREFIXES"))
    import os

    raw = (os.environ.get("DLE_LEGACY_API_PREFIXES") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def register_routes(app):
    """Register application blueprints."""
    legacy = _legacy_api_prefixes_enabled(app)

    # Auth routes (`/api/v1/auth/*`)
    app.register_blueprint(auth_bp)

    # Generic API routes (`/api/v1/*`)
    app.register_blueprint(api_bp)
    app.register_blueprint(memory_api)

    # Ops admin routes (`/api/v1/admin/cache/*`, `/api/v1/admin/health`)
    # Gateway admin is registered separately under `/api/v1/admin/gateway/*`.
    app.register_blueprint(admin_bp)

    # Core knowledge routes (`/api/v1/knowledge/*`)
    app.register_blueprint(knowledge_bp)

    # Knowledge algorithm routes (`/api/v1/ka/*` + optional legacy)
    app.register_blueprint(ka_bp, url_prefix="/api/v1/ka")
    if legacy:
        app.register_blueprint(ka_bp, name="ka_legacy", url_prefix="/api/ka")

    # Simulation routes (`/api/v1/simulations/*` + optional legacy)
    app.register_blueprint(simulation_bp)
    if legacy:
        app.register_blueprint(simulation_bp, name="simulation_legacy", url_prefix="/api")

    # MCP routes (`/api/v1/mcp/*` + optional legacy)
    app.register_blueprint(mcp_bp, url_prefix="/api/v1/mcp")
    if legacy:
        app.register_blueprint(mcp_bp, name="mcp_legacy", url_prefix="/api/mcp")

    # Axis-7 UKG compliance standards (`/api/v1/compliance/*`) — sole owner of this prefix.
    from .compliance_routes import compliance_bp

    app.register_blueprint(compliance_bp)

    # Dataset Exporter routes (`/api/v1/dataset/*`)
    from .dataset_routes import dataset_bp

    app.register_blueprint(dataset_bp)

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
