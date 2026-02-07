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

TEST_DB_PATH = ROOT_DIR / "test_suite.sqlite3"

import pytest
from app import app as flask_app, db
from extensions import limiter, login_manager

@pytest.fixture
def app():
    """Provide app fixture for tests that need app context."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
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

    from models import User

    # Rebind user loader on each test app setup because the suite imports
    # multiple app factories that can overwrite global LoginManager callbacks.
    @login_manager.user_loader
    def _load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    with flask_app.app_context():
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
        # Ensure test runs start from a clean schema even if the module-level
        # app initialization previously populated the default sqlite database.
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

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
