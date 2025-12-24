"""
Replit Auth Integration Module

Provides OAuth/OpenID Connect authentication via Replit alongside existing
username/password authentication. Uses Flask-Dance for OAuth handling.
"""

import jwt
import os
import uuid
import logging
import requests
from functools import wraps
from urllib.parse import urlencode
from datetime import datetime, UTC
from jwt import PyJWKClient, PyJWKClientError

from flask import g, session, redirect, request, url_for, flash
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_authorized, oauth_error
from flask_dance.consumer.storage import BaseStorage
from flask_login import login_user, logout_user, current_user
from sqlalchemy.exc import NoResultFound
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, OAuthAccount

logger = logging.getLogger(__name__)

# Global JWKS client for signature verification
_jwks_client = None


class OAuthAccountStorage(BaseStorage):
    """Custom storage for OAuth tokens using OAuthAccount model."""

    def get(self, blueprint):
        if not current_user.is_authenticated:
            return None
        try:
            oauth = OAuthAccount.query.filter_by(
                user_id=current_user.id,
                provider=blueprint.name,
            ).first()
            return oauth.token if oauth else None
        except Exception:
            return None

    def set(self, blueprint, token, provider_user_id=None):
        """Store OAuth token. provider_user_id should be the Replit 'sub' claim."""
        if not current_user.is_authenticated:
            return
        oauth = OAuthAccount.query.filter_by(
            user_id=current_user.id,
            provider=blueprint.name,
        ).first()
        if oauth:
            oauth.token = token
            oauth.updated_at = datetime.now(UTC)
        else:
            # Only create if we have a valid provider_user_id
            if not provider_user_id:
                logger.warning("Cannot store OAuth token without provider_user_id")
                return
            oauth = OAuthAccount(
                user_id=current_user.id,
                provider=blueprint.name,
                provider_user_id=str(provider_user_id),
                token=token,
            )
            db.session.add(oauth)
        db.session.commit()

    def delete(self, blueprint):
        if not current_user.is_authenticated:
            return
        OAuthAccount.query.filter_by(
            user_id=current_user.id,
            provider=blueprint.name,
        ).delete()
        db.session.commit()


def get_jwks_client():
    """Get or create the JWKS client for signature verification."""
    global _jwks_client
    if _jwks_client is None:
        issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")
        jwks_uri = f"{issuer_url}/certs"
        _jwks_client = PyJWKClient(jwks_uri)
    return _jwks_client


def generate_nonce() -> str:
    """Generate a secure nonce for OIDC."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def verify_id_token(id_token: str, valid_nonces: set = None) -> dict:
    """
    Verify and decode ID token using Replit's JWKS with full OIDC validation.
    
    Validates:
    - Signature using Replit's JWKS
    - Audience (aud) matches REPL_ID
    - Issuer (iss) matches Replit OIDC endpoint
    - Expiration (exp) is in the future
    - Issued at (iat) is within acceptable skew
    - Nonce exists in valid_nonces if provided (replay protection)
    - Authorized party (azp) if present
    
    Args:
        id_token: The JWT ID token to verify
        valid_nonces: Set of valid nonces issued by this session. If provided,
                      the token's nonce must be in this set.
    
    Returns:
        Verified claims dictionary
        
    Raises:
        ValueError: If token verification fails
    """
    issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")
    repl_id = os.environ.get('REPL_ID')
    
    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        
        # Clock skew tolerance of 60 seconds
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=repl_id,
            issuer=issuer_url,
            leeway=60,  # Allow 60 seconds clock skew
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["sub", "aud", "iss", "exp", "iat"],
            }
        )
        
        # Verify nonce is in our valid set (replay protection)
        if valid_nonces is not None:
            token_nonce = claims.get('nonce')
            if not token_nonce:
                raise ValueError("ID token missing nonce claim")
            if token_nonce not in valid_nonces:
                raise ValueError("Unknown nonce - possible replay attack")
        
        # Verify azp if present (must match client_id if specified)
        azp = claims.get('azp')
        if azp and azp != repl_id:
            raise ValueError("Authorized party (azp) does not match client_id")
        
        # Verify iat is not too old (max 10 minutes)
        import time
        iat = claims.get('iat', 0)
        if time.time() - iat > 600:
            raise ValueError("Token issued too long ago (max 10 minutes)")
        
        return claims
        
    except PyJWKClientError as e:
        logger.error(f"JWKS client error: {e}")
        raise ValueError(f"Failed to verify token signature: {e}")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise ValueError(f"Invalid ID token: {e}")


def make_replit_blueprint():
    """Create and configure the Replit OAuth blueprint."""
    try:
        repl_id = os.environ.get('REPL_ID')
        if not repl_id:
            logger.warning("REPL_ID not set - Replit Auth will be disabled")
            return None
    except KeyError:
        return None

    issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")

    replit_bp = OAuth2ConsumerBlueprint(
        "replit_auth",
        __name__,
        client_id=repl_id,
        client_secret=None,
        base_url=issuer_url,
        authorization_url_params={"prompt": "login consent"},
        token_url=issuer_url + "/token",
        token_url_params={"auth": (), "include_client_id": True},
        auto_refresh_url=issuer_url + "/token",
        auto_refresh_kwargs={"client_id": repl_id},
        authorization_url=issuer_url + "/auth",
        use_pkce=True,
        code_challenge_method="S256",
        scope=["openid", "profile", "email", "offline_access"],
        storage=OAuthAccountStorage(),
    )
    
    @replit_bp.before_app_request
    def inject_nonce_into_auth():
        """
        Inject nonce into authorization requests for replay protection.
        
        Nonces are stored in a session set keyed by the nonce value itself.
        On callback, we extract the nonce from the ID token and verify it exists
        in our set (then remove it for one-time use).
        
        This approach:
        - Supports concurrent login attempts (each gets unique nonce)
        - Validates by checking if returned nonce was issued by us
        - Removes nonce after use (replay protection)
        
        SECURITY NOTE: Flask session cookies are cryptographically signed with
        SECRET_KEY. An attacker cannot forge or modify the nonce set without the key.
        The oauth_authorized signal fires only after Flask-Dance validates the
        OAuth state parameter, ensuring the callback corresponds to a legitimate
        login initiation from this session.
        """
        if request.endpoint == 'replit_auth.login':
            nonce = generate_nonce()
            # Store nonce in a set for concurrent login support
            nonce_set = session.setdefault('replit_auth_nonces', {})
            # Clean up old entries (max 5 concurrent attempts, oldest first)
            if len(nonce_set) >= 5:
                # Remove oldest by timestamp
                oldest = min(nonce_set.items(), key=lambda x: x[1])
                nonce_set.pop(oldest[0], None)
            nonce_set[nonce] = datetime.now(UTC).isoformat()
            session.modified = True
            # Flask-Dance will include the nonce in the auth URL
            replit_bp.authorization_url_params['nonce'] = nonce

    @replit_bp.before_app_request
    def set_applocal_session():
        if '_browser_session_key' not in session:
            session['_browser_session_key'] = uuid.uuid4().hex
        session.modified = True
        g.browser_session_key = session['_browser_session_key']

    @replit_bp.route("/logout")
    def replit_logout():
        logout_user()
        end_session_endpoint = issuer_url + "/session/end"
        encoded_params = urlencode({
            "client_id": repl_id,
            "post_logout_redirect_uri": request.url_root,
        })
        logout_url = f"{end_session_endpoint}?{encoded_params}"
        return redirect(logout_url)

    return replit_bp


def find_or_create_user(user_claims):
    """Find existing user by OAuth account or email, or create new user."""
    provider_user_id = user_claims.get('sub')
    email = user_claims.get('email')

    oauth_account = OAuthAccount.query.filter_by(
        provider='replit_auth',
        provider_user_id=str(provider_user_id),
    ).first()

    if oauth_account:
        return oauth_account.user

    if email:
        existing_user = User.query.filter(
            db.func.lower(User.email) == email.lower()
        ).first()
        if existing_user:
            oauth_account = OAuthAccount(
                user_id=existing_user.id,
                provider='replit_auth',
                provider_user_id=str(provider_user_id),
            )
            db.session.add(oauth_account)
            db.session.commit()
            return existing_user

    base_username = user_claims.get('first_name', 'user') or 'user'
    username = base_username.lower().replace(' ', '_')
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username.lower()}_{counter}"
        counter += 1

    # Create a valid but unusable password hash for OAuth-only users
    # This prevents crashes in password check functions
    random_password = str(uuid.uuid4()) + str(uuid.uuid4())
    oauth_password_hash = generate_password_hash(random_password)
    
    new_user = User(
        username=username,
        email=email or f"{provider_user_id}@replit.user",
        password_hash=oauth_password_hash,
        active=True,
    )
    db.session.add(new_user)
    db.session.flush()

    oauth_account = OAuthAccount(
        user_id=new_user.id,
        provider='replit_auth',
        provider_user_id=str(provider_user_id),
    )
    db.session.add(oauth_account)
    db.session.commit()

    logger.info(f"Created new user {username} via Replit Auth")
    return new_user


@oauth_authorized.connect
def handle_oauth_authorized(blueprint, token):
    """Handle successful OAuth authorization."""
    if blueprint.name != 'replit_auth':
        return

    try:
        # Get the set of valid nonces issued by this session
        nonce_dict = session.get('replit_auth_nonces', {})
        
        if not nonce_dict:
            logger.warning("OAuth callback with no stored nonces - possible replay attack")
            raise ValueError("No OAuth nonces found - possible replay attack")
        
        # Convert dict keys to set for nonce validation
        valid_nonces = set(nonce_dict.keys())
        
        # Verify the ID token with full signature and nonce validation
        # This will check that the token's nonce is in our valid set
        user_claims = verify_id_token(token['id_token'], valid_nonces=valid_nonces)
        
        # Remove the used nonce from session (one-time use)
        token_nonce = user_claims.get('nonce')
        if token_nonce in nonce_dict:
            del nonce_dict[token_nonce]
            session.modified = True
        
        provider_user_id = user_claims.get('sub')
        
        if not provider_user_id:
            raise ValueError("Missing 'sub' claim in ID token")
        
        user = find_or_create_user(user_claims)
        login_user(user)

        # Update or create OAuth account with correct provider_user_id
        oauth = OAuthAccount.query.filter_by(
            user_id=user.id,
            provider='replit_auth',
        ).first()
        if oauth:
            oauth.token = token
            oauth.updated_at = datetime.now(UTC)
        else:
            # This shouldn't happen as find_or_create_user creates the link,
            # but handle it just in case
            oauth = OAuthAccount(
                user_id=user.id,
                provider='replit_auth',
                provider_user_id=str(provider_user_id),
                token=token,
            )
            db.session.add(oauth)
        db.session.commit()

        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for('pages.dashboard'))

    except ValueError as e:
        logger.error(f"OAuth token verification failed: {e}")
        flash("Authentication failed: Invalid token. Please try again.", "danger")
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"OAuth authorization failed: {e}")
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for('auth.login'))


@oauth_error.connect
def handle_oauth_error(blueprint, error, error_description=None, error_uri=None):
    """Handle OAuth errors."""
    logger.error(f"OAuth error: {error} - {error_description}")
    flash("Authentication failed. Please try again.", "danger")
    return redirect(url_for('auth.login'))


def require_replit_login(f):
    """Decorator to require Replit authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = request.url
            return redirect(url_for('replit_auth.login'))
        return f(*args, **kwargs)
    return decorated_function
