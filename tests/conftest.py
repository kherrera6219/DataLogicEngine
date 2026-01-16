import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest
from app import app, db
from extensions import limiter

# Load environment variables for tests
load_dotenv()

# Ensure repository root is on the Python path for tests
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['CACHE_TYPE'] = 'NullCache'
    app.config['RATELIMIT_ENABLED'] = False
    app.config['CORS_ORIGINS'] = "*"
    app.config['CORS_RESOURCES'] = {r"/*": {"origins": "*"}}
    
    # Remove Limiter from before_request_funcs to avoid Redis connection
    for key in list(app.before_request_funcs.keys()):
        app.before_request_funcs[key] = [
            f for f in app.before_request_funcs[key]
            if 'check_request_limit' not in getattr(f, '__name__', '')
        ]
    
    # Also patch storage just in case direct calls happen
    from limits.storage.memory import MemoryStorage
    limiter._storage = MemoryStorage() 
    limiter.enabled = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def authenticated_client(client):
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
