
from unittest.mock import Mock, patch

# Import Targets
from backend.security.password_security import PasswordSecurity

# -----------------------------------------------------------------------------
# Password Security Tests
# -----------------------------------------------------------------------------

class TestPasswordSecurity:
    
    def test_password_strength_validation(self):
        # Weak
        valid, errors = PasswordSecurity.validate_password_strength("weak")
        assert valid is False
        assert len(errors) > 0
        
        # Strong
        strong_pass = "StrongPass123!@#"
        valid, errors = PasswordSecurity.validate_password_strength(strong_pass)
        assert valid is True
        assert len(errors) == 0

    @patch('backend.security.password_security.requests.get')
    def test_breach_check_safe(self, mock_get):
        # Mock HIBP API returning Not Found (safe)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "AB123:5\r\nCD456:1" # Fakes
        mock_get.return_value = mock_response
        
        # This password should NOT match the fake hashes
        is_breached, count = PasswordSecurity.check_password_breach("MySecurePassword123!")
        assert is_breached is False

    @patch('backend.security.password_security.requests.get')
    def test_breach_check_pwned(self, mock_get):
        # Calculate hash prefix for "password"
        # SHA1("password") = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
        # Prefix: 5BAA6. Suffix: 1E4C9...
        
        mock_response = Mock()
        mock_response.status_code = 200
        # Return a matching suffix
        target_suffix = "1E4C9B93F3F0682250B6CF8331B7EE68FD8"
        mock_response.text = f"OtherHash:1\r\n{target_suffix}:5000"
        mock_get.return_value = mock_response
        
        is_breached, count = PasswordSecurity.check_password_breach("password")
        assert is_breached is True
        assert count == 5000
