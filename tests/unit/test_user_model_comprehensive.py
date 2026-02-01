"""
Comprehensive User Model Unit Tests

Tests for User model methods and properties including:
- Password management (set, check, validation)
- Account locking and security
- MFA integration
- Email encryption/decryption
- Serialization (to_dict, from_dict)
- Password expiration
- Model representation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from models import User, db


class TestUserPasswordManagement:
    """Test user password setting and verification"""

    def test_set_password_creates_hash(self, app, client):
        """Test set_password creates password hash"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            user.set_password("SecureP@ssw0rd123")

            assert user.password_hash is not None
            assert user.password_hash != "SecureP@ssw0rd123"  # Should be hashed

    def test_set_password_updates_last_password_change(self, app, client):
        """Test set_password updates last_password_change"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            # Ensure we have a timezone-aware comparison baseline
            old_time = user.last_password_change.replace(tzinfo=None) if user.last_password_change else datetime.utcnow()

            user.set_password("SecureP@ssw0rd123")

            new_time = user.last_password_change.replace(tzinfo=None)
            assert new_time >= old_time

    def test_set_password_weak_password_raises_error(self, app, client):
        """Test set_password raises ValueError for weak passwords"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            with pytest.raises(ValueError, match="Password too weak"):
                user.set_password("weak")

    def test_set_password_without_uppercase_raises_error(self, app, client):
        """Test password without uppercase is rejected"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            with pytest.raises(ValueError):
                user.set_password("nouppercasep@ss123")

    def test_set_password_without_special_char_raises_error(self, app, client):
        """Test password without special character is rejected"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            with pytest.raises(ValueError):
                user.set_password("NoSpecialChar123")

    def test_check_password_correct(self, app, client):
        """Test check_password returns True for correct password"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            password = "SecureP@ssw0rd123"

            user.set_password(password)

            assert user.check_password(password) is True

    def test_check_password_incorrect(self, app, client):
        """Test check_password returns False for incorrect password"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            user.set_password("SecureP@ssw0rd123")

            assert user.check_password("WrongPassword123!") is False

    def test_check_password_no_hash(self, app, client):
        """Test check_password returns False when no password set"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            assert user.check_password("AnyPassword123!") is False

    def test_password_hash_different_for_same_password(self, app, client):
        """Test password hashing is salted (same password -> different hash)"""
        with app.app_context():
            user1 = User(username="user1", email="user1@example.com")
            user2 = User(username="user2", email="user2@example.com")
            password = "SameP@ssw0rd123"

            user1.set_password(password)
            user2.set_password(password)

            assert user1.password_hash != user2.password_hash


class TestUserAccountLocking:
    """Test account locking functionality"""

    def test_is_account_locked_when_not_locked(self, app, client):
        """Test is_account_locked returns False for unlocked account"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            assert user.is_account_locked() is False

    def test_is_account_locked_when_locked(self, app, client):
        """Test is_account_locked returns True when locked"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            # Use naive UTC to match default storage behavior if consistent, or aware if column implies it
            # But safer to just be consistent. Models use datetime.now(UTC)
            user.locked_until = datetime.now(datetime.timezone.utc) + timedelta(minutes=15)

            assert user.is_account_locked() is True

    def test_is_account_locked_after_lock_expires(self, app, client):
        """Test is_account_locked returns False after lock expires"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            # Lock expired 1 minute ago
            user.locked_until = datetime.now(datetime.timezone.utc) - timedelta(minutes=1)

            assert user.is_account_locked() is False

    def test_is_account_locked_at_exact_expiry(self, app, client):
        """Test is_account_locked at exact expiry time"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            # Set to expire "now"
            user.locked_until = datetime.now(datetime.timezone.utc)

            # Should be unlocked (locked_until <= now)
            assert user.is_account_locked() is False


class TestPasswordExpiration:
    """Test password expiration checking"""

    def test_is_password_expired_recent_password(self, app, client):
        """Test password changed recently is not expired"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.last_password_change = datetime.utcnow() - timedelta(days=30)

            assert user.is_password_expired() is False

    def test_is_password_expired_old_password(self, app, client):
        """Test old password is expired"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.last_password_change = datetime.utcnow() - timedelta(days=100)

            assert user.is_password_expired() is True

    def test_is_password_expired_never_changed(self, app, client):
        """Test password never changed is considered expired"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.last_password_change = None

            assert user.is_password_expired() is True


class TestMFAIntegration:
    """Test MFA integration"""

    def test_verify_totp_when_mfa_not_enabled(self, app, client):
        """Test TOTP verification returns False when MFA not enabled"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.mfa_enabled = False

            assert user.verify_totp("123456") is False

    def test_verify_totp_when_no_secret(self, app, client):
        """Test TOTP verification returns False when no secret"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.mfa_enabled = True
            user.mfa_secret = None

            assert user.verify_totp("123456") is False

    @patch('models.MFAManager.verify_totp')
    def test_verify_totp_calls_mfa_manager(self, mock_verify, app, client):
        """Test TOTP verification calls MFAManager"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.mfa_enabled = True
            user.mfa_secret = "TESTSECRET123"

            mock_verify.return_value = True

            result = user.verify_totp("123456")

            assert result is True
            mock_verify.assert_called_once_with("TESTSECRET123", "123456")

    @patch('models.MFAManager.verify_totp')
    def test_verify_totp_invalid_code(self, mock_verify, app, client):
        """Test TOTP verification with invalid code"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.mfa_enabled = True
            user.mfa_secret = "TESTSECRET123"

            mock_verify.return_value = False

            result = user.verify_totp("000000")

            assert result is False


class TestEmailEncryption:
    """Test email encryption/decryption"""

    @patch('extensions.encryption_manager')
    def test_email_getter_decrypts(self, mock_encryption, app, client):
        """Test email property decrypts stored email"""
        with app.app_context():
            mock_encryption.decrypt.return_value = "test@example.com"

            user = User(username="testuser")
            user._email = "encrypted_email_data"

            result = user.email

            assert result == "test@example.com"
            mock_encryption.decrypt.assert_called_once_with("encrypted_email_data", field_name='email')

    @patch('extensions.encryption_manager')
    def test_email_setter_encrypts(self, mock_encryption, app, client):
        """Test email property encrypts email"""
        with app.app_context():
            mock_encryption.encrypt.return_value = "encrypted_email_data"

            user = User(username="testuser")
            user.email = "test@example.com"

            assert user._email == "encrypted_email_data"
            mock_encryption.encrypt.assert_called_once_with("test@example.com", field_name='email')

    def test_email_setter_none_value(self, app, client):
        """Test setting email to None"""
        with app.app_context():
            user = User(username="testuser")
            user.email = None

            assert user._email is None

    def test_email_getter_none_value(self, app, client):
        """Test getting email when None"""
        with app.app_context():
            user = User(username="testuser")
            user._email = None

            assert user.email is None

    @patch('extensions.encryption_manager')
    def test_email_decryption_fallback(self, mock_encryption, app, client):
        """Test email decryption falls back to plaintext"""
        with app.app_context():
            mock_encryption.decrypt.side_effect = ValueError("Decryption failed")

            user = User(username="testuser")
            user._email = "plaintext@example.com"

            # Should fallback to plaintext
            result = user.email

            assert result == "plaintext@example.com"


class TestUserSerialization:
    """Test to_dict and from_dict methods"""

    def test_to_dict_includes_all_fields(self, app, client):
        """Test to_dict includes all expected fields"""
        with app.app_context():
            user = User(
                id=1,
                username="testuser",
                email="test@example.com",
                active=True,
                is_admin=False,
                role="user",
                mfa_enabled=True
            )
            user.last_successful_login = datetime.utcnow()

            result = user.to_dict()

            assert 'id' in result
            assert 'username' in result
            assert 'email' in result
            assert 'active' in result
            assert 'is_admin' in result
            assert 'role' in result
            assert 'mfa_enabled' in result
            assert 'created_at' in result
            assert 'last_login' in result

    def test_to_dict_values_correct(self, app, client):
        """Test to_dict returns correct values"""
        with app.app_context():
            user = User(
                id=123,
                username="johndo",
                email="john@example.com",
                active=True,
                is_admin=True,
                role="admin",
                mfa_enabled=False
            )

            result = user.to_dict()

            assert result['id'] == 123
            assert result['username'] == "johndoe"
            assert result['email'] == "john@example.com"
            assert result['active'] is True
            assert result['is_admin'] is True
            assert result['role'] == "admin"
            assert result['mfa_enabled'] is False

    def test_to_dict_datetime_iso_format(self, app, client):
        """Test to_dict converts datetime to ISO format"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.created_at = datetime(2024, 1, 15, 10, 30, 0)

            result = user.to_dict()

            assert isinstance(result['created_at'], str)
            assert 'T' in result['created_at']  # ISO format indicator

    def test_to_dict_none_datetime(self, app, client):
        """Test to_dict handles None datetime"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.last_successful_login = None

            result = user.to_dict()

            assert result['last_login'] is None

    def test_from_dict_creates_user(self, app, client):
        """Test from_dict creates User instance"""
        with app.app_context():
            data = {
                'username': 'newuser',
                'email': 'new@example.com',
                'role': 'analyst',
                'active': True,
                'is_admin': False
            }

            user = User.from_dict(data)

            assert isinstance(user, User)
            assert user.username == 'newuser'
            assert user.email == 'new@example.com'
            assert user.role == 'analyst'
            assert user.active is True
            assert user.is_admin is False

    def test_from_dict_partial_data(self, app, client):
        """Test from_dict with partial data"""
        with app.app_context():
            data = {
                'username': 'partial',
                'email': 'partial@example.com'
            }

            user = User.from_dict(data)

            assert user.username == 'partial'
            assert user.email == 'partial@example.com'
            # Other fields should be defaults or None

    def test_from_dict_ignores_extra_fields(self, app, client):
        """Test from_dict ignores fields not in whitelist"""
        with app.app_context():
            data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password_hash': 'should_be_ignored',
                'extra_field': 'should_be_ignored'
            }

            user = User.from_dict(data)

            assert user.username == 'testuser'
            assert user.password_hash is None  # Should not be set from dict

    def test_round_trip_serialization(self, app, client):
        """Test to_dict and from_dict round trip"""
        with app.app_context():
            original = User(
                username="roundtrip",
                email="roundtrip@example.com",
                role="developer",
                active=True,
                is_admin=False
            )

            # Serialize
            data = original.to_dict()

            # Deserialize
            recreated = User.from_dict(data)

            assert recreated.username == original.username
            assert recreated.email == original.email
            assert recreated.role == original.role
            assert recreated.active == original.active
            assert recreated.is_admin == original.is_admin


class TestUserRepresentation:
    """Test __repr__ method"""

    def test_repr_format(self, app, client):
        """Test __repr__ returns correct format"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            result = repr(user)

            assert result == '<User testuser>'

    def test_repr_different_usernames(self, app, client):
        """Test __repr__ with different usernames"""
        with app.app_context():
            user1 = User(username="alice", email="alice@example.com")
            user2 = User(username="bob", email="bob@example.com")

            assert repr(user1) == '<User alice>'
            assert repr(user2) == '<User bob>'


class TestUserDefaults:
    """Test default values"""

    def test_default_active_true(self, app, client):
        """Test user is active by default"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            db.session.add(user)
            db.session.commit()
            assert user.active is True

    def test_default_is_admin_false(self, app, client):
        """Test user is not admin by default"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            db.session.add(user)
            db.session.commit()
            assert user.is_admin is False

    def test_default_role_user(self, app, client):
        """Test default role is 'user'"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            db.session.add(user)
            db.session.commit()
            assert user.role == 'user'

    def test_default_mfa_disabled(self, app, client):
        """Test MFA is disabled by default"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            db.session.add(user)
            db.session.commit()
            assert user.mfa_enabled is False

    def test_default_failed_login_attempts_zero(self, app, client):
        """Test failed login attempts starts at zero"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            db.session.add(user)
            db.session.commit()
            assert user.failed_login_attempts == 0

    def test_default_created_at_set(self, app, client):
        """Test created_at is set on creation"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            db.session.add(user)
            db.session.commit()

            assert user.created_at is not None
            assert isinstance(user.created_at, datetime)


class TestUserValidation:
    """Test user field validation"""

    def test_username_required(self, app, client):
        """Test username is required"""
        with app.app_context():
            user = User(email="test@example.com")

            db.session.add(user)

            with pytest.raises(Exception):  # SQLAlchemy will raise integrity error
                db.session.commit()

    def test_email_required(self, app, client):
        """Test email is required"""
        with app.app_context():
            user = User(username="testuser")

            db.session.add(user)

            with pytest.raises(Exception):  # SQLAlchemy will raise integrity error
                db.session.commit()

    def test_username_unique(self, app, client):
        """Test username must be unique"""
        with app.app_context():
            user1 = User(username="duplicate", email="user1@example.com", role="user")
            user1.set_password("Password123!")
            db.session.add(user1)
            db.session.commit()

            user2 = User(username="duplicate", email="user2@example.com", role="user")

            db.session.add(user2)

            with pytest.raises(Exception):  # Unique constraint violation
                db.session.commit()


class TestUserEdgeCases:
    """Test edge cases"""

    def test_very_long_username(self, app, client):
        """Test username length limit"""
        with app.app_context():
            # Username column is String(64)
            long_username = "a" * 100

            user = User(username=long_username, email="test@example.com")
            db.session.add(user)

            # Should fail or truncate
            with pytest.raises(Exception):
                db.session.commit()

    def test_special_characters_in_username(self, app, client):
        """Test username with special characters"""
        with app.app_context():
            user = User(username="test_user-123", email="test@example.com", role="user")
            user.set_password("Password123!")

            db.session.add(user)
            db.session.commit()

            # Should succeed
            assert user.id is not None

    def test_unicode_in_username(self, app, client):
        """Test username with unicode characters"""
        with app.app_context():
            user = User(username="user_日本語", email="test@example.com", role="user")
            user.set_password("Password123!")

            db.session.add(user)
            db.session.commit()

            assert user.username == "user_日本語"

    def test_multiple_password_changes(self, app, client):
        """Test changing password multiple times"""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")

            user.set_password("FirstP@ssw0rd123")
            hash1 = user.password_hash

            user.set_password("SecondP@ssw0rd456")
            hash2 = user.password_hash

            user.set_password("ThirdP@ssw0rd789")
            hash3 = user.password_hash

            # All hashes should be different
            assert hash1 != hash2 != hash3

            # Only last password should work
            assert user.check_password("ThirdP@ssw0rd789") is True
            assert user.check_password("SecondP@ssw0rd456") is False
            assert user.check_password("FirstP@ssw0rd123") is False


class TestUserIntegration:
    """Integration tests for User model"""

    def test_complete_user_lifecycle(self, app, client):
        """Test complete user lifecycle"""
        with app.app_context():
            # Create user
            user = User(
                username="lifecycle_user",
                email="lifecycle@example.com",
                role="user"
            )

            # Set password
            user.set_password("InitialP@ssw0rd123")

            # Save to database
            db.session.add(user)
            db.session.commit()

            user_id = user.id

            # Retrieve from database
            retrieved = db.session.get(User, user_id)
            assert retrieved.username == "lifecycle_user"

            # Check password
            assert retrieved.check_password("InitialP@ssw0rd123") is True

            # Record failed login
            retrieved.failed_login_attempts = 1
            db.session.commit()

            # Record successful login
            retrieved.record_successful_login()
            db.session.refresh(retrieved)
            assert retrieved.failed_login_attempts == 0

            # Change password
            retrieved.set_password("NewP@ssw0rd456")
            db.session.commit()

            # Verify new password
            assert retrieved.check_password("NewP@ssw0rd456") is True

            # Serialize
            user_dict = retrieved.to_dict()
            assert user_dict['username'] == "lifecycle_user"

            # Cleanup
            db.session.delete(retrieved)
            db.session.commit()

    def test_user_with_mfa_workflow(self, app, client):
        """Test user with MFA enabled"""
        with app.app_context():
            user = User(
                username="mfa_user",
                email="mfa@example.com",
                role="user"
            )
            user.set_password("MfaP@ssw0rd123")
            user.mfa_enabled = True
            user.mfa_secret = "TESTSECRET"

            db.session.add(user)
            db.session.commit()

            user_id = user.id

            # Retrieve
            retrieved = db.session.get(User, user_id)

            assert retrieved.mfa_enabled is True
            assert retrieved.mfa_secret == "TESTSECRET"

            # Cleanup
            db.session.delete(retrieved)
            db.session.commit()
