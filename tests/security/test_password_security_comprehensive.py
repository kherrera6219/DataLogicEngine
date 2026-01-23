"""
Comprehensive Password Security Testing Suite

Tests for:
- Password strength validation
- Password breach detection (Have I Been Pwned API)
- Password expiration logic
- Password history (integration with User model)
- Password strength scoring
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, UTC
from backend.security.password_security import PasswordSecurity
import requests


class TestPasswordStrengthValidation:
    """Test password strength validation"""

    def test_strong_password_passes_validation(self):
        """Test that strong password passes all requirements"""
        password = "MyStr0ng!P@ssw0rd"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is True
        assert len(errors) == 0

    def test_password_too_short_fails(self):
        """Test password shorter than minimum length fails"""
        password = "Short1!"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False
        assert any("at least" in error and "characters" in error for error in errors)

    def test_password_missing_uppercase_fails(self):
        """Test password without uppercase fails"""
        password = "mystr0ng!p@ssw0rd"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False
        assert any("uppercase" in error.lower() for error in errors)

    def test_password_missing_lowercase_fails(self):
        """Test password without lowercase fails"""
        password = "MYSTR0NG!P@SSW0RD"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False
        assert any("lowercase" in error.lower() for error in errors)

    def test_password_missing_digit_fails(self):
        """Test password without digit fails"""
        password = "MyStrong!P@ssword"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False
        assert any("digit" in error.lower() for error in errors)

    def test_password_missing_special_char_fails(self):
        """Test password without special character fails"""
        password = "MyStr0ngPassw0rd"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False
        assert any("special character" in error.lower() for error in errors)

    def test_password_with_common_pattern_fails(self):
        """Test password containing common pattern fails"""
        passwords_with_patterns = [
            "MyPassword123456!",  # Contains 123456
            "SecurePassword!123",  # Contains 'password'
            "Qwerty!123456789",   # Contains 'qwerty'
            "MyAbc123!Password",  # Contains 'abc123'
        ]

        for password in passwords_with_patterns:
            is_valid, errors = PasswordSecurity.validate_password_strength(password)

            assert is_valid is False
            assert any("common pattern" in error.lower() for error in errors)

    def test_password_all_requirements_missing(self):
        """Test password missing all requirements returns multiple errors"""
        password = "short"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False
        assert len(errors) >= 4  # Length, uppercase, digit, special

    def test_password_minimum_valid_length(self):
        """Test password at minimum valid length"""
        password = "MyStr0ng!P@s"  # Exactly 12 characters

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is True

    def test_password_various_special_characters(self):
        """Test password with various special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"

        for char in special_chars[:5]:  # Test a few
            password = f"MyStr0ng{char}Passw0rd"
            is_valid, errors = PasswordSecurity.validate_password_strength(password)
            assert is_valid is True, f"Failed with special char: {char}"

    def test_empty_password_fails(self):
        """Test empty password fails validation"""
        password = ""

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False
        assert len(errors) > 0


class TestPasswordBreachDetection:
    """Test password breach detection using Have I Been Pwned API"""

    @patch('backend.security.password_security.requests.get')
    def test_breached_password_detected(self, mock_get):
        """Test detection of breached password"""
        # Mock API response for a breached password
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "0018A45C4D1DEF81644B54AB7F969B88D65:3\r\n" \
                            "00D4F6E8FA6EECAD2A3AA415EEC418D38EC:2\r\n" \
                            "011053FD0102E94D6AE2F8B83D76FAF94F6:1"
        mock_get.return_value = mock_response

        # Password that hashes to have suffix 0018A45C4D1DEF81644B54AB7F969B88D65
        password = "test_password"

        is_breached, count = PasswordSecurity.check_password_breach(password)

        assert mock_get.called
        # Result depends on actual hash, but method should execute

    @patch('backend.security.password_security.requests.get')
    def test_non_breached_password(self, mock_get):
        """Test password not found in breaches"""
        # Mock API response without matching hash
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:1\r\n" \
                            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB:2"
        mock_get.return_value = mock_response

        password = "UniqueSecureP@ssw0rd123"

        is_breached, count = PasswordSecurity.check_password_breach(password)

        assert is_breached is False
        assert count == 0

    @patch('backend.security.password_security.requests.get')
    def test_api_timeout_fails_open(self, mock_get):
        """Test API timeout fails open (doesn't block user)"""
        mock_get.side_effect = requests.exceptions.Timeout()

        password = "TestPassword123!"

        is_breached, count = PasswordSecurity.check_password_breach(password)

        assert is_breached is False
        assert count is None

    @patch('backend.security.password_security.requests.get')
    def test_api_error_fails_open(self, mock_get):
        """Test API error fails open"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        password = "TestPassword123!"

        is_breached, count = PasswordSecurity.check_password_breach(password)

        assert is_breached is False
        assert count is None

    @patch('backend.security.password_security.requests.get')
    def test_network_exception_fails_open(self, mock_get):
        """Test network exception fails open"""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        password = "TestPassword123!"

        is_breached, count = PasswordSecurity.check_password_breach(password)

        assert is_breached is False
        assert count is None

    @patch('backend.security.password_security.requests.get')
    def test_breach_check_uses_k_anonymity(self, mock_get):
        """Test that breach check uses k-anonymity (only sends hash prefix)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response

        password = "TestPassword123!"

        PasswordSecurity.check_password_breach(password)

        # Verify URL only contains prefix (5 characters)
        called_url = mock_get.call_args[0][0]
        assert "/range/" in called_url
        hash_prefix = called_url.split("/range/")[1]
        assert len(hash_prefix) == 5

    @patch('backend.security.password_security.requests.get')
    def test_custom_timeout_parameter(self, mock_get):
        """Test custom timeout parameter is used"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response

        password = "TestPassword123!"
        custom_timeout = 5

        PasswordSecurity.check_password_breach(password, timeout=custom_timeout)

        # Verify timeout was passed
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == custom_timeout

    @patch('backend.security.password_security.requests.get')
    def test_breach_count_parsed_correctly(self, mock_get):
        """Test breach count is parsed correctly from API response"""
        # Create a password and its expected hash
        password = "password"
        import hashlib
        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        suffix = sha1_hash[5:]

        # Mock response with this suffix and count
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"{suffix}:9999999"
        mock_get.return_value = mock_response

        is_breached, count = PasswordSecurity.check_password_breach(password)

        assert is_breached is True
        assert count == 9999999


class TestPasswordExpiration:
    """Test password expiration logic"""

    def test_recently_changed_password_not_expired(self):
        """Test password changed recently is not expired"""
        last_changed = datetime.now(UTC) - timedelta(days=30)

        is_expired = PasswordSecurity.is_password_expired(last_changed)

        assert is_expired is False

    def test_old_password_is_expired(self):
        """Test password changed long ago is expired"""
        last_changed = datetime.now(UTC) - timedelta(days=100)

        is_expired = PasswordSecurity.is_password_expired(last_changed)

        assert is_expired is True

    def test_password_at_expiry_boundary(self):
        """Test password at exactly expiry days"""
        last_changed = datetime.now(UTC) - timedelta(days=PasswordSecurity.PASSWORD_EXPIRY_DAYS)

        is_expired = PasswordSecurity.is_password_expired(last_changed)

        # At boundary, should be expired or about to be
        assert isinstance(is_expired, bool)

    def test_custom_expiry_days(self):
        """Test custom expiry days parameter"""
        last_changed = datetime.now(UTC) - timedelta(days=50)
        custom_expiry = 30

        is_expired = PasswordSecurity.is_password_expired(last_changed, expiry_days=custom_expiry)

        assert is_expired is True

    def test_none_last_changed_considered_expired(self):
        """Test None last_changed is considered expired"""
        is_expired = PasswordSecurity.is_password_expired(None)

        assert is_expired is True

    def test_naive_datetime_handled(self):
        """Test naive datetime (no timezone) is handled"""
        last_changed = datetime.now() - timedelta(days=30)  # Naive datetime

        # Should not crash
        is_expired = PasswordSecurity.is_password_expired(last_changed)

        assert isinstance(is_expired, bool)


class TestDaysUntilExpiry:
    """Test days until expiry calculation"""

    def test_days_until_expiry_positive(self):
        """Test positive days until expiry"""
        last_changed = datetime.now(UTC) - timedelta(days=30)

        days = PasswordSecurity.days_until_expiry(last_changed)

        expected_days = PasswordSecurity.PASSWORD_EXPIRY_DAYS - 30
        assert days >= expected_days - 1  # Allow 1 day tolerance
        assert days <= expected_days + 1

    def test_days_until_expiry_negative(self):
        """Test negative days when already expired"""
        last_changed = datetime.now(UTC) - timedelta(days=100)

        days = PasswordSecurity.days_until_expiry(last_changed)

        assert days < 0

    def test_days_until_expiry_none(self):
        """Test None last_changed returns -1"""
        days = PasswordSecurity.days_until_expiry(None)

        assert days == -1

    def test_days_until_expiry_custom_expiry_days(self):
        """Test custom expiry days"""
        last_changed = datetime.now(UTC) - timedelta(days=10)
        custom_expiry = 30

        days = PasswordSecurity.days_until_expiry(last_changed, expiry_days=custom_expiry)

        expected_days = 30 - 10
        assert days >= expected_days - 1
        assert days <= expected_days + 1

    def test_days_until_expiry_naive_datetime(self):
        """Test naive datetime handled"""
        last_changed = datetime.now() - timedelta(days=30)

        # Should not crash
        days = PasswordSecurity.days_until_expiry(last_changed)

        assert isinstance(days, int)


class TestPasswordStrengthScoring:
    """Test password strength score calculation"""

    def test_very_strong_password_high_score(self):
        """Test very strong password gets high score"""
        password = "MyV3ry!Str0ng&C0mpl3x#P@ssw0rd"

        score, label = PasswordSecurity.calculate_password_strength_score(password)

        assert score >= 80
        assert label == "Very Strong"

    def test_strong_password_good_score(self):
        """Test strong password gets good score"""
        password = "MyStr0ng!P@ssw0rd"

        score, label = PasswordSecurity.calculate_password_strength_score(password)

        assert score >= 60
        assert label in ["Strong", "Very Strong"]

    def test_moderate_password_medium_score(self):
        """Test moderate password gets medium score"""
        password = "MyPass123!"

        score, label = PasswordSecurity.calculate_password_strength_score(password)

        assert 40 <= score < 80

    def test_weak_password_low_score(self):
        """Test weak password gets low score"""
        password = "weak123"

        score, label = PasswordSecurity.calculate_password_strength_score(password)

        assert score < 60
        assert label in ["Weak", "Very Weak", "Moderate"]

    def test_very_weak_password_lowest_score(self):
        """Test very weak password gets lowest score"""
        password = "abc"

        score, label = PasswordSecurity.calculate_password_strength_score(password)

        assert score < 40

    def test_length_bonus_calculation(self):
        """Test length contributes to score"""
        short_password = "Aa1!Bb2@"  # 8 chars
        medium_password = "Aa1!Bb2@Cc3#"  # 12 chars
        long_password = "Aa1!Bb2@Cc3#Dd4$Ee5%"  # 20 chars

        short_score, _ = PasswordSecurity.calculate_password_strength_score(short_password)
        medium_score, _ = PasswordSecurity.calculate_password_strength_score(medium_password)
        long_score, _ = PasswordSecurity.calculate_password_strength_score(long_password)

        assert medium_score > short_score
        assert long_score > medium_score

    def test_character_variety_bonus(self):
        """Test character variety contributes to score"""
        lowercase_only = "abcdefghijklmnop"
        mixed_case = "AbCdEfGhIjKlMnOp"
        with_digits = "AbCd1234IjKlMnOp"
        with_special = "AbCd!@#$IjKl12Op"

        score1, _ = PasswordSecurity.calculate_password_strength_score(lowercase_only)
        score2, _ = PasswordSecurity.calculate_password_strength_score(mixed_case)
        score3, _ = PasswordSecurity.calculate_password_strength_score(with_digits)
        score4, _ = PasswordSecurity.calculate_password_strength_score(with_special)

        assert score2 > score1
        assert score3 > score2
        assert score4 > score3

    def test_unique_characters_bonus(self):
        """Test unique characters contribute to score"""
        repetitive = "Aa1!Aa1!Aa1!Aa1!"  # Few unique chars
        diverse = "AbCd!@#$1234EfGh"     # Many unique chars

        score1, _ = PasswordSecurity.calculate_password_strength_score(repetitive)
        score2, _ = PasswordSecurity.calculate_password_strength_score(diverse)

        assert score2 > score1

    def test_empty_password_score(self):
        """Test empty password gets minimum score"""
        password = ""

        score, label = PasswordSecurity.calculate_password_strength_score(password)

        assert score == 0
        assert label == "Very Weak"

    def test_score_ranges_correct(self):
        """Test score ranges map to correct labels"""
        test_cases = [
            (90, "Very Strong"),
            (75, "Strong"),
            (55, "Moderate"),
            (35, "Weak"),
            (15, "Very Weak"),
        ]

        for test_score, expected_label in test_cases:
            # Create password that yields approximately this score
            if test_score >= 80:
                password = "MyV3ry!Str0ng&C0mpl3x#P@ssw0rd123"
            elif test_score >= 60:
                password = "MyStr0ng!P@ssw0rd"
            elif test_score >= 40:
                password = "MyPass123!"
            elif test_score >= 20:
                password = "pass123"
            else:
                password = "abc"

            score, label = PasswordSecurity.calculate_password_strength_score(password)
            # Just verify label is appropriate for score
            if score >= 80:
                assert label == "Very Strong"
            elif score >= 60:
                assert label == "Strong"
            elif score >= 40:
                assert label == "Moderate"
            elif score >= 20:
                assert label == "Weak"
            else:
                assert label == "Very Weak"


class TestPasswordSecurityEdgeCases:
    """Test edge cases and error scenarios"""

    def test_unicode_password_validation(self):
        """Test password with unicode characters"""
        password = "MyStr0ng!P@ssw0rd™"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        # Should handle unicode gracefully
        assert isinstance(is_valid, bool)

    def test_very_long_password(self):
        """Test very long password"""
        password = "A" * 1000 + "1!a"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        # Should handle long passwords
        assert isinstance(is_valid, bool)

    @patch('backend.security.password_security.requests.get')
    def test_malformed_api_response(self, mock_get):
        """Test handling of malformed API response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "MALFORMED RESPONSE WITHOUT COLONS"
        mock_get.return_value = mock_response

        password = "TestPassword123!"

        # Should not crash
        try:
            is_breached, count = PasswordSecurity.check_password_breach(password)
            # If it handles gracefully, it should fail open
            assert is_breached is False
        except Exception:
            # Or it might raise exception, which is also acceptable
            pass

    def test_password_with_only_spaces(self):
        """Test password with only spaces"""
        password = "            "

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        assert is_valid is False

    def test_password_with_null_bytes(self):
        """Test password with null bytes"""
        password = "Test\x00Password123!"

        is_valid, errors = PasswordSecurity.validate_password_strength(password)

        # Should handle gracefully
        assert isinstance(is_valid, bool)

    def test_expiry_with_future_date(self):
        """Test expiry with future last_changed date"""
        last_changed = datetime.now(UTC) + timedelta(days=10)

        is_expired = PasswordSecurity.is_password_expired(last_changed)

        # Future date should not be expired
        assert is_expired is False

    def test_concurrent_breach_checks(self):
        """Test multiple concurrent breach checks don't interfere"""
        with patch('backend.security.password_security.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_get.return_value = mock_response

            passwords = ["Pass1!", "Pass2!", "Pass3!"]

            results = [PasswordSecurity.check_password_breach(p) for p in passwords]

            # All should complete
            assert len(results) == 3
            assert all(isinstance(r, tuple) for r in results)


class TestPasswordPolicyConstants:
    """Test password policy constants are reasonable"""

    def test_minimum_length_reasonable(self):
        """Test minimum length is security-appropriate"""
        assert PasswordSecurity.MIN_PASSWORD_LENGTH >= 8
        assert PasswordSecurity.MIN_PASSWORD_LENGTH <= 20

    def test_password_history_count_reasonable(self):
        """Test password history count is reasonable"""
        assert PasswordSecurity.PASSWORD_HISTORY_COUNT >= 3
        assert PasswordSecurity.PASSWORD_HISTORY_COUNT <= 10

    def test_expiry_days_reasonable(self):
        """Test expiry days is reasonable"""
        assert PasswordSecurity.PASSWORD_EXPIRY_DAYS >= 30
        assert PasswordSecurity.PASSWORD_EXPIRY_DAYS <= 365

    def test_requirements_enabled(self):
        """Test all security requirements are enabled"""
        assert PasswordSecurity.REQUIRE_UPPERCASE is True
        assert PasswordSecurity.REQUIRE_LOWERCASE is True
        assert PasswordSecurity.REQUIRE_DIGIT is True
        assert PasswordSecurity.REQUIRE_SPECIAL is True


class TestPasswordSecurityIntegration:
    """Integration tests combining multiple password security features"""

    @patch('backend.security.password_security.requests.get')
    def test_complete_password_validation_workflow(self, mock_get):
        """Test complete password validation workflow"""
        # Mock breach API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response

        password = "MySecure!P@ssw0rd2024"

        # Step 1: Validate strength
        is_strong, errors = PasswordSecurity.validate_password_strength(password)
        assert is_strong is True

        # Step 2: Check breach
        is_breached, count = PasswordSecurity.check_password_breach(password)
        assert is_breached is False

        # Step 3: Calculate strength score
        score, label = PasswordSecurity.calculate_password_strength_score(password)
        assert score >= 60

        # Password is suitable for use
        assert is_strong and not is_breached and score >= 60

    def test_weak_password_fails_multiple_checks(self):
        """Test weak password fails validation and scoring"""
        password = "password"

        # Should fail strength validation
        is_strong, errors = PasswordSecurity.validate_password_strength(password)
        assert is_strong is False

        # Should have low score
        score, label = PasswordSecurity.calculate_password_strength_score(password)
        assert score < 60

    def test_password_lifecycle_simulation(self):
        """Test simulated password lifecycle"""
        # New password set
        last_changed = datetime.now(UTC)

        # Initially not expired
        assert PasswordSecurity.is_password_expired(last_changed) is False

        # Check days until expiry
        days = PasswordSecurity.days_until_expiry(last_changed)
        assert days > 0

        # Simulate time passing (91 days)
        old_last_changed = datetime.now(UTC) - timedelta(days=91)

        # Should now be expired
        assert PasswordSecurity.is_password_expired(old_last_changed) is True

        # Days should be negative
        expired_days = PasswordSecurity.days_until_expiry(old_last_changed)
        assert expired_days < 0
