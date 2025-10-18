"""
Universal Knowledge Graph (UKG) System - Configuration

This module provides configuration settings for the UKG system
following Microsoft enterprise standards for security and integration.
"""

import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def _generate_ephemeral_secret(env_key: str) -> str:
    """Return a secure secret for the provided environment key."""

    value = os.environ.get(env_key)
    if value:
        return value

    # Fallback to a strong, process-unique secret so development runs remain safe.
    generated = secrets.token_hex(32)
    logger.warning(
        "%s not configured. Using a generated, ephemeral secret; set the environment "
        "variable to persist sessions across restarts.",
        env_key,
    )
    return generated


def _default_sqlite_uri() -> str:
    """Provide a safe SQLite URI when no database URL is configured."""

    db_path = Path(os.environ.get("UKG_SQLITE_PATH", "ukg_system.db")).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def _parse_cors_origins(value: str | None) -> list[str]:
    """Parse the configured CORS origins with sensible defaults."""

    if value:
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    # Restrict defaults to common local development hosts rather than wildcard access.
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


class Config:
    """Base configuration class for UKG system."""
    
    # Application settings
    APP_NAME = "Universal Knowledge Graph"
    APP_VERSION = "1.0.0"
    
    # Security settings
    SECRET_KEY = _generate_ephemeral_secret("SECRET_KEY")
    JWT_SECRET_KEY = _generate_ephemeral_secret("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60  # 1 hour
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or _default_sqlite_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # UKG specific settings
    DEFAULT_CONFIDENCE_THRESHOLD = 0.85
    MAX_SIMULATION_LAYERS = 7
    DEFAULT_REFINEMENT_STEPS = 12
    ENTROPY_SAMPLING_ENABLED = True
    MEMORY_CACHE_SIZE = 4096  # MB
    QUANTUM_SIMULATION_ENABLED = False
    RECURSIVE_PROCESSING_ENABLED = True
    MAX_RECURSION_DEPTH = 8
    
    # Azure AD/Entra ID Integration
    AZURE_AD_TENANT_ID = os.environ.get("AZURE_AD_TENANT_ID")
    AZURE_AD_CLIENT_ID = os.environ.get("AZURE_AD_CLIENT_ID")
    AZURE_AD_CLIENT_SECRET = os.environ.get("AZURE_AD_CLIENT_SECRET")
    
    # Azure OpenAI Integration
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "ukg-media")
    
    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "ukg_system.log")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS settings
    CORS_ORIGINS = _parse_cors_origins(os.environ.get("CORS_ORIGINS"))


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Simplified UKG settings for development
    MAX_SIMULATION_LAYERS = 5
    QUANTUM_SIMULATION_ENABLED = False
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Testing environment configuration."""
    
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Simplified UKG settings for testing
    MAX_SIMULATION_LAYERS = 3
    DEFAULT_REFINEMENT_STEPS = 3
    JWT_ACCESS_TOKEN_EXPIRES = 300  # 5 minutes


class ProductionConfig(Config):
    """Production environment configuration with enhanced security."""
    
    DEBUG = False
    TESTING = False
    
    # Enforce secure settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # Production settings
    JWT_ACCESS_TOKEN_EXPIRES = 30 * 60  # 30 minutes
    
    # Full UKG capabilities
    QUANTUM_SIMULATION_ENABLED = True
    RECURSIVE_PROCESSING_ENABLED = True
    DEFAULT_CONFIDENCE_THRESHOLD = 0.90


def get_config():
    """Get the current configuration based on environment."""
    env = os.environ.get("FLASK_ENV", "development")
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()