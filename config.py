"""
Universal Knowledge Graph (UKG) System - Configuration

This module provides configuration settings for the UKG system
following Microsoft enterprise standards for security and integration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """Base configuration class for UKG system."""
    
    # Application settings
    APP_NAME = "Universal Knowledge Graph"
    APP_VERSION = "1.0.0"
    
    # Security settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "ukg-dev-key-replace-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "ukg-jwt-dev-key-replace-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60  # 1 hour
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///ukg_system.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # UKG simulation settings
    DEFAULT_CONFIDENCE_THRESHOLD = 0.85
    MAX_SIMULATION_LAYERS = 7
    DEFAULT_REFINEMENT_STEPS = 12
    ENTROPY_SAMPLING_ENABLED = True
    MEMORY_CACHE_SIZE = 4096  # MB
    QUANTUM_SIMULATION_ENABLED = False
    RECURSIVE_PROCESSING_ENABLED = True
    MAX_RECURSION_DEPTH = 8
    
    # Microsoft Enterprise integration settings
    AZURE_AD_TENANT_ID = os.environ.get("AZURE_AD_TENANT_ID")
    AZURE_AD_CLIENT_ID = os.environ.get("AZURE_AD_CLIENT_ID")
    AZURE_AD_CLIENT_SECRET = os.environ.get("AZURE_AD_CLIENT_SECRET")
    
    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    # Azure Storage settings
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "ukg-media")
    
    # Logging settings
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "ukg_system.log")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS settings
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Override for development
    MAX_SIMULATION_LAYERS = 5
    QUANTUM_SIMULATION_ENABLED = False
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Testing environment configuration."""
    
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # For testing purposes
    MAX_SIMULATION_LAYERS = 3
    DEFAULT_REFINEMENT_STEPS = 3
    JWT_ACCESS_TOKEN_EXPIRES = 300  # 5 minutes


class ProductionConfig(Config):
    """Production environment configuration with enhanced security."""
    
    DEBUG = False
    TESTING = False
    
    # Force secure settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # More strict settings for production
    JWT_ACCESS_TOKEN_EXPIRES = 30 * 60  # 30 minutes
    
    # Enable advanced features in production
    QUANTUM_SIMULATION_ENABLED = True
    RECURSIVE_PROCESSING_ENABLED = True
    DEFAULT_CONFIDENCE_THRESHOLD = 0.90


# Configuration mapping
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig
}

# Get current configuration
def get_config():
    """Get the current configuration based on environment."""
    env = os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)