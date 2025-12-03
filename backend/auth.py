
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from .models import db, User
from .security.mfa import MFAManager
from .schemas import validate_request_data, UserLoginSchema, UserRegistrationSchema
import logging

logger = logging.getLogger(__name__)

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
        # Store pending login in session
        session['pending_mfa_user_id'] = user.id
        session['mfa_verified'] = False

        return jsonify({
            'message': 'MFA verification required',
            'mfa_required': True,
            'user_id': user.id
        }), 200

    # Record successful login
    user.record_successful_login()
    db.session.commit()

    # Mark MFA as verified (not required for this user)
    session['mfa_verified'] = True

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

    # Warn if admin user doesn't have MFA enabled
    if user.is_admin and not user.mfa_enabled:
        response_data['warning'] = 'MFA is required for admin accounts. Please enable it in your security settings.'

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


# ============================================================================
# MFA (Multi-Factor Authentication) Endpoints
# ============================================================================

@auth_bp.route('/mfa/setup', methods=['POST'])
@jwt_required()
def mfa_setup():
    """
    Initiate MFA setup for the current user.

    Returns QR code and backup codes.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.mfa_enabled:
        return jsonify({'error': 'MFA is already enabled'}), 400

    try:
        # Generate MFA secret, QR code, and backup codes
        secret, qr_code, backup_codes = MFAManager.setup_mfa(user.username)

        # Store secret temporarily (not enabled yet)
        user.mfa_secret = secret
        db.session.commit()

        # Hash backup codes for storage
        hashed_codes = MFAManager.hash_backup_codes(backup_codes)

        return jsonify({
            'message': 'MFA setup initiated',
            'qr_code': qr_code,
            'secret': secret,  # For manual entry
            'backup_codes': backup_codes,  # Show once, user must save
            'instructions': 'Scan the QR code with your authenticator app and verify with a code to enable MFA'
        }), 200

    except Exception as e:
        logger.error(f"Error setting up MFA: {str(e)}")
        return jsonify({'error': 'Failed to setup MFA'}), 500


@auth_bp.route('/mfa/verify-setup', methods=['POST'])
@jwt_required()
def mfa_verify_setup():
    """
    Verify and enable MFA by confirming a code from the authenticator app.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.mfa_enabled:
        return jsonify({'error': 'MFA is already enabled'}), 400

    if not user.mfa_secret:
        return jsonify({'error': 'MFA setup not initiated. Call /mfa/setup first'}), 400

    data = request.get_json()
    code = data.get('code')
    backup_codes_hashed = data.get('backup_codes_hashed')  # From setup response

    if not code:
        return jsonify({'error': 'Verification code required'}), 400

    # Verify the code
    if not MFAManager.validate_mfa_setup(user.mfa_secret, code):
        return jsonify({'error': 'Invalid verification code'}), 400

    try:
        # Enable MFA
        user.mfa_enabled = True
        user.mfa_backup_codes = backup_codes_hashed if backup_codes_hashed else []
        db.session.commit()

        logger.info(f"MFA enabled for user: {user.username}")

        return jsonify({
            'message': 'MFA enabled successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error enabling MFA: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to enable MFA'}), 500


@auth_bp.route('/mfa/verify', methods=['POST'])
def mfa_verify_login():
    """
    Verify MFA code during login.
    """
    data = request.get_json()
    code = data.get('code')
    user_id = data.get('user_id') or session.get('pending_mfa_user_id')
    use_backup = data.get('use_backup', False)

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    if not code:
        return jsonify({'error': 'Verification code required'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.mfa_enabled:
        return jsonify({'error': 'MFA is not enabled for this user'}), 400

    verified = False

    try:
        if use_backup:
            # Verify backup code
            is_valid, code_hash = MFAManager.verify_backup_code(code, user.mfa_backup_codes or [])

            if is_valid:
                # Mark backup code as used
                user.mfa_backup_codes = MFAManager.mark_backup_code_used(code_hash, user.mfa_backup_codes)
                db.session.commit()
                verified = True
                logger.info(f"Backup code used for user: {user.username}")
            else:
                return jsonify({'error': 'Invalid or already used backup code'}), 400
        else:
            # Verify TOTP code
            verified = MFAManager.verify_totp(user.mfa_secret, code)

            if not verified:
                return jsonify({'error': 'Invalid verification code'}), 400

        # MFA verified successfully
        if verified:
            # Record successful login
            user.record_successful_login()
            db.session.commit()

            # Mark MFA as verified in session
            session['mfa_verified'] = True
            session.pop('pending_mfa_user_id', None)

            # Create access token
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(minutes=15)
            )

            # Get remaining backup codes
            unused_codes = MFAManager.get_unused_backup_codes_count(user.mfa_backup_codes or [])

            response_data = {
                'message': 'MFA verification successful',
                'access_token': access_token,
                'user': user.to_dict()
            }

            # Warn if running low on backup codes
            if use_backup and unused_codes <= 3:
                response_data['warning'] = f'You have {unused_codes} backup codes remaining. Consider generating new ones.'

            return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error verifying MFA: {str(e)}")
        return jsonify({'error': 'MFA verification failed'}), 500


@auth_bp.route('/mfa/disable', methods=['POST'])
@jwt_required()
def mfa_disable():
    """
    Disable MFA for the current user.
    Requires password confirmation.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.mfa_enabled:
        return jsonify({'error': 'MFA is not enabled'}), 400

    # Admin users cannot disable MFA without approval
    if user.is_admin:
        return jsonify({
            'error': 'Admin users cannot disable MFA without administrator approval',
            'contact': 'Please contact your system administrator'
        }), 403

    data = request.get_json()
    password = data.get('password')

    if not password:
        return jsonify({'error': 'Password confirmation required'}), 400

    # Verify password
    if not user.check_password(password):
        return jsonify({'error': 'Invalid password'}), 401

    try:
        # Disable MFA
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_backup_codes = None
        db.session.commit()

        # Clear session MFA flag
        session['mfa_verified'] = False

        logger.info(f"MFA disabled for user: {user.username}")

        return jsonify({
            'message': 'MFA disabled successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error disabling MFA: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to disable MFA'}), 500


@auth_bp.route('/mfa/backup-codes', methods=['POST'])
@jwt_required()
def generate_new_backup_codes():
    """
    Generate new backup codes.
    Invalidates all old backup codes.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.mfa_enabled:
        return jsonify({'error': 'MFA is not enabled'}), 400

    data = request.get_json()
    password = data.get('password')

    if not password:
        return jsonify({'error': 'Password confirmation required'}), 400

    # Verify password
    if not user.check_password(password):
        return jsonify({'error': 'Invalid password'}), 401

    try:
        # Generate new backup codes
        backup_codes = MFAManager.generate_backup_codes()
        hashed_codes = MFAManager.hash_backup_codes(backup_codes)

        # Replace old backup codes
        user.mfa_backup_codes = hashed_codes
        db.session.commit()

        logger.info(f"New backup codes generated for user: {user.username}")

        return jsonify({
            'message': 'New backup codes generated',
            'backup_codes': backup_codes,  # Show once, user must save
            'warning': 'Save these codes securely. They cannot be recovered.'
        }), 200

    except Exception as e:
        logger.error(f"Error generating backup codes: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to generate backup codes'}), 500


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

    unused_backup_codes = 0
    if user.mfa_enabled and user.mfa_backup_codes:
        unused_backup_codes = MFAManager.get_unused_backup_codes_count(user.mfa_backup_codes)

    return jsonify({
        'mfa_enabled': user.mfa_enabled,
        'mfa_required': MFAManager.check_mfa_required(user),
        'is_admin': user.is_admin,
        'backup_codes_remaining': unused_backup_codes,
        'session_verified': session.get('mfa_verified', False)
    }), 200
