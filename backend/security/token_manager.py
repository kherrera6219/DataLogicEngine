"""
JWT Token Manager

Provides secure JWT token management including:
- Access token and refresh token generation
- Token blacklisting for logout
- Token refresh mechanism
- Token binding to user agent
"""

import os
import redis
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    decode_token
)

logger = logging.getLogger(__name__)


class TokenManager:
    """Manage JWT tokens with enhanced security"""

    # Configuration
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
    REFRESH_TOKEN_LIFETIME = timedelta(days=7)

    def __init__(self, redis_client=None):
        """
        Initialize token manager.

        Args:
            redis_client: Optional Redis client for token blacklist
        """
        if not redis_client:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        else:
            self.redis_client = redis_client

        logger.info("Token manager initialized")

    def create_tokens(self, user_id: int, additional_claims: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Create access and refresh tokens for a user.

        Args:
            user_id: User ID
            additional_claims: Optional additional claims to include in tokens

        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Get user agent for token binding
        user_agent = request.headers.get('User-Agent', '')
        user_agent_hash = self._hash_user_agent(user_agent)

        # Create claims
        claims = {
            'user_agent_hash': user_agent_hash,
            'token_id': secrets.token_urlsafe(16)
        }

        if additional_claims:
            claims.update(additional_claims)

        # Create tokens
        access_token = create_access_token(
            identity=user_id,
            expires_delta=self.ACCESS_TOKEN_LIFETIME,
            additional_claims=claims
        )

        refresh_token = create_refresh_token(
            identity=user_id,
            expires_delta=self.REFRESH_TOKEN_LIFETIME,
            additional_claims=claims
        )

        logger.debug(f"Tokens created for user {user_id}")

        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Refresh access token using a refresh token.

        Implements refresh token rotation - old refresh token is invalidated.

        Args:
            refresh_token: Current refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token) or (None, None) if invalid
        """
        try:
            # Decode refresh token
            decoded = decode_token(refresh_token)
            user_id = decoded['sub']
            token_id = decoded.get('token_id')

            # Check if token is blacklisted
            if self.is_token_blacklisted(token_id):
                logger.warning(f"Attempted to use blacklisted refresh token: {token_id}")
                return None, None

            # Verify user agent binding
            if not self._verify_user_agent_binding(decoded):
                logger.warning(f"User agent mismatch for token refresh: {token_id}")
                return None, None

            # Blacklist old refresh token (rotation)
            self.blacklist_token(token_id, self.REFRESH_TOKEN_LIFETIME)

            # Create new tokens
            access_token, new_refresh_token = self.create_tokens(user_id)

            logger.info(f"Tokens refreshed for user {user_id}")

            return access_token, new_refresh_token

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None, None

    def blacklist_token(self, token_id: str, expires_in: timedelta):
        """
        Add a token to the blacklist.

        Args:
            token_id: Token ID to blacklist
            expires_in: How long to keep in blacklist (should match token expiry)
        """
        try:
            key = f"token_blacklist:{token_id}"
            self.redis_client.setex(
                key,
                int(expires_in.total_seconds()),
                datetime.utcnow().isoformat()
            )
            logger.debug(f"Token blacklisted: {token_id}")

        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}")

    def is_token_blacklisted(self, token_id: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            token_id: Token ID to check

        Returns:
            True if blacklisted
        """
        try:
            key = f"token_blacklist:{token_id}"
            return self.redis_client.exists(key) > 0

        except Exception as e:
            logger.error(f"Error checking token blacklist: {str(e)}")
            return False

    def revoke_token(self):
        """
        Revoke the current JWT token (for logout).
        """
        try:
            jwt_data = get_jwt()
            token_id = jwt_data.get('token_id')
            exp_timestamp = jwt_data.get('exp')

            if token_id and exp_timestamp:
                # Calculate time until expiry
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                expires_in = exp_datetime - datetime.utcnow()

                if expires_in.total_seconds() > 0:
                    self.blacklist_token(token_id, expires_in)
                    logger.info(f"Token revoked: {token_id}")
                else:
                    logger.debug(f"Token already expired: {token_id}")

        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")

    def revoke_all_user_tokens(self, user_id: int):
        """
        Revoke all tokens for a user.

        Useful when password changes or account is compromised.

        Args:
            user_id: User ID
        """
        try:
            # Add user to revoked users list
            key = f"revoked_users:{user_id}"
            # Keep for max refresh token lifetime
            self.redis_client.setex(
                key,
                int(self.REFRESH_TOKEN_LIFETIME.total_seconds()),
                datetime.utcnow().isoformat()
            )

            logger.info(f"All tokens revoked for user {user_id}")

        except Exception as e:
            logger.error(f"Error revoking user tokens: {str(e)}")

    def is_user_revoked(self, user_id: int) -> bool:
        """
        Check if all tokens for a user have been revoked.

        Args:
            user_id: User ID

        Returns:
            True if user's tokens are revoked
        """
        try:
            key = f"revoked_users:{user_id}"
            return self.redis_client.exists(key) > 0

        except Exception as e:
            logger.error(f"Error checking user revocation: {str(e)}")
            return False

    def verify_token(self) -> bool:
        """
        Verify the current JWT token.

        Checks:
        - Token is not blacklisted
        - User is not revoked
        - User agent matches

        Returns:
            True if token is valid
        """
        try:
            jwt_data = get_jwt()
            user_id = get_jwt_identity()
            token_id = jwt_data.get('token_id')

            # Check if token is blacklisted
            if token_id and self.is_token_blacklisted(token_id):
                logger.warning(f"Blacklisted token used: {token_id}")
                return False

            # Check if user is revoked
            if user_id and self.is_user_revoked(user_id):
                logger.warning(f"Revoked user token used: {user_id}")
                return False

            # Check user agent binding
            if not self._verify_user_agent_binding(jwt_data):
                logger.warning(f"User agent mismatch for token: {token_id}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return False

    @staticmethod
    def _hash_user_agent(user_agent: str) -> str:
        """
        Hash user agent for token binding.

        Args:
            user_agent: User agent string

        Returns:
            SHA-256 hash of user agent
        """
        return hashlib.sha256(user_agent.encode()).hexdigest()

    def _verify_user_agent_binding(self, jwt_data: Dict) -> bool:
        """
        Verify user agent matches the one in the token.

        Args:
            jwt_data: Decoded JWT data

        Returns:
            True if user agent matches
        """
        # Get stored user agent hash from token
        stored_hash = jwt_data.get('user_agent_hash')

        if not stored_hash:
            # No binding in token (backward compatibility)
            return True

        # Get current user agent
        current_user_agent = request.headers.get('User-Agent', '')
        current_hash = self._hash_user_agent(current_user_agent)

        return stored_hash == current_hash

    @staticmethod
    def on_password_change(user_id: int):
        """
        Handle token revocation when password changes.

        Args:
            user_id: User ID whose password changed
        """
        from flask import current_app
        token_manager = current_app.extensions.get('token_manager')

        if token_manager:
            token_manager.revoke_all_user_tokens(user_id)
            logger.info(f"All tokens revoked for user {user_id} due to password change")

    @staticmethod
    def on_account_locked(user_id: int):
        """
        Handle token revocation when account is locked.

        Args:
            user_id: User ID whose account was locked
        """
        from flask import current_app
        token_manager = current_app.extensions.get('token_manager')

        if token_manager:
            token_manager.revoke_all_user_tokens(user_id)
            logger.info(f"All tokens revoked for user {user_id} due to account lock")


def configure_token_manager(app, redis_client=None):
    """
    Configure token manager for a Flask application.

    Args:
        app: Flask application instance
        redis_client: Optional Redis client

    Example:
        from flask import Flask
        from flask_jwt_extended import JWTManager
        from backend.security.token_manager import configure_token_manager

        app = Flask(__name__)
        jwt = JWTManager(app)
        configure_token_manager(app)
    """
    token_manager = TokenManager(redis_client)
    app.extensions['token_manager'] = token_manager

    # Register JWT callbacks
    from flask_jwt_extended import JWTManager

    jwt = app.extensions.get('jwt-manager') or JWTManager(app)

    # Check token blacklist on each request
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        token_id = jwt_payload.get('token_id')
        user_id = jwt_payload.get('sub')

        # Check token blacklist
        if token_id and token_manager.is_token_blacklisted(token_id):
            return True

        # Check user revocation
        if user_id and token_manager.is_user_revoked(user_id):
            return True

        return False

    logger.info("Token manager configured with JWT integration")
    return token_manager
