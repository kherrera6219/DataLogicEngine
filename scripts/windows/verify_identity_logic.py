import os
import sys
import unittest

# Add current directory to path
sys.path.append(os.getcwd())

import tempfile
import shutil

# 1. Create isolated key directory for the entire test session
TEST_KEY_DIR = tempfile.mkdtemp()
os.environ["UKG_KEY_DIR"] = TEST_KEY_DIR

from datetime import datetime
from flask import Flask
from extensions import db, login_manager, audit_logger, rbac_manager
from models import User, AuditLog
from routes.auth_routes import auth_bp

class TestIdentityIsolation(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-key'
        
        # Isolate encryption keys for testing
        import tempfile
        import shutil
        self.test_key_dir = tempfile.mkdtemp()
        
        from extensions import encryption_manager as em
        em.key_dir = self.test_key_dir
        em.kek_file = os.path.join(self.test_key_dir, "kek.enc")
        em.dek_registry_file = os.path.join(self.test_key_dir, "dek_registry.json")
        em._kek = em._load_or_create_kek()
        em.dek_registry = em._load_dek_registry()
        em._current_dek = em._get_current_dek()

        db.init_app(self.app)
        login_manager.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        
        with self.app.app_context():
            db.create_all()

    def test_first_run_owner_assignment(self):
        """Verify that the first registered Windows user becomes the Owner."""
        with self.app.app_context():
            # Mock the windows identity resolution
            from unittest.mock import patch
            with patch('backend.auth.windows_identity.get_windows_user_identity') as mock_identity:
                mock_identity.return_value = {'username': 'owner_user', 'sid': 'S-1-5-21-OWNER'}
                
                # Call desktop_auto_login
                with self.app.test_client() as client:
                    response = client.post('/api/v1/auth/desktop/auto-login')
                    self.assertEqual(response.status_code, 200)
                    
                    user = User.query.filter_by(sid='S-1-5-21-OWNER').first()
                    self.assertIsNotNone(user)
                    self.assertEqual(user.role, 'owner')
                    self.assertTrue(user.is_admin)
                    
                    # Check Audit Log
                    audit = AuditLog.query.filter_by(windows_sid='S-1-5-21-OWNER').first()
                    self.assertIsNotNone(audit)
                    self.assertEqual(audit.action, "FIRST_RUN_REGISTRATION")

    def test_subsequent_user_assignment(self):
        """Verify that subsequent Windows users become standard users."""
        with self.app.app_context():
            from unittest.mock import patch
            
            # 1. Register Owner
            owner = User(username="owner", email="owner@local.ukg", password_hash="dummy", sid="S-OWNER", role="owner", is_admin=True)
            db.session.add(owner)
            db.session.commit()
            
            # 2. Register Second User
            with patch('backend.auth.windows_identity.get_windows_user_identity') as mock_identity:
                mock_identity.return_value = {'username': 'second_user', 'sid': 'S-SECOND'}
                
                with self.app.test_client() as client:
                    response = client.post('/api/v1/auth/desktop/auto-login')
                    self.assertEqual(response.status_code, 200)
                    
                    user = User.query.filter_by(sid='S-SECOND').first()
                    self.assertIsNotNone(user)
                    self.assertEqual(user.role, 'user')
                    self.assertFalse(user.is_admin)

    def test_username_deconfliction(self):
        """Verify that identical Windows usernames result in unique app usernames."""
        with self.app.app_context():
            from unittest.mock import patch
            
            # 1. Existing user with name 'kevin'
            user1 = User(username="kevin", email="kevin@local.ukg", password_hash="dummy", sid="S-1")
            db.session.add(user1)
            db.session.commit()
            
            # 2. New Windows user also named 'kevin' (different SID)
            with patch('backend.auth.windows_identity.get_windows_user_identity') as mock_identity:
                mock_identity.return_value = {'username': 'kevin', 'sid': 'S-2'}
                
                with self.app.test_client() as client:
                    response = client.post('/api/v1/auth/desktop/auto-login')
                    self.assertEqual(response.status_code, 200)
                    
                    user2 = User.query.filter_by(sid='S-2').first()
                    self.assertEqual(user2.username, "kevin_1")

    def tearDown(self):
        import shutil
        if hasattr(self, 'test_key_dir'):
            shutil.rmtree(self.test_key_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
