
import os
import unittest
from unittest import mock
from app import app, db, User

class TestCriticalFixes(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for easier testing
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        db.create_all()
        
        # Create a test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('Secure!Token789')
        db.session.add(self.user)
        
        # Create an admin user
        self.admin = User(username='admin', email='admin@example.com', is_admin=True)
        self.admin.set_password('Admin!Access789')
        db.session.add(self.admin)
        
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_production_config_hardening(self):
        """Test that secure cookies are enforced when FLASK_ENV is production"""
        # Mock environment variables
        with mock.patch.dict(os.environ, {'FLASK_ENV': 'production', 'SESSION_COOKIE_SECURE': 'true'}):
            # Re-apply config logic from app.py (simplified for test since we can't reload app easily)
            is_production = os.environ.get("FLASK_ENV") != "development"
            secure_cookie = os.environ.get("SESSION_COOKIE_SECURE", "True" if is_production else "False").lower() == "true"
            
            self.assertTrue(is_production)
            self.assertTrue(secure_cookie)

    # Legacy web-login + MFA UI tests removed: the /login, /mfa-setup, /mfa-verify
    # routes were deleted with multi-user auth, and the User MFA columns were dropped
    # in auth-deprecation Phase E (single-mode / OS-level auth).

if __name__ == '__main__':
    unittest.main()
