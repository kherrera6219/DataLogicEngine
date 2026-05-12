import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from models import UserAIPreferences

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')
logger = logging.getLogger(__name__)


def _get_or_create_prefs(user_id: int) -> UserAIPreferences:
    prefs = UserAIPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = UserAIPreferences(user_id=user_id)
        db.session.add(prefs)
        db.session.commit()
    return prefs


@settings_bp.route('/ai', methods=['GET'])
@login_required
def get_ai_settings():
    prefs = _get_or_create_prefs(current_user.id)
    return jsonify({
        "ai_processing_enabled": prefs.ai_processing_enabled,
        "preferred_provider": prefs.preferred_provider or "auto",
        "preferred_model": prefs.preferred_model,
        "store_chat_history": prefs.store_chat_history,
    })


@settings_bp.route('/ai', methods=['POST'])
@login_required
def update_ai_settings():
    data = request.get_json(silent=True) or {}

    allowed_providers = {'auto', 'openai', 'azure', 'anthropic', 'google'}
    provider = data.get('preferred_provider', 'auto')
    if provider not in allowed_providers:
        return jsonify({"error": "Invalid provider selection"}), 400

    prefs = _get_or_create_prefs(current_user.id)
    prefs.preferred_provider = None if provider == 'auto' else provider
    prefs.preferred_model = data.get('preferred_model') or None
    if 'ai_processing_enabled' in data:
        prefs.ai_processing_enabled = bool(data['ai_processing_enabled'])
    if 'store_chat_history' in data:
        prefs.store_chat_history = bool(data['store_chat_history'])

    db.session.commit()

    logger.info(
        "AI preferences updated",
        extra={
            "user_id": current_user.id,
            "preferred_provider": prefs.preferred_provider,
            "ai_processing_enabled": prefs.ai_processing_enabled,
            "store_chat_history": prefs.store_chat_history,
        },
    )
    return jsonify({"success": True, "settings": prefs.to_dict()})
