"""
Tests for validation utilities
"""

import pytest
from utils.validators import isValidEmail, validatePassword, sanitizeInput


class TestEmailValidation:
    """Test email validation function"""

    def test_valid_emails(self):
        """Test that valid email addresses are accepted"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.com',
            'admin@test-domain.com',
        ]
        for email in valid_emails:
            assert isValidEmail(email) is True, f"Email {email} should be valid"

    def test_invalid_emails(self):
        """Test that invalid email addresses are rejected"""
        invalid_emails = [
            'invalid',
            'invalid@',
            '@invalid.com',
            'invalid@com',
            '',
            None,
        ]
        for email in invalid_emails:
            assert isValidEmail(email) is False, f"Email {email} should be invalid"


class TestPasswordValidation:
    """Test password validation function"""

    def test_strong_password(self):
        """Test that strong passwords are accepted"""
        result = validatePassword('StrongP@ss123')
        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_password_too_short(self):
        """Test that short passwords are rejected"""
        result = validatePassword('Ab1!')
        assert result['valid'] is False
        assert any('at least 8 characters' in error for error in result['errors'])

    def test_password_requires_uppercase(self):
        """Test that passwords require uppercase letters"""
        result = validatePassword('lowercase123!')
        assert result['valid'] is False
        assert any('uppercase letter' in error for error in result['errors'])

    def test_password_requires_lowercase(self):
        """Test that passwords require lowercase letters"""
        result = validatePassword('UPPERCASE123!')
        assert result['valid'] is False
        assert any('lowercase letter' in error for error in result['errors'])

    def test_password_requires_number(self):
        """Test that passwords require numbers"""
        result = validatePassword('NoNumbers!')
        assert result['valid'] is False
        assert any('number' in error for error in result['errors'])

    def test_password_requires_special_char(self):
        """Test that passwords require special characters"""
        result = validatePassword('NoSpecial123')
        assert result['valid'] is False
        assert any('special character' in error for error in result['errors'])

    def test_password_multiple_errors(self):
        """Test that weak passwords return multiple errors"""
        result = validatePassword('weak')
        assert result['valid'] is False
        assert len(result['errors']) > 1

    @pytest.mark.parametrize('password', [None, '', '   '])
    def test_password_handles_empty(self, password):
        """Test that empty passwords are rejected"""
        result = validatePassword(password)
        assert result['valid'] is False


class TestInputSanitization:
    """Test input sanitization function"""

    def test_escapes_html_tags(self):
        """Test that HTML tags are escaped"""
        result = sanitizeInput('<script>alert("XSS")</script>')
        assert '<script>' not in result
        assert '&lt;script&gt;' in result

    def test_escapes_quotes(self):
        """Test that quotes are escaped"""
        result = sanitizeInput('It\'s a "test"')
        assert '&#x27;' in result  # Escaped single quote
        assert '&quot;' in result  # Escaped double quote

    @pytest.mark.parametrize('input_val', [None, '', '   '])
    def test_handles_empty(self, input_val):
        """Test that empty inputs are handled"""
        result = sanitizeInput(input_val)
        assert isinstance(result, str)

    def test_preserves_safe_text(self):
        """Test that safe text is preserved"""
        safe_text = 'Safe text 123'
        assert sanitizeInput(safe_text) == safe_text
