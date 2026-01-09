
from authlib.integrations.flask_client import OAuth
from flask import redirect, url_for, session, current_app
import os

oauth = OAuth()

def configure_sso(app):
    """
    Configure SSO (Single Sign-On) using OIDC.
    Currently defaults to Azure AD / Entra ID pattern.
    """
    if not app.config.get('OIDC_CLIENT_ID'):
        # SSO not configured
        return

    oauth.init_app(app)
    
    # Register Azure AD / Entra ID
    oauth.register(
        name='azure',
        client_id=app.config.get('OIDC_CLIENT_ID'),
        client_secret=app.config.get('OIDC_CLIENT_SECRET'),
        server_metadata_url=app.config.get('OIDC_DISCOVERY_URL'),
        client_kwargs={
            'scope': 'openid profile email'
        }
    )

def login_sso():
    """Initiate SSO login flow"""
    if not current_app.config.get('OIDC_CLIENT_ID'):
        return "SSO not configured", 501
        
    redirect_uri = url_for('auth_api.sso_callback_route', _external=True)
    return oauth.azure.authorize_redirect(redirect_uri)

def handle_sso_callback():
    """Handle SSO callback"""
    try:
        token = oauth.azure.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
             # Fallback if userinfo in token
             user_info = oauth.azure.parse_id_token(token)
             
        # Logic to find or create user would go here
        # For now, just return the user info for debugging/verification
        return user_info
    except Exception as e:
        current_app.logger.error(f"SSO Callback failed: {e}")
        raise e
