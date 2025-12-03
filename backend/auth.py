
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from .models import db, User
from backend.security.mfa import MFASetup, MFAManager, verify_mfa_token, verify_backup_code, generate_backup_codes

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

    # Check if MFA is enabled
    if user.mfa_enabled:
        mfa_token = data.get('mfa_code')

        if not mfa_token:
            # MFA required but not provided
            return jsonify({
                'error': 'MFA code required',
                'mfa_required': True,
                'user_id': user.id
            }), 403

        # Verify MFA token (TOTP or backup code)
        if verify_mfa_token(user.mfa_secret, mfa_token):
            # Valid TOTP token
            pass
        elif user.mfa_backup_codes and verify_backup_code(mfa_token, user.mfa_backup_codes)[0]:
            # Valid backup code - remove it
            is_valid, used_hash = verify_backup_code(mfa_token, user.mfa_backup_codes)
            user.mfa_backup_codes.remove(used_hash)
            db.session.commit()
        else:
            # Invalid MFA token
            return jsonify({
                'error': 'Invalid MFA code',
                'mfa_required': True
            }), 401

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

    # Warn if backup codes are running low
    if user.mfa_enabled and user.mfa_backup_codes:
        remaining_codes = len(user.mfa_backup_codes)
        if remaining_codes <= 3:
            response_data['warning'] = f'Only {remaining_codes} backup codes remaining. Generate new ones soon.'

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

# ========================================
# Multi-Factor Authentication Endpoints
# ========================================

@auth_bp.route('/mfa/setup', methods=['POST'])
@jwt_required()
def mfa_setup():
    """
    Initiate MFA setup for the current user.

    Returns QR code and backup codes for MFA enrollment.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.mfa_enabled:
        return jsonify({'error': 'MFA is already enabled. Disable it first to re-setup.'}), 400

    # Initialize MFA setup
    setup = MFASetup(user.email or user.username)
    data = setup.initiate_setup()

    # Store secret temporarily (will be confirmed after verification)
    user.mfa_secret = data['secret']
    user.mfa_backup_codes = setup.get_hashed_backup_codes()
    db.session.commit()

    return jsonify({
        'message': 'MFA setup initiated. Scan the QR code with your authenticator app.',
        'qr_code': data['qr_code'],
        'manual_entry_key': data['manual_entry'],
        'backup_codes': data['backup_codes']  # Show these ONCE!
    }), 200

@auth_bp.route('/mfa/verify-setup', methods=['POST'])
@jwt_required()
def mfa_verify_setup():
    """
    Verify MFA setup by checking a TOTP code.

    Expects: { "mfa_code": "123456" }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.mfa_enabled:
        return jsonify({'error': 'MFA is already enabled'}), 400

    if not user.mfa_secret:
        return jsonify({'error': 'MFA setup not initiated. Call /auth/mfa/setup first.'}), 400

    # Get MFA code from request
    data = request.get_json()
    mfa_code = data.get('mfa_code')

    if not mfa_code:
        return jsonify({'error': 'MFA code required'}), 400

    # Verify TOTP code
    if not verify_mfa_token(user.mfa_secret, mfa_code):
        return jsonify({'error': 'Invalid MFA code. Please try again.'}), 401

    # Enable MFA
    user.mfa_enabled = True
    db.session.commit()

    return jsonify({
        'message': 'MFA enabled successfully!',
        'backup_codes_count': len(user.mfa_backup_codes) if user.mfa_backup_codes else 0
    }), 200

@auth_bp.route('/mfa/disable', methods=['POST'])
@jwt_required()
def mfa_disable():
    """
    Disable MFA for the current user.

    Expects: { "password": "user_password", "mfa_code": "123456" }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.mfa_enabled:
        return jsonify({'error': 'MFA is not enabled'}), 400

    # Get request data
    data = request.get_json()
    password = data.get('password')
    mfa_code = data.get('mfa_code')

    if not password:
        return jsonify({'error': 'Password required to disable MFA'}), 400

    # Verify password
    if not user.check_password(password):
        return jsonify({'error': 'Invalid password'}), 401

    # Verify MFA code (TOTP or backup code)
    if not mfa_code:
        return jsonify({'error': 'MFA code required to disable MFA'}), 400

    valid_totp = verify_mfa_token(user.mfa_secret, mfa_code)
    valid_backup = False

    if user.mfa_backup_codes:
        valid_backup, _ = verify_backup_code(mfa_code, user.mfa_backup_codes)

    if not valid_totp and not valid_backup:
        return jsonify({'error': 'Invalid MFA code'}), 401

    # Disable MFA
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_backup_codes = None
    db.session.commit()

    return jsonify({'message': 'MFA disabled successfully'}), 200

@auth_bp.route('/mfa/regenerate-backup-codes', methods=['POST'])
@jwt_required()
def mfa_regenerate_backup_codes():
    """
    Generate new backup codes.

    Expects: { "mfa_code": "123456" }
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.mfa_enabled:
        return jsonify({'error': 'MFA is not enabled'}), 400

    # Get MFA code from request
    data = request.get_json()
    mfa_code = data.get('mfa_code')

    if not mfa_code:
        return jsonify({'error': 'MFA code required to regenerate backup codes'}), 400

    # Verify TOTP code (don't allow backup codes to regenerate backup codes)
    if not verify_mfa_token(user.mfa_secret, mfa_code):
        return jsonify({'error': 'Invalid MFA code'}), 401

    # Generate new backup codes
    plaintext_codes, hashed_codes = generate_backup_codes()

    # Update user's backup codes
    user.mfa_backup_codes = hashed_codes
    db.session.commit()

    return jsonify({
        'message': 'New backup codes generated. Save these securely!',
        'backup_codes': plaintext_codes  # Show these ONCE!
    }), 200

@auth_bp.route('/mfa/status', methods=['GET'])
@jwt_required()
def mfa_status():
    """
    Get MFA status for the current user.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'mfa_enabled': user.mfa_enabled,
        'backup_codes_remaining': len(user.mfa_backup_codes) if user.mfa_backup_codes else 0
    }), 200
