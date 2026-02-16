"""
Application configuration compatibility module.

This module preserves the legacy `config.py` API expected by tests and a few
runtime components while the project transitions to backend/config packages.
"""

import os

from dotenv import load_dotenv
from backend.security.secret_resolver import resolve_secret_with_source

load_dotenv()


def _resolve_secret(name: str, default: str | None = None) -> str | None:
    value, _ = resolve_secret_with_source(name, default=default)
    return value


class Config:
    """Base configuration for shared runtime settings."""

    APP_NAME = "Universal Knowledge Graph"
    APP_VERSION = "1.0.0"

    # Secrets default to env-provided values in base config.
    SECRET_KEY = _resolve_secret("SECRET_KEY")
    JWT_SECRET_KEY = _resolve_secret("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///ukg_system.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    DEFAULT_CONFIDENCE_THRESHOLD = 0.85
    MAX_SIMULATION_LAYERS = 7
    DEFAULT_REFINEMENT_STEPS = 12
    ENTROPY_SAMPLING_ENABLED = True
    MEMORY_CACHE_SIZE = 4096
    QUANTUM_SIMULATION_ENABLED = False
    RECURSIVE_PROCESSING_ENABLED = True
    MAX_RECURSION_DEPTH = 8

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "ukg_system.log")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080",
    ).split(",")

    OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET")
    OIDC_DISCOVERY_URL = os.getenv(
        "OIDC_DISCOVERY_URL",
        "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
    )


class DevelopmentConfig(Config):
    """Development defaults for local workflows."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    # Development-only fallback secrets.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-for-local-development-only")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-key-for-local-development-only")

    MAX_SIMULATION_LAYERS = 5
    QUANTUM_SIMULATION_ENABLED = False
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Configuration used by automated tests."""

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    MAX_SIMULATION_LAYERS = 3
    DEFAULT_REFINEMENT_STEPS = 3
    JWT_ACCESS_TOKEN_EXPIRES = 300


class ProductionConfig(Config):
    """Production configuration with secure defaults."""

    DEBUG = False
    TESTING = False

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    JWT_ACCESS_TOKEN_EXPIRES = 30 * 60

    QUANTUM_SIMULATION_ENABLED = True
    RECURSIVE_PROCESSING_ENABLED = True
    DEFAULT_CONFIDENCE_THRESHOLD = 0.90


class DesktopConfig(ProductionConfig):
    """Desktop/local packaged app profile."""

    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://localhost:54320/ukg_local")
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:63790/0")
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "ukg-local-neo4j")

    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    QUANTUM_SIMULATION_ENABLED = True


def get_config():
    """Return config object for the current environment."""
    env = os.environ.get("FLASK_ENV", "development")

    if os.environ.get("IS_DESKTOP_APP", "False").lower() == "true":
        return DesktopConfig()

    if env == "production":
        return ProductionConfig()
    if env == "testing":
        return TestingConfig()
    return DevelopmentConfig()
