import pytest
from unittest.mock import MagicMock
from knowledge_algorithms.ka_118_sensitive_data_discovery import KA118SensitiveDataDiscovery
from backend.security.rbac import RBACManager, Permission

class MockUser:
    def __init__(self, username, role):
        self.username = username
        self.role = role
        self.is_authenticated = True
        self.id = 123

class TestDataProtection:
    
    def test_ka118_pii_detection(self):
        """Verify KA-118 detects email addresses."""
        agent = KA118SensitiveDataDiscovery()
        params = {"data": {"content": "Contact me at test.user@example.com regarding the merge."}}
        
        result = agent.run(params)
        
        # .run() returns a KAResult dict, logic output is in 'output'
        assert result["success"] is True
        output = result["output"]
        assert "PII:EMAIL" in output["detected_tags"]
        assert output["classification_level"] == "CONFIDENTIAL"

    def test_ka118_secret_detection(self):
        """Verify KA-118 detects API keys."""
        agent = KA118SensitiveDataDiscovery()
        # Simulated API key pattern
        params = {"data": {"content": "api_key = 'sk-123456789012345678901234567890'"}}
        
        result = agent.run(params)
        
        assert result["success"] is True
        output = result["output"]
        assert "SECRET:KEY" in output["detected_tags"]
        assert output["classification_level"] == "CRITICAL"

    def test_rbac_deny_by_default(self):
        """Verify RBAC blocks PII access without permission."""
        rbac = RBACManager()
        # Mock user without PRIVACY_READER
        user = MockUser("regular_joe", "user")
        
        # Tags indicating PII
        tags = ["PII:EMAIL"]
        
        # Should be denied
        allowed = rbac.check_data_access(user, tags)
        assert allowed is False

    def test_rbac_allow_with_permission(self):
        """Verify RBAC allows PII access with permission."""
        rbac = RBACManager()
        # Mock user WITH PRIVACY_READER (via Security Officer role)
        user = MockUser("sec_officer", "security_officer")
        
        tags = ["PII:EMAIL"]
        
        # Should be allowed
        allowed = rbac.check_data_access(user, tags)
        assert allowed is True
