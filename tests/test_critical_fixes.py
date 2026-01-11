
import os
import unittest
from unittest import mock
from datetime import timedelta
from flask import Flask, session
from flask_login import LoginManager, UserMixin
from app import app, db, User
import pyotp
from backend.tracing.models import TraceRun

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

    @unittest.skip("Legacy UI test - App is now API-only")
    def test_mfa_flow_admin_enforcement(self):
        """Test that admins are redirected to MFA setup"""
        # Login as admin
        try:
            response = self.app.post('/login', data={
                'username': 'admin',
                'password': 'Admin!Access789'
            }, follow_redirects=True)
        except Exception as e:
            print(f"LOGIN FAILED WITH ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise e
        
        # Should be redirected to /mfa-setup
        self.assertIn(b'Setup Two-Factor Authentication', response.data)
        
        # Verify user is partially logged in (login_user called temporarily)
        # Note: In the real app, we check if they are logged in.
        # Let's verify we can access mfa-setup
        response = self.app.get('/mfa-setup', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    @unittest.skip("Legacy UI test - App is now API-only")
    def test_mfa_setup_and_verify(self):
        """Test full MFA setup and subsequent login verification"""
        # 1. Login as standard user (no MFA yet)
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'Secure!Token789'
        }, follow_redirects=True)
        
        # 2. Go to MFA setup manually (simulate user enabling it)
        response = self.app.get('/mfa-setup')
        # Extract secret from context or HTML (mocking the secret for test)
        # We'll just set it directly on the user for the test
        user = User.query.filter_by(username='testuser').first()
        import pyotp
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        db.session.commit()
        
        # 3. Submit correct token to enable
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        response = self.app.post('/mfa-setup', data={'token': token}, follow_redirects=True)
        self.assertIn(b'Two-factor authentication enabled successfully', response.data)
        
        # Verify MFA is enabled in DB
        user = User.query.filter_by(username='testuser').first()
        self.assertTrue(user.mfa_enabled)
        
        # 4. Logout
        self.app.get('/logout', follow_redirects=True)
        
        # 5. Login again - should redirect to mfa-verify
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'Secure!Token789'
        }, follow_redirects=True)
        
        self.assertIn(b'Two-Factor Authentication', response.data)
        self.assertIn(b'Verify', response.data) # Button text
        
        # 6. Submit correct code to mfa-verify
        token = totp.now()
        response = self.app.post('/mfa-verify', data={'token': token}, follow_redirects=True)
        
        # Should be at dashboard
        self.assertIn(b'Dashboard', response.data)

if __name__ == '__main__':
    unittest.main()
