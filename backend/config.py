
import os

class APIConfig:
    """Configuration for external APIs"""
    
    def __init__(self):
        # OpenAI Configuration
        self.openai_api_key = os.environ.get('OPENAI_API_KEY', '')
        self.openai_model = os.environ.get('OPENAI_MODEL', 'gpt-4')
        
        # Database Configuration
        self.db_url = os.environ.get('DATABASE_URL', 'sqlite:///chatbot.db')
        
        # JWT Configuration
        self.jwt_secret = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
        self.jwt_expiry_days = int(os.environ.get('JWT_EXPIRY_DAYS', '7'))
        
        # Replit Auth Configuration
        self.replit_auth_enabled = os.environ.get('REPLIT_AUTH_ENABLED', 'true').lower() == 'true'
