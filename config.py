"""
Universal Knowledge Graph (UKG) System - Configuration

This module provides configuration settings for the UKG system.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppConfig:
    """Configuration for the UKG application"""
    
    def __init__(self):
        """Initialize configuration."""
        # Database configuration
        self.database_url = os.environ.get('DATABASE_URL')
        
        # Server configuration
        self.port = int(os.environ.get('PORT', 8080))
        self.host = os.environ.get('HOST', '0.0.0.0')
        self.debug = os.environ.get('DEBUG', 'True').lower() == 'true'
        
        # Application configuration
        self.secret_key = os.environ.get('SECRET_KEY', 'ukg-development-secret-key')
        
        # Logging configuration
        self.log_level = os.environ.get('LOG_LEVEL', 'DEBUG')
        
        # Simulation configuration
        self.simulation_steps = int(os.environ.get('SIMULATION_STEPS', 10))
        self.simulation_interval = float(os.environ.get('SIMULATION_INTERVAL', 1.0))
        
        # API configuration
        self.api_version = os.environ.get('API_VERSION', 'v1')
        self.api_prefix = f'/api/{self.api_version}'
        
        # Storage configuration
        self.upload_folder = os.environ.get('UPLOAD_FOLDER', './uploads')
        self.allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'json', 'xml'}
        
        # Security configuration
        self.cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')

# Create a configuration instance
config = AppConfig()