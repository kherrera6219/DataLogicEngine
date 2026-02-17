# ruff: noqa: E402
import os
import sys
import unittest
import json

# Add current directory to path
sys.path.append(os.getcwd())

import tempfile
import shutil

# 1. Create isolated key directory for the entire test session
TEST_KEY_DIR = tempfile.mkdtemp()
os.environ["UKG_KEY_DIR"] = TEST_KEY_DIR

from flask import Flask
from extensions import db, login_manager, cache
from models import User, AuditLog
from routes.admin_routes import admin_bp
from routes.user_data_routes import user_data_bp

class TestAuditSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['TESTING'] = True
        cls.app.config['SECRET_KEY'] = 'test-key'
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.app.config['CACHE_TYPE'] = 'SimpleCache'
        
        db.init_app(cls.app)
        login_manager.init_app(cls.app)
        cache.init_app(cls.app)
        cls.app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
        cls.app.register_blueprint(user_data_bp, url_prefix='/api/v1/user/data')
        
        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_KEY_DIR):
            shutil.rmtree(TEST_KEY_DIR, ignore_errors=True)

    def test_ownership_transfer_auditing(self):
        """Verify that transferring ownership creates a valid audit log."""
        with self.app.app_context():
            # Create Owner and Admin
            owner = User(username="owner", email="owner@local.ukg", password_hash="dummy", sid="S-OWNER", role="owner", is_admin=True)
            admin = User(username="admin_user", email="admin@local.ukg", password_hash="dummy", sid="S-ADMIN", role="admin", is_admin=True)
            db.session.add_all([owner, admin])
            db.session.commit()
            
            with self.app.test_client() as client:
                # Use patch to mock current_user
                from unittest.mock import patch
                with patch('flask_login.utils._get_user', return_value=owner):
                    # Transfer
                    response = client.post('/api/v1/admin/users/transfer-ownership', json={
                        'target_user_id': admin.id,
                        'confirm': 'TRANSFER'
                    })
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify Roles
                    self.assertEqual(admin.role, 'owner')
                    self.assertEqual(owner.role, 'admin')
                    
                    # Check Audit Log
                    audit = AuditLog.query.filter_by(action="OWNERSHIP_TRANSFERRED").first()
                    self.assertIsNotNone(audit)
                    self.assertEqual(audit.user_id, owner.id)
                    details = json.loads(audit.details) if isinstance(audit.details, str) else audit.details
                    self.assertEqual(details['to_username'], "admin_user")

    def test_profile_deletion_auditing(self):
        """Verify that profile deletion creates a valid audit log before wiping."""
        with self.app.app_context():
            user = User(username="audit_test", email="audit@local.ukg", password_hash="dummy", sid="S-AUDIT", role="user")
            db.session.add(user)
            db.session.commit()
            
            with self.app.test_client() as client:
                from unittest.mock import patch
                with patch('flask_login.utils._get_user', return_value=user):
                    # Delete profile
                    response = client.post('/api/v1/user/data/delete', json={
                        'confirm': 'DELETE'
                    })
                    self.assertEqual(response.status_code, 200)
                    
                    # Check Audit Log
                    audit = AuditLog.query.filter_by(action="PROFILE_WIPE").first()
                    self.assertIsNotNone(audit)
                    self.assertEqual(audit.windows_sid, "S-AUDIT")
                    # User should be gone
                    deleted_user = User.query.filter_by(sid="S-AUDIT").first()
                    self.assertIsNone(deleted_user)

if __name__ == "__main__":
    unittest.main()
