import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    """Configuration for the UKG application"""

    def __init__(self):
        # Debug mode
        self.DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

        # Server configuration
        self.HOST = os.environ.get('HOST', '0.0.0.0')
        self.PORT = int(os.environ.get('PORT', 5000))

        # API Configuration
        self.OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
        self.OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4')

        # Database Configuration
        self.DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///ukg.db')

        # JWT Configuration
        self.JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'ukg-secret-key')
        self.JWT_EXPIRY_DAYS = int(os.environ.get('JWT_EXPIRY_DAYS', '7'))

        # UKG Configuration
        self.CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', '0.85'))
        self.ENABLE_LOCATION_CONTEXT = os.environ.get('ENABLE_LOCATION_CONTEXT', 'true').lower() == 'true'
        self.ENABLE_RESEARCH_AGENTS = os.environ.get('ENABLE_RESEARCH_AGENTS', 'true').lower() == 'true'

# Create a global instance
config = AppConfig()