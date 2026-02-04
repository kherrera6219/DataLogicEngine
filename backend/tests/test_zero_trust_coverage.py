
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta, UTC
import json

from backend.security.zero_trust import (
    ZeroTrustManager, 
    TrustScoreCalculator, 
    AccessContext, 
    DeviceFingerprint,
    TrustLevel,
    RiskLevel
)

class TestTrustScoreCalculator:
    @pytest.fixture
    def calculator(self):
        with patch("os.makedirs"), \
             patch("os.path.exists", return_value=False), \
             patch("builtins.open", mock_open()):
             
            return TrustScoreCalculator()

    def test_calculate_user_trust_new_user(self, calculator):
        score = calculator._calculate_user_trust_score("new_user")
        assert score == 15

    def test_calculate_device_trust_known(self, calculator):
        device = DeviceFingerprint(
            device_id="dev_123", user_agent="test", ip_address="1.2.3.4",
            os_family="Windows", browser_family="Chrome", 
            is_mobile=False, is_tablet=False, is_pc=True
        )
        
        # Manually seed registry
        calculator.device_registry = {"dev_123": {"successful_auths": 20}}
        
        score = calculator._calculate_device_trust_score(device)
        # Base 10 + Known 5 + Auth History 3 = 18 (Assuming no other bonuses met)
        assert score >= 18

    def test_calculate_context_trust(self, calculator):
        # Create a mock context
        device = MagicMock()
        context = AccessContext(
            user_id="u1",
            device=device,
            time_of_day=10, # Business hours
            network_type="corporate"
        )
        
        score = calculator._calculate_context_trust_score(context)
        # Base 15 + Time 3 + Corp Network 5 = 23
        assert score == 23

class TestZeroTrustManager:
    @pytest.fixture
    def zt_manager(self):
        with patch("os.makedirs"), \
             patch("os.path.exists", return_value=False), \
             patch("builtins.open", mock_open()):
            
            # Mock calculator inside manager
            mgr = ZeroTrustManager()
            return mgr

    def test_evaluate_access_allow(self, zt_manager):
        # Setup high trust score
        zt_manager.trust_calculator.calculate_trust_score = MagicMock(return_value=(85, {}))
        
        # Create dummy inputs
        device = MagicMock()
        device.device_id = "d1"
        
        allowed, risk, details = zt_manager.evaluate_access_request(
            "u1", device, "view_dashboard", "read"
        )
        
        assert allowed is True
        assert details["trust_level"] == "VERIFIED"

    def test_evaluate_access_deny_critical(self, zt_manager):
        # Setup low trust score
        zt_manager.trust_calculator.calculate_trust_score = MagicMock(return_value=(30, {}))
        
        device = MagicMock()
        device.device_id = "d1"
        
        # Request critical resource
        allowed, risk, details = zt_manager.evaluate_access_request(
            "u1", device, "delete_production_db", "delete"
        )
        
        # Should be blocked
        assert allowed is False
        assert risk == RiskLevel.CRITICAL
