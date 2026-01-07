"""
Email Service for DataLogicEngine

Provides email functionality for:
- Password reset
- Account verification
- Notifications
"""

import os
import logging
from typing import Optional, List
from flask import Flask, render_template, current_app
from flask_mail import Mail, Message
from threading import Thread

logger = logging.getLogger(__name__)

# Initialize Flask-Mail
mail = Mail()


def init_mail(app: Flask) -> None:
    """Initialize email service with Flask app."""
    app.config.setdefault('MAIL_SERVER', os.environ.get('MAIL_SERVER', 'smtp.gmail.com'))
    app.config.setdefault('MAIL_PORT', int(os.environ.get('MAIL_PORT', 587)))
    app.config.setdefault('MAIL_USE_TLS', os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true')
    app.config.setdefault('MAIL_USE_SSL', os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true')
    app.config.setdefault('MAIL_USERNAME', os.environ.get('MAIL_USERNAME'))
    app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD'))
    app.config.setdefault('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@datalogicengine.com'))
    
    mail.init_app(app)
    logger.info("Email service initialized")


def send_async_email(app: Flask, msg: Message) -> None:
    """Send email asynchronously."""
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"Email sent to {msg.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")


def send_email(
    subject: str,
    recipients: List[str],
    body: Optional[str] = None,
    html: Optional[str] = None,
    template: Optional[str] = None,
    template_data: Optional[dict] = None,
    async_send: bool = True
) -> bool:
    """
    Send an email.
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        body: Plain text body
        html: HTML body
        template: Template name (e.g., 'email/welcome.html')
        template_data: Data for template rendering
        async_send: Whether to send asynchronously
    
    Returns:
        bool: True if email was queued/sent successfully
    """
    try:
        msg = Message(subject=subject, recipients=recipients)
        
        if template:
            msg.html = render_template(template, **(template_data or {}))
        elif html:
            msg.html = html
        
        if body:
            msg.body = body
        elif not msg.html:
            raise ValueError("Either body, html, or template must be provided")
        
        if async_send:
            Thread(
                target=send_async_email,
                args=(current_app._get_current_object(), msg)
            ).start()
        else:
            mail.send(msg)
        
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


def send_password_reset_email(user_email: str, reset_token: str, reset_url: str) -> bool:
    """Send password reset email."""
    return send_email(
        subject="Password Reset Request - DataLogicEngine",
        recipients=[user_email],
        template="email/password_reset.html",
        template_data={
            "reset_url": reset_url,
            "reset_token": reset_token,
            "expires_in": "1 hour"
        }
    )


def send_verification_email(user_email: str, verification_url: str) -> bool:
    """Send account verification email."""
    return send_email(
        subject="Verify Your Account - DataLogicEngine",
        recipients=[user_email],
        template="email/verify_account.html",
        template_data={"verification_url": verification_url}
    )


def send_welcome_email(user_email: str, username: str) -> bool:
    """Send welcome email after registration."""
    return send_email(
        subject="Welcome to DataLogicEngine!",
        recipients=[user_email],
        template="email/welcome.html",
        template_data={"username": username}
    )


def send_notification_email(
    user_email: str,
    notification_type: str,
    title: str,
    message: str
) -> bool:
    """Send a notification email."""
    return send_email(
        subject=f"{title} - DataLogicEngine",
        recipients=[user_email],
        template="email/notification.html",
        template_data={
            "type": notification_type,
            "title": title,
            "message": message
        }
    )
