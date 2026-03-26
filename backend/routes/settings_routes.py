
import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')
logger = logging.getLogger(__name__)

@settings_bp.route('/ai', methods=['GET'])
@login_required
def get_ai_settings():
    """Get current user AI preferences"""
    # In a real app, these would be columns on the User model
    # For now, we'll return defaults or mocked values if columns don't exist
    prefs = current_user.preferences if hasattr(current_user, 'preferences') else {}
    
    return jsonify({
        "ai_enabled": prefs.get('ai_enabled', True),
        "provider": prefs.get('ai_provider', 'auto'),
        "store_history": prefs.get('store_ai_history', True)
    })

@settings_bp.route('/ai', methods=['POST'])
@login_required
def update_ai_settings():
    """Update user AI preferences"""
    data = request.get_json(silent=True) or {}
    
    # Validation
    allowed_providers = ['auto', 'openai', 'azure', 'anthropic', 'google']
    if data.get('provider') and data['provider'] not in allowed_providers:
        return jsonify({"error": "Invalid provider selection"}), 400

    # In a real app, update the model. 
    # mocking the persistence for this demo since we haven't migrated the User model
    # current_user.preferences = { ...current_user.preferences, ...data }
    # db.session.commit()
    
    # Log update receipt without leaking full preference payloads.
    logger.info(
        "AI settings updated",
        extra={
            "username": getattr(current_user, "username", ""),
            "provider": data.get("provider", "auto"),
            "ai_enabled": bool(data.get("ai_enabled", True)),
            "store_history": bool(data.get("store_history", True)),
        },
    )
    
    return jsonify({
        "success": True,
        "message": "AI preferences updated",
        "settings": {
            "ai_enabled": data.get('ai_enabled', True),
            "provider": data.get('provider', 'auto'),
            "store_history": data.get('store_history', True)
        }
    })
