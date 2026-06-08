"""
Notification Preferences Routes

Provides endpoints for getting and saving per-user notification settings.
Backed by the UserNotificationPreference SQL table (one row per user).
"""

import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/user/notifications')

# Valid values for digest_frequency.
_DIGEST_FREQUENCIES = {'none', 'daily', 'weekly'}

# Keys accepted in PATCH/POST body — must match UserNotificationPreference columns.
_BOOL_KEYS = (
    'email_on_run_complete',
    'email_on_run_failed',
    'email_on_simulation_complete',
    'inapp_run_complete',
    'inapp_run_failed',
    'inapp_simulation_complete',
    'inapp_system_alerts',
)


def _get_or_create_prefs():
    """Return the UserNotificationPreference row for the current user, creating
    it with defaults if it does not yet exist."""
    from models import UserNotificationPreference
    from extensions import db

    prefs = UserNotificationPreference.query.filter_by(user_id=current_user.id).first()
    if prefs is None:
        prefs = UserNotificationPreference(user_id=current_user.id)
        db.session.add(prefs)
        db.session.flush()   # assign PK; caller owns the commit
    return prefs


@notification_bp.route('', methods=['GET'])
@login_required
def get_notification_prefs():
    """Return the current user's notification preferences."""
    try:
        from extensions import db
        prefs = _get_or_create_prefs()
        db.session.commit()
        return jsonify({'success': True, 'preferences': prefs.to_dict()})
    except Exception as e:
        from extensions import db
        db.session.rollback()
        logger.error("Failed to load notification prefs for user %s: %s", current_user.id, e)
        return jsonify({'success': False, 'error': 'Failed to load preferences'}), 500


@notification_bp.route('', methods=['POST'])
@login_required
def save_notification_prefs():
    """Persist notification preference updates for the current user."""
    data = request.get_json() or {}

    # Validate digest_frequency if provided.
    if 'digest_frequency' in data and data['digest_frequency'] not in _DIGEST_FREQUENCIES:
        return jsonify({
            'success': False,
            'error': f"digest_frequency must be one of: {', '.join(sorted(_DIGEST_FREQUENCIES))}",
        }), 400

    try:
        from extensions import db
        prefs = _get_or_create_prefs()

        # Apply boolean toggles.
        for key in _BOOL_KEYS:
            if key in data:
                value = data[key]
                if not isinstance(value, bool):
                    return jsonify({'success': False, 'error': f"'{key}' must be a boolean"}), 400
                setattr(prefs, key, value)

        # Apply digest_frequency if provided.
        if 'digest_frequency' in data:
            prefs.digest_frequency = data['digest_frequency']

        db.session.commit()
        return jsonify({'success': True, 'preferences': prefs.to_dict()})
    except Exception as e:
        from extensions import db
        db.session.rollback()
        logger.error("Failed to save notification prefs for user %s: %s", current_user.id, e)
        return jsonify({'success': False, 'error': 'Failed to save preferences'}), 500
