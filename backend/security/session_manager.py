"""
Session Security Manager

Provides enhanced session management including:
- Redis-based session storage
- Session rotation
- Concurrent session limits
- Session invalidation on security events
"""

import os
import redis
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from flask import session
from flask_session import Session

logger = logging.getLogger(__name__)


class SessionManager:
    """Enhanced session management with Redis backend"""

    # Configuration
    MAX_CONCURRENT_SESSIONS = 3
    SESSION_ROTATION_INTERVAL = timedelta(minutes=5)

    def __init__(self, app=None, redis_client=None):
        """
        Initialize session manager.

        Args:
            app: Flask application instance
            redis_client: Optional Redis client (will create one if not provided)
        """
        self.app = app
        self.redis_client = redis_client

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize session management with a Flask app.

        Args:
            app: Flask application instance
        """
        # Configure Redis connection
        if not self.redis_client:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

        # Configure Flask-Session for Redis storage
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = self.redis_client
        app.config['SESSION_PERMANENT'] = True
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'session:'
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
            minutes=int(os.environ.get('SESSION_LIFETIME_MINUTES', 15))
        )

        # Initialize Flask-Session
        Session(app)

        # Register session rotation check
        @app.before_request
        def check_session_rotation():
            """Check if session needs rotation"""
            if 'user_id' in session:
                last_rotation = session.get('last_rotation')
                if last_rotation:
                    last_rotation = datetime.fromisoformat(last_rotation)
                    if datetime.utcnow() - last_rotation > self.SESSION_ROTATION_INTERVAL:
                        self.rotate_session()
                else:
                    # First time, set rotation timestamp
                    session['last_rotation'] = datetime.utcnow().isoformat()

        logger.info("Session manager initialized with Redis backend")

    def rotate_session(self):
        """
        Rotate session ID while preserving session data.

        This helps prevent session fixation attacks.
        """
        # Get current session data
        session_data = dict(session)

        # Clear current session
        session.clear()

        # Restore session data with new session ID
        for key, value in session_data.items():
            session[key] = value

        # Update rotation timestamp
        session['last_rotation'] = datetime.utcnow().isoformat()
        session.modified = True

        logger.debug("Session rotated successfully")

    def get_user_sessions(self, user_id: int) -> List[str]:
        """
        Get all active session IDs for a user.

        Args:
            user_id: User ID

        Returns:
            List of session IDs
        """
        try:
            key = f"user_sessions:{user_id}"
            sessions = self.redis_client.smembers(key)
            return list(sessions) if sessions else []
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []

    def add_user_session(self, user_id: int, session_id: str):
        """
        Track a new session for a user.

        Args:
            user_id: User ID
            session_id: Session ID
        """
        try:
            key = f"user_sessions:{user_id}"

            # Add session to user's session set
            self.redis_client.sadd(key, session_id)

            # Set expiry on the set (cleanup old entries)
            self.redis_client.expire(key, 86400)  # 24 hours

            # Store session metadata
            meta_key = f"session_meta:{session_id}"
            self.redis_client.hmset(meta_key, {
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            })
            self.redis_client.expire(meta_key, 86400)

            # Enforce concurrent session limit
            self.enforce_session_limit(user_id)

        except Exception as e:
            logger.error(f"Error adding user session: {str(e)}")

    def remove_user_session(self, user_id: int, session_id: str):
        """
        Remove a session from user's active sessions.

        Args:
            user_id: User ID
            session_id: Session ID
        """
        try:
            key = f"user_sessions:{user_id}"
            self.redis_client.srem(key, session_id)

            # Remove session metadata
            meta_key = f"session_meta:{session_id}"
            self.redis_client.delete(meta_key)

        except Exception as e:
            logger.error(f"Error removing user session: {str(e)}")

    def enforce_session_limit(self, user_id: int):
        """
        Enforce maximum concurrent sessions per user.

        Args:
            user_id: User ID
        """
        try:
            sessions = self.get_user_sessions(user_id)

            if len(sessions) > self.MAX_CONCURRENT_SESSIONS:
                # Get session metadata to find oldest sessions
                session_ages = []
                for sid in sessions:
                    meta_key = f"session_meta:{sid}"
                    meta = self.redis_client.hgetall(meta_key)
                    if meta:
                        created_at = datetime.fromisoformat(meta.get('created_at', datetime.utcnow().isoformat()))
                        session_ages.append((sid, created_at))

                # Sort by age (oldest first)
                session_ages.sort(key=lambda x: x[1])

                # Remove oldest sessions
                sessions_to_remove = len(sessions) - self.MAX_CONCURRENT_SESSIONS
                for i in range(sessions_to_remove):
                    old_session_id = session_ages[i][0]
                    self.invalidate_session(old_session_id)
                    logger.info(f"Removed old session for user {user_id} (limit enforcement)")

        except Exception as e:
            logger.error(f"Error enforcing session limit: {str(e)}")

    def invalidate_session(self, session_id: str):
        """
        Invalidate a specific session.

        Args:
            session_id: Session ID to invalidate
        """
        try:
            # Get user ID from session metadata
            meta_key = f"session_meta:{session_id}"
            meta = self.redis_client.hgetall(meta_key)

            if meta:
                user_id = meta.get('user_id')
                if user_id:
                    self.remove_user_session(int(user_id), session_id)

            # Delete the session from Redis
            session_key = f"session:{session_id}"
            self.redis_client.delete(session_key)

            logger.info(f"Session invalidated: {session_id}")

        except Exception as e:
            logger.error(f"Error invalidating session: {str(e)}")

    def invalidate_all_user_sessions(self, user_id: int, except_current: bool = False):
        """
        Invalidate all sessions for a user.

        Args:
            user_id: User ID
            except_current: If True, keep the current session active
        """
        try:
            sessions = self.get_user_sessions(user_id)
            current_session_id = session.get('session_id') if except_current else None

            for session_id in sessions:
                if session_id != current_session_id:
                    self.invalidate_session(session_id)

            logger.info(f"Invalidated all sessions for user {user_id}")

        except Exception as e:
            logger.error(f"Error invalidating user sessions: {str(e)}")

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata.

        Args:
            session_id: Session ID

        Returns:
            Dictionary of session metadata or None
        """
        try:
            meta_key = f"session_meta:{session_id}"
            meta = self.redis_client.hgetall(meta_key)
            return dict(meta) if meta else None

        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            return None

    def update_session_activity(self, session_id: str):
        """
        Update last activity timestamp for a session.

        Args:
            session_id: Session ID
        """
        try:
            meta_key = f"session_meta:{session_id}"
            self.redis_client.hset(meta_key, 'last_activity', datetime.utcnow().isoformat())

        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")

    @staticmethod
    def on_password_change(user_id: int):
        """
        Handle session invalidation when password changes.

        Args:
            user_id: User ID whose password changed
        """
        from flask import current_app
        session_manager = current_app.extensions.get('session_manager')

        if session_manager:
            # Invalidate all sessions except current
            session_manager.invalidate_all_user_sessions(user_id, except_current=True)
            logger.info(f"Sessions invalidated for user {user_id} due to password change")

    @staticmethod
    def on_account_locked(user_id: int):
        """
        Handle session invalidation when account is locked.

        Args:
            user_id: User ID whose account was locked
        """
        from flask import current_app
        session_manager = current_app.extensions.get('session_manager')

        if session_manager:
            # Invalidate all sessions including current
            session_manager.invalidate_all_user_sessions(user_id, except_current=False)
            logger.info(f"All sessions invalidated for user {user_id} due to account lock")


def configure_session_manager(app, redis_client=None):
    """
    Configure session manager for a Flask application.

    Args:
        app: Flask application instance
        redis_client: Optional Redis client

    Example:
        from flask import Flask
        from backend.security.session_manager import configure_session_manager

        app = Flask(__name__)
        configure_session_manager(app)
    """
    session_manager = SessionManager(app, redis_client)
    app.extensions['session_manager'] = session_manager
    logger.info("Session manager configured")
    return session_manager
