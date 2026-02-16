
from unittest.mock import Mock, patch

# Import Targets
from backend.security.api_security import RequestSigner
from backend.security.password_security import PasswordSecurity
from backend.security.data_classification import DataClassifier, DataClassification, PIIType

# -----------------------------------------------------------------------------
# Request Signer Tests
# -----------------------------------------------------------------------------

class TestRequestSigner:
    def setup_method(self):
        self.audit_logger = Mock()
        self.signer = RequestSigner(audit_logger=self.audit_logger)
        self.api_key = "test_key"
        self.api_secret = "test_secret"

    def test_sign_and_verify_success(self):
        method = "POST"
        path = "/api/data"
        body = '{"foo": "bar"}'
        
        # Sign
        headers = self.signer.sign_request(method, path, body, self.api_key, self.api_secret)
        
        # Verify
        valid, error = self.signer.verify_request(
            method=method,
            path=path,
            body=body,
            api_key_id=headers["X-API-Key"],
            api_secret=self.api_secret,
            timestamp=headers["X-API-Timestamp"],
            signature=headers["X-API-Signature"]
        )
        assert valid is True
        assert error is None

    def test_verify_fails_tampered_body(self):
        method = "POST"
        path = "/api/data"
        body = '{"foo": "bar"}'
        headers = self.signer.sign_request(method, path, body, self.api_key, self.api_secret)
        
        # Tamper body
        valid, error = self.signer.verify_request(
            method=method,
            path=path,
            body='{"foo": "baz"}', # changed
            api_key_id=headers["X-API-Key"],
            api_secret=self.api_secret,
            timestamp=headers["X-API-Timestamp"],
            signature=headers["X-API-Signature"]
        )
        assert valid is False
        assert "Invalid signature" in error

    def test_verify_fails_replay_attack(self):
        method = "GET"
        path = "/api/status"
        headers = self.signer.sign_request(method, path, None, self.api_key, self.api_secret)
        
        # First verification (stores nonce if provided, but sign_request doesn't add nonce by default in output dict?)
        # Let's verify nonce logic if we manually add a nonce.
        nonce = "unique-nonce-123"
        
        # Verify first time
        valid, _ = self.signer.verify_request(
            method, path, None, headers["X-API-Key"], self.api_secret, 
            headers["X-API-Timestamp"], headers["X-API-Signature"], nonce=nonce
        )
        assert valid is True
        
        # Verify second time (Replay)
        valid, error = self.signer.verify_request(
            method, path, None, headers["X-API-Key"], self.api_secret, 
            headers["X-API-Timestamp"], headers["X-API-Signature"], nonce=nonce
        )
        assert valid is False
        assert "replay attack detected" in str(error)

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

# -----------------------------------------------------------------------------
# Data Classification Tests
# -----------------------------------------------------------------------------

class TestDataClassification:
    def setup_method(self):
        self.logger = Mock()
        self.classifier = DataClassifier(audit_logger=self.logger)

    def test_pii_detection_ssn(self):
        # Pattern match
        text = "User SSN is 123-45-6789 test"
        detected = self.classifier.detect_pii(text)
        assert PIIType.SSN in detected

    def test_pii_detection_email(self):
        text = "Contact me at user@example.com"
        detected = self.classifier.detect_pii(text)
        assert PIIType.EMAIL in detected

    def test_classify_field_restricted(self):
        # Keyword based
        cls = self.classifier.classify_field("social_security_number", "anything")
        assert cls == DataClassification.RESTRICTED

    def test_classify_dict(self):
        data = {
            "user_email": "test@test.com",
            "project_name": "Project Alpha",
            "public_info": "Hello"
        }
        res = self.classifier.classify_dict(data)
        
        # Emails are PII -> Restricted? Or Confidential?
        # classify_field uses regex/keywords. 'user_email' contains 'email'.
        # 'email' is in PII_FIELD_NAMES but classify_field logic for keywords check:
        # restricted_keywords misses 'email'.
        # confidential_keywords misses 'email'.
        # internal_keywords misses 'email'.
        # But classify_field checks `detect_pii(value)`.
        # value "test@test.com" triggers PII (EMAIL).
        # if pii_detected -> RESTRICTED (Line 201).
        
        assert res["user_email"] == DataClassification.RESTRICTED
        assert res["project_name"] == DataClassification.INTERNAL

    def test_mask_pii(self):
        text = "Call 555-123-4567 or email foo@bar.com"
        masked = self.classifier.mask_pii(text)
        assert "555-123-4567" not in masked
        assert "***-***" in masked # Phone mask pattern
        assert "foo@bar.com" not in masked
        assert "***@" in masked
