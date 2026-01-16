
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
    """Handle SSO callback and sync user to database"""
    try:
        token = oauth.azure.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
             user_info = oauth.azure.parse_id_token(token)
             
        # Sync user to database
        from models import db, User
        email = user_info.get('email')
        username = user_info.get('preferred_username') or user_info.get('name') or email.split('@')[0]
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # Map tenant ID from OIDC claims if available
            # 'tid' is Azure AD tenant, 'org_id' or 'tenant_id' are common in others
            tenant_id = user_info.get('tid') or user_info.get('tenant_id') or user_info.get('org_id')
            
            user = User(
                username=username,
                email=email,
                is_active=True,
                is_sso=True,
                tenant_id=tenant_id,
                role='user', # Default role
                password_hash='SSO_EXTERNAL' # Placeholder as it's nullable=False in schema usually
            )
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Created new SSO user: {email} for tenant: {tenant_id}")
        else:
            # Update last login or other info if needed
            current_app.logger.info(f"SSO login for existing user: {email}")
            
        session['user_id'] = user.id
        return user_info
    except Exception as e:
        current_app.logger.error(f"SSO Callback failed: {e}")
        raise e
