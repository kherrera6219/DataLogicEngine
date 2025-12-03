
from flask import Blueprint, request, jsonify
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

    # Check if user exists
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401

    # Check if account is locked
    if user.is_account_locked():
        return jsonify({
            'error': 'Account is temporarily locked due to multiple failed login attempts. Please try again later.',
            'locked_until': user.locked_until.isoformat() if user.locked_until else None
        }), 403

    # Check password
    if not user.check_password(data['password']):
        # Record failed login attempt
        user.record_failed_login()
        db.session.commit()

        return jsonify({
            'error': 'Invalid username or password',
            'attempts_remaining': max(0, 5 - user.failed_login_attempts)
        }), 401

    # Check if password is expired
    if user.is_password_expired():
        return jsonify({
            'error': 'Password has expired. Please reset your password.',
            'force_password_change': True,
            'user_id': user.id
        }), 403

    # Check if password change is forced
    if user.force_password_change:
        return jsonify({
            'error': 'Password change required. Please change your password.',
            'force_password_change': True,
            'user_id': user.id
        }), 403

    # Record successful login
    user.record_successful_login()
    db.session.commit()

    # Create access token (15 minutes for enhanced security)
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(minutes=15)
    )

    # Prepare response
    response_data = {
        'access_token': access_token,
        'user': user.to_dict()
    }

    # Warn if password is expiring soon (within 7 days)
    days_until_expiry = user.days_until_password_expiry()
    if days_until_expiry is not None and 0 < days_until_expiry <= 7:
        response_data['warning'] = f'Your password will expire in {days_until_expiry} days. Please change it soon.'

    return jsonify(response_data), 200

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
    try:
        user_id = request.headers.get('X-Replit-User-Id')
        username = request.headers.get('X-Replit-User-Name')
        
        if not user_id or not username:
            return jsonify({'error': 'Not authenticated with Replit'}), 401
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Create new user from Replit credentials
            user = User(
                username=username,
                email=f"{username}@replit.user",  # Placeholder email
            )
            user.set_password(f"replit_{user_id}")  # Set a password they can reset later
            db.session.add(user)
            db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=1)
        )
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
