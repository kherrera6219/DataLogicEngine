import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_flask_app():
    """Provide a global mock for Flask application context."""
    mock_app = MagicMock()
    # Mock current_app.app_context()
    ctx = mock_app.app_context.return_value
    ctx.__enter__.return_value = MagicMock()
    
    with patch('flask.current_app', mock_app):
        yield mock_app

@pytest.fixture
def mock_db_extensions():
    """Mock db and cache extensions globally."""
    mock_db = MagicMock()
    mock_db.session = MagicMock()
    # Mock db.Model for inheritance
    mock_db.Model = MagicMock()
    
    mock_cache = MagicMock()
    
    with patch('extensions.db', mock_db), \
         patch('extensions.cache', mock_cache):
        yield mock_db, mock_cache

@pytest.fixture
def client():
    """Create a test client for the application."""
    from backend import create_legacy_app
    app = create_legacy_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
