import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()

# Force in-memory storage for tests to avoid Redis dependencies
os.environ['RATELIMIT_STORAGE_URI'] = 'memory://'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0' # Keep URL but we'll disable it
os.environ['USE_REDIS'] = 'False'
os.environ['SESSION_TYPE'] = 'null' # Disable flask-session for tests if possible

# Ensure repository root is on the Python path for tests
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from app import app as flask_app, db
from extensions import limiter

@pytest.fixture
def app():
    """Provide app fixture for tests that need app context."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['CACHE_TYPE'] = 'NullCache'
    flask_app.config['RATELIMIT_ENABLED'] = False
    flask_app.config['CORS_ORIGINS'] = "*"
    flask_app.config['CORS_RESOURCES'] = {r"/*": {"origins": "*"}}
    
    # Remove Limiter from before_request_funcs to avoid Redis connection
    for key in list(flask_app.before_request_funcs.keys()):
        flask_app.before_request_funcs[key] = [
            f for f in flask_app.before_request_funcs[key]
            if 'check_request_limit' not in getattr(f, '__name__', '')
        ]
    
    from limits.storage.memory import MemoryStorage
    limiter._storage = MemoryStorage() 
    limiter.enabled = False

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    with app.test_client() as test_client:
        yield test_client

@pytest.fixture
def authenticated_client(app, client):
    """Create authenticated test client."""
    # Register and login user using JSON data
    test_pass = 'SecureTest789$#@'
    client.post('/api/v1/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': test_pass,
        'confirm_password': test_pass
    })

    client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': test_pass
    })

    return client
