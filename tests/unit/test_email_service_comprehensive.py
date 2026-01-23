"""
Comprehensive Email Service Testing Suite

Tests for email functionality covering:
- Basic email sending
- Async email sending
- Template rendering
- Password reset emails
- Verification emails
- Welcome emails
- Notification emails
- Error handling and retry logic
- Email queue management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from flask import Flask
from flask_mail import Message
import threading

from backend.email_service import (
    init_mail,
    send_email,
    send_async_email,
    send_password_reset_email,
    send_verification_email,
    send_welcome_email,
    send_notification_email
)


@pytest.fixture
def test_app():
    """Create test Flask app with email configuration"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['MAIL_SERVER'] = 'smtp.test.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'test@test.com'
    app.config['MAIL_PASSWORD'] = 'test_password'
    app.config['MAIL_DEFAULT_SENDER'] = 'noreply@test.com'
    app.config['MAIL_SUPPRESS_SEND'] = True  # Don't actually send emails in tests

    return app


@pytest.fixture
def initialized_mail(test_app):
    """Initialize mail with test app"""
    init_mail(test_app)
    return test_app


class TestEmailInitialization:
    """Test email service initialization"""

    def test_init_mail_configures_server(self):
        """Test mail initialization sets server configuration"""
        app = Flask(__name__)
        app.config['MAIL_SERVER'] = 'custom.smtp.com'

        init_mail(app)

        assert app.config['MAIL_SERVER'] == 'custom.smtp.com'

    def test_init_mail_sets_defaults(self):
        """Test mail initialization sets default values"""
        app = Flask(__name__)

        init_mail(app)

        assert 'MAIL_SERVER' in app.config
        assert 'MAIL_PORT' in app.config
        assert 'MAIL_DEFAULT_SENDER' in app.config

    def test_init_mail_from_environment(self, monkeypatch):
        """Test mail initialization from environment variables"""
        monkeypatch.setenv('MAIL_SERVER', 'env.smtp.com')
        monkeypatch.setenv('MAIL_PORT', '465')
        monkeypatch.setenv('MAIL_USERNAME', 'env_user')

        app = Flask(__name__)
        init_mail(app)

        assert app.config['MAIL_SERVER'] == 'env.smtp.com'
        assert app.config['MAIL_PORT'] == 465
        assert app.config['MAIL_USERNAME'] == 'env_user'

    def test_init_mail_tls_configuration(self):
        """Test TLS/SSL configuration"""
        app = Flask(__name__)
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False

        init_mail(app)

        assert app.config['MAIL_USE_TLS'] is True
        assert app.config['MAIL_USE_SSL'] is False


class TestBasicEmailSending:
    """Test basic email sending functionality"""

    @patch('backend.email_service.mail.send')
    def test_send_email_with_plain_body(self, mock_send, initialized_mail):
        """Test sending email with plain text body"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test Subject",
                recipients=["test@example.com"],
                body="Test body",
                async_send=False
            )

            assert result is True
            mock_send.assert_called_once()

    @patch('backend.email_service.mail.send')
    def test_send_email_with_html(self, mock_send, initialized_mail):
        """Test sending email with HTML body"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test Subject",
                recipients=["test@example.com"],
                html="<h1>Test HTML</h1>",
                async_send=False
            )

            assert result is True
            mock_send.assert_called_once()

    @patch('backend.email_service.mail.send')
    def test_send_email_to_multiple_recipients(self, mock_send, initialized_mail):
        """Test sending email to multiple recipients"""
        with initialized_mail.app_context():
            recipients = ["user1@test.com", "user2@test.com", "user3@test.com"]

            result = send_email(
                subject="Test",
                recipients=recipients,
                body="Test",
                async_send=False
            )

            assert result is True
            mock_send.assert_called_once()

            # Verify Message was created with correct recipients
            call_args = mock_send.call_args[0][0]
            assert len(call_args.recipients) == 3

    def test_send_email_requires_content(self, initialized_mail):
        """Test sending email requires either body, html, or template"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=["test@test.com"],
                async_send=False
            )

            assert result is False

    @patch('backend.email_service.render_template')
    @patch('backend.email_service.mail.send')
    def test_send_email_with_template(self, mock_send, mock_render, initialized_mail):
        """Test sending email with template"""
        mock_render.return_value = "<html>Rendered content</html>"

        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=["test@test.com"],
                template="email/test.html",
                template_data={"key": "value"},
                async_send=False
            )

            assert result is True
            mock_render.assert_called_once_with("email/test.html", key="value")

    @patch('backend.email_service.mail.send')
    def test_send_email_with_body_and_html(self, mock_send, initialized_mail):
        """Test email can have both plain and HTML body"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=["test@test.com"],
                body="Plain text",
                html="<p>HTML text</p>",
                async_send=False
            )

            assert result is True


class TestAsyncEmailSending:
    """Test asynchronous email sending"""

    @patch('backend.email_service.Thread')
    @patch('backend.email_service.mail.send')
    def test_send_email_async_creates_thread(self, mock_send, mock_thread, initialized_mail):
        """Test async email sending creates thread"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=["test@test.com"],
                body="Test",
                async_send=True
            )

            assert result is True
            mock_thread.assert_called_once()
            # Verify thread was started
            mock_thread.return_value.start.assert_called_once()

    @patch('backend.email_service.mail.send')
    def test_send_async_email_in_app_context(self, mock_send, initialized_mail):
        """Test async email sends within app context"""
        with initialized_mail.app_context():
            msg = Message(
                subject="Test",
                recipients=["test@test.com"],
                body="Test body"
            )

            send_async_email(initialized_mail, msg)

            mock_send.assert_called_once_with(msg)

    @patch('backend.email_service.mail.send')
    def test_send_async_email_handles_errors(self, mock_send, initialized_mail):
        """Test async email handles sending errors"""
        mock_send.side_effect = Exception("SMTP error")

        with initialized_mail.app_context():
            msg = Message(
                subject="Test",
                recipients=["test@test.com"],
                body="Test"
            )

            # Should not raise exception
            send_async_email(initialized_mail, msg)


class TestPasswordResetEmail:
    """Test password reset email functionality"""

    @patch('backend.email_service.send_email')
    def test_send_password_reset_email(self, mock_send_email, initialized_mail):
        """Test sending password reset email"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            result = send_password_reset_email(
                user_email="user@test.com",
                reset_token="abc123",
                reset_url="http://test.com/reset"
            )

            assert result is True
            mock_send_email.assert_called_once()

    @patch('backend.email_service.send_email')
    def test_password_reset_email_subject(self, mock_send_email, initialized_mail):
        """Test password reset email has correct subject"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_password_reset_email(
                user_email="user@test.com",
                reset_token="abc123",
                reset_url="http://test.com/reset"
            )

            call_kwargs = mock_send_email.call_args[1]
            assert "Password Reset" in call_kwargs['subject']

    @patch('backend.email_service.send_email')
    def test_password_reset_email_includes_token(self, mock_send_email, initialized_mail):
        """Test password reset email includes token and URL"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_password_reset_email(
                user_email="user@test.com",
                reset_token="abc123token",
                reset_url="http://test.com/reset"
            )

            call_kwargs = mock_send_email.call_args[1]
            template_data = call_kwargs['template_data']

            assert template_data['reset_token'] == "abc123token"
            assert template_data['reset_url'] == "http://test.com/reset"

    @patch('backend.email_service.send_email')
    def test_password_reset_email_includes_expiry(self, mock_send_email, initialized_mail):
        """Test password reset email includes expiry information"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_password_reset_email(
                user_email="user@test.com",
                reset_token="abc123",
                reset_url="http://test.com/reset"
            )

            call_kwargs = mock_send_email.call_args[1]
            template_data = call_kwargs['template_data']

            assert 'expires_in' in template_data


class TestVerificationEmail:
    """Test account verification email"""

    @patch('backend.email_service.send_email')
    def test_send_verification_email(self, mock_send_email, initialized_mail):
        """Test sending verification email"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            result = send_verification_email(
                user_email="user@test.com",
                verification_url="http://test.com/verify"
            )

            assert result is True
            mock_send_email.assert_called_once()

    @patch('backend.email_service.send_email')
    def test_verification_email_subject(self, mock_send_email, initialized_mail):
        """Test verification email has correct subject"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_verification_email(
                user_email="user@test.com",
                verification_url="http://test.com/verify"
            )

            call_kwargs = mock_send_email.call_args[1]
            assert "Verify" in call_kwargs['subject']

    @patch('backend.email_service.send_email')
    def test_verification_email_includes_url(self, mock_send_email, initialized_mail):
        """Test verification email includes verification URL"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_verification_email(
                user_email="user@test.com",
                verification_url="http://test.com/verify?token=xyz"
            )

            call_kwargs = mock_send_email.call_args[1]
            template_data = call_kwargs['template_data']

            assert template_data['verification_url'] == "http://test.com/verify?token=xyz"


class TestWelcomeEmail:
    """Test welcome email"""

    @patch('backend.email_service.send_email')
    def test_send_welcome_email(self, mock_send_email, initialized_mail):
        """Test sending welcome email"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            result = send_welcome_email(
                user_email="newuser@test.com",
                username="newuser"
            )

            assert result is True
            mock_send_email.assert_called_once()

    @patch('backend.email_service.send_email')
    def test_welcome_email_subject(self, mock_send_email, initialized_mail):
        """Test welcome email has correct subject"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_welcome_email(
                user_email="newuser@test.com",
                username="newuser"
            )

            call_kwargs = mock_send_email.call_args[1]
            assert "Welcome" in call_kwargs['subject']

    @patch('backend.email_service.send_email')
    def test_welcome_email_includes_username(self, mock_send_email, initialized_mail):
        """Test welcome email includes username"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_welcome_email(
                user_email="newuser@test.com",
                username="johndoe"
            )

            call_kwargs = mock_send_email.call_args[1]
            template_data = call_kwargs['template_data']

            assert template_data['username'] == "johndoe"


class TestNotificationEmail:
    """Test notification emails"""

    @patch('backend.email_service.send_email')
    def test_send_notification_email(self, mock_send_email, initialized_mail):
        """Test sending notification email"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            result = send_notification_email(
                user_email="user@test.com",
                notification_type="alert",
                title="Security Alert",
                message="Suspicious activity detected"
            )

            assert result is True
            mock_send_email.assert_called_once()

    @patch('backend.email_service.send_email')
    def test_notification_email_includes_type(self, mock_send_email, initialized_mail):
        """Test notification email includes notification type"""
        mock_send_email.return_value = True

        with initialized_mail.app_context():
            send_notification_email(
                user_email="user@test.com",
                notification_type="info",
                title="Info",
                message="Test message"
            )

            call_kwargs = mock_send_email.call_args[1]
            template_data = call_kwargs['template_data']

            assert template_data['type'] == "info"
            assert template_data['title'] == "Info"
            assert template_data['message'] == "Test message"

    @patch('backend.email_service.send_email')
    def test_notification_email_various_types(self, mock_send_email, initialized_mail):
        """Test notification emails with various types"""
        mock_send_email.return_value = True

        notification_types = ["alert", "warning", "info", "success"]

        with initialized_mail.app_context():
            for notif_type in notification_types:
                send_notification_email(
                    user_email="user@test.com",
                    notification_type=notif_type,
                    title=f"{notif_type.title()} Title",
                    message=f"{notif_type} message"
                )

        assert mock_send_email.call_count == len(notification_types)


class TestErrorHandling:
    """Test error handling in email service"""

    @patch('backend.email_service.mail.send')
    def test_send_email_handles_smtp_error(self, mock_send, initialized_mail):
        """Test email sending handles SMTP errors"""
        mock_send.side_effect = Exception("SMTP connection failed")

        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=["test@test.com"],
                body="Test",
                async_send=False
            )

            assert result is False

    @patch('backend.email_service.render_template')
    def test_send_email_handles_template_error(self, mock_render, initialized_mail):
        """Test email sending handles template errors"""
        mock_render.side_effect = Exception("Template not found")

        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=["test@test.com"],
                template="nonexistent.html",
                async_send=False
            )

            assert result is False

    @patch('backend.email_service.mail.send')
    def test_send_email_handles_invalid_recipient(self, mock_send, initialized_mail):
        """Test email sending handles invalid recipients"""
        mock_send.side_effect = Exception("Invalid recipient")

        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=["invalid@@email"],
                body="Test",
                async_send=False
            )

            assert result is False

    @patch('backend.email_service.send_email')
    def test_password_reset_handles_send_failure(self, mock_send_email, initialized_mail):
        """Test password reset handles send failure"""
        mock_send_email.return_value = False

        with initialized_mail.app_context():
            result = send_password_reset_email(
                user_email="user@test.com",
                reset_token="abc",
                reset_url="http://test.com"
            )

            assert result is False


class TestEmailConfiguration:
    """Test email configuration scenarios"""

    def test_mail_server_configuration(self):
        """Test mail server configuration"""
        app = Flask(__name__)
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587

        init_mail(app)

        assert app.config['MAIL_SERVER'] == 'smtp.gmail.com'
        assert app.config['MAIL_PORT'] == 587

    def test_mail_authentication_configuration(self):
        """Test mail authentication configuration"""
        app = Flask(__name__)
        app.config['MAIL_USERNAME'] = 'user@example.com'
        app.config['MAIL_PASSWORD'] = 'secure_password'

        init_mail(app)

        assert app.config['MAIL_USERNAME'] == 'user@example.com'
        assert app.config['MAIL_PASSWORD'] == 'secure_password'

    def test_mail_default_sender(self):
        """Test default sender configuration"""
        app = Flask(__name__)
        app.config['MAIL_DEFAULT_SENDER'] = 'custom@sender.com'

        init_mail(app)

        assert app.config['MAIL_DEFAULT_SENDER'] == 'custom@sender.com'


class TestEmailQueue:
    """Test email queue management"""

    @patch('backend.email_service.Thread')
    def test_multiple_async_emails_queued(self, mock_thread, initialized_mail):
        """Test multiple async emails are queued"""
        with initialized_mail.app_context():
            for i in range(5):
                send_email(
                    subject=f"Test {i}",
                    recipients=[f"user{i}@test.com"],
                    body=f"Body {i}",
                    async_send=True
                )

            # Each should create a thread
            assert mock_thread.call_count == 5

    @patch('backend.email_service.mail.send')
    def test_sync_emails_sent_immediately(self, mock_send, initialized_mail):
        """Test synchronous emails are sent immediately"""
        with initialized_mail.app_context():
            send_email(
                subject="Test",
                recipients=["test@test.com"],
                body="Test",
                async_send=False
            )

            # Should be sent immediately
            mock_send.assert_called_once()


class TestEmailIntegrity:
    """Test email content integrity"""

    @patch('backend.email_service.mail.send')
    def test_email_subject_preserved(self, mock_send, initialized_mail):
        """Test email subject is preserved"""
        with initialized_mail.app_context():
            subject = "Important: Account Security"

            send_email(
                subject=subject,
                recipients=["test@test.com"],
                body="Test",
                async_send=False
            )

            # Verify Message was created with correct subject
            call_args = mock_send.call_args[0][0]
            assert call_args.subject == subject

    @patch('backend.email_service.mail.send')
    def test_email_recipients_preserved(self, mock_send, initialized_mail):
        """Test email recipients are preserved"""
        with initialized_mail.app_context():
            recipients = ["user1@test.com", "user2@test.com"]

            send_email(
                subject="Test",
                recipients=recipients,
                body="Test",
                async_send=False
            )

            call_args = mock_send.call_args[0][0]
            assert call_args.recipients == recipients

    @patch('backend.email_service.mail.send')
    def test_email_body_preserved(self, mock_send, initialized_mail):
        """Test email body content is preserved"""
        with initialized_mail.app_context():
            body = "This is the email body with special chars: <>&"

            send_email(
                subject="Test",
                recipients=["test@test.com"],
                body=body,
                async_send=False
            )

            call_args = mock_send.call_args[0][0]
            assert call_args.body == body


class TestEdgeCases:
    """Test edge cases in email service"""

    @patch('backend.email_service.mail.send')
    def test_empty_recipient_list(self, mock_send, initialized_mail):
        """Test sending to empty recipient list"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test",
                recipients=[],
                body="Test",
                async_send=False
            )

            # Should handle gracefully
            assert isinstance(result, bool)

    @patch('backend.email_service.mail.send')
    def test_very_long_subject(self, mock_send, initialized_mail):
        """Test email with very long subject"""
        with initialized_mail.app_context():
            long_subject = "A" * 1000

            result = send_email(
                subject=long_subject,
                recipients=["test@test.com"],
                body="Test",
                async_send=False
            )

            assert result is True

    @patch('backend.email_service.mail.send')
    def test_unicode_in_email(self, mock_send, initialized_mail):
        """Test email with Unicode characters"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test 日本語 Español",
                recipients=["test@test.com"],
                body="Unicode body: 你好 مرحبا",
                async_send=False
            )

            assert result is True

    @patch('backend.email_service.mail.send')
    def test_special_characters_in_subject(self, mock_send, initialized_mail):
        """Test email with special characters"""
        with initialized_mail.app_context():
            result = send_email(
                subject="Test: <>&\"'",
                recipients=["test@test.com"],
                body="Test",
                async_send=False
            )

            assert result is True


class TestIntegration:
    """Integration tests for email service"""

    @patch('backend.email_service.mail.send')
    def test_complete_email_workflow(self, mock_send, initialized_mail):
        """Test complete email sending workflow"""
        with initialized_mail.app_context():
            # Send various types of emails
            send_password_reset_email(
                "user@test.com",
                "token123",
                "http://test.com/reset"
            )

            send_verification_email(
                "user@test.com",
                "http://test.com/verify"
            )

            send_welcome_email(
                "user@test.com",
                "testuser"
            )

            send_notification_email(
                "user@test.com",
                "info",
                "Test",
                "Message"
            )

        # All emails should be processed
        assert mock_send.call_count >= 4
