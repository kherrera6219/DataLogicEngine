
import hashlib
import hmac
import os
import secrets

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from .models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create new user
    new_user = User(
        username=data['username'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    # Find user
    user = User.query.filter_by(username=data['username']).first()
    
    # Check password
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Create access token
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(days=1)
    )
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

@auth_bp.route('/replit-auth', methods=['GET'])
def replit_auth():
    """Handle Replit Auth integration"""
    if os.environ.get('REPLIT_AUTH_ENABLED', 'false').lower() != 'true':
        return jsonify({'error': 'Replit authentication is disabled'}), 503

    shared_secret = os.environ.get('REPLIT_AUTH_SHARED_SECRET')
    if not shared_secret:
        current_app.logger.error('REPLIT_AUTH_SHARED_SECRET is not configured; rejecting request')
        return jsonify({'error': 'Replit authentication is not configured'}), 503

    user_id = request.headers.get('X-Replit-User-Id')
    username = request.headers.get('X-Replit-User-Name')
    signature = request.headers.get('X-Replit-Signature')

    if not user_id or not username:
        return jsonify({'error': 'Not authenticated with Replit'}), 401

    if not signature:
        return jsonify({'error': 'Missing Replit signature header'}), 401

    payload = f"{user_id}:{username}"
    expected_signature = hmac.new(
        shared_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        current_app.logger.warning('Replit signature verification failed for user %s', username)
        return jsonify({'error': 'Invalid Replit signature'}), 401

    try:
        user = User.query.filter_by(username=username).first()

        if not user:
            user = User(
                username=username,
                email=f"{username}@replit.user",
            )
            user.set_password(secrets.token_urlsafe(32))
            db.session.add(user)
            db.session.commit()

        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(minutes=15)
        )

        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200

    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.exception('Error processing Replit authentication')
        return jsonify({'error': str(exc)}), 500
