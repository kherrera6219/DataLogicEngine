import os
import secrets
from backend.llm_gateway.model_defaults import OPENAI_LATEST_MODEL
from backend.security.secret_resolver import resolve_secret_with_source

class APIConfig:
    """Configuration for external APIs"""
    
    def __init__(self):
        # OpenAI Configuration
        self.openai_api_key, _ = resolve_secret_with_source('OPENAI_API_KEY', default='')
        self.openai_model = os.environ.get('OPENAI_MODEL', OPENAI_LATEST_MODEL)
        self.app_version = '2.4.0'
        
        # Database Configuration
        # Defaults to a local sqlite in memory or local file if not provided
        self.db_url = os.environ.get('DATABASE_URL', 'sqlite:///ukg_production.db')
        
        # JWT Configuration
        # Generate a random secret if one isn't provided (transient)
        # Production should use a persistent secret stored via DPAPI or KeyVault
        self.jwt_secret, self.jwt_secret_source = resolve_secret_with_source('JWT_SECRET_KEY')
        if not self.jwt_secret:
            # Fallback for dev, but warn in logs (should be handled by ConfigManager)
            self.jwt_secret = secrets.token_hex(32)
            
        self.jwt_expiry_days = int(os.environ.get('JWT_EXPIRY_DAYS', '7'))
        
        # Replit Auth Configuration
        self.replit_auth_enabled = os.environ.get('REPLIT_AUTH_ENABLED', 'false').lower() == 'true'
