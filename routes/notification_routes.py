"""
Notification Preferences Routes

Provides endpoints for getting and saving per-user notification settings.
"""

import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/user/notifications')

# Default preferences applied when a user has no stored prefs.
_DEFAULTS: dict = {
    'email_on_run_complete': True,
    'email_on_run_failed': True,
    'email_on_simulation_complete': False,
    'inapp_run_complete': True,
    'inapp_run_failed': True,
    'inapp_simulation_complete': True,
    'inapp_system_alerts': True,
    'digest_frequency': 'none',  # none | daily | weekly
}


def _get_user_prefs() -> dict:
    """Read notification prefs from runtime settings for the current user."""
    from backend.storage.runtime_settings import load_storage_settings
    settings = load_storage_settings()
    all_prefs = settings.get('notification_prefs', {})
    user_prefs = all_prefs.get(str(current_user.id), {})
    return {**_DEFAULTS, **user_prefs}


@notification_bp.route('', methods=['GET'])
@login_required
def get_notification_prefs():
    """Return the current user's notification preferences."""
    return jsonify({'success': True, 'preferences': _get_user_prefs()})


@notification_bp.route('', methods=['POST'])
@login_required
def save_notification_prefs():
    """Persist notification preference updates for the current user."""
    data = request.get_json() or {}

    # Only allow known keys through.
    patch = {k: data[k] for k in _DEFAULTS if k in data}

    try:
        from backend.storage.runtime_settings import load_storage_settings, save_storage_settings
        settings = load_storage_settings()
        all_prefs = settings.get('notification_prefs', {})
        user_prefs = dict(all_prefs.get(str(current_user.id), {}))
        user_prefs.update(patch)
        all_prefs[str(current_user.id)] = user_prefs
        settings['notification_prefs'] = all_prefs
        save_storage_settings(settings)

        return jsonify({'success': True, 'preferences': {**_DEFAULTS, **user_prefs}})
    except Exception as e:
        logger.error(f"Failed to save notification prefs for user {current_user.id}: {e}")
        return jsonify({'success': False, 'error': 'Failed to save preferences'}), 500
