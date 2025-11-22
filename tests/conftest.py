"""
Pytest configuration and shared fixtures for UKG System tests
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask application instance for testing"""
    from app import app as flask_app

    # Set testing configuration
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key-do-not-use-in-production',
        'WTF_CSRF_ENABLED': False,
    })

    yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner for the Flask application"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db(app):
    """Create a clean database for each test"""
    from app import db as _db

    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!'
    }


@pytest.fixture
def auth_headers():
    """Generate authentication headers for API requests"""
    def _auth_headers(token):
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    return _auth_headers


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
