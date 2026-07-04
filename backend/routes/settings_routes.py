import logging

from flask import Blueprint, g, jsonify, request
from flask_login import current_user

from extensions import db
from backend.auth.api_decorators import api_session_login_required
from backend.llm_gateway.model_defaults import DEFAULT_MODEL_BY_PROVIDER
from models import UserAIPreferences

settings_bp = Blueprint('settings', __name__, url_prefix='/api/v1/settings')
logger = logging.getLogger(__name__)
ALLOWED_AI_PREFERENCE_PROVIDERS = frozenset({"auto", "openai", "google"})


def _get_or_create_prefs(user_id: int) -> UserAIPreferences:
    prefs = UserAIPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = UserAIPreferences(user_id=user_id)
        db.session.add(prefs)
        db.session.commit()
    return prefs


def _authenticated_user_id() -> int:
    auth_user = getattr(g, 'auth_user', None) or current_user
    return auth_user.id


@settings_bp.route('/ai', methods=['GET'])
@api_session_login_required
def get_ai_settings():
    prefs = _get_or_create_prefs(_authenticated_user_id())
    return jsonify({
        "ai_processing_enabled": prefs.ai_processing_enabled,
        "preferred_provider": prefs.preferred_provider or "auto",
        "preferred_model": prefs.preferred_model,
        "store_chat_history": prefs.store_chat_history,
    })


@settings_bp.route('/ai', methods=['POST'])
@api_session_login_required
def update_ai_settings():
    data = request.get_json(silent=True) or {}

    provider = str(data.get('preferred_provider', 'auto')).strip().lower()
    if provider not in ALLOWED_AI_PREFERENCE_PROVIDERS:
        return jsonify({"error": "Invalid provider selection"}), 400

    preferred_model = str(data.get('preferred_model') or '').strip() or None
    if provider == "auto":
        preferred_model = None
    elif preferred_model:
        provider_defaults = {DEFAULT_MODEL_BY_PROVIDER[provider]}
        if preferred_model not in provider_defaults:
            return jsonify({"error": "Invalid model selection"}), 400

    prefs = _get_or_create_prefs(_authenticated_user_id())
    prefs.preferred_provider = None if provider == 'auto' else provider
    prefs.preferred_model = preferred_model
    if 'ai_processing_enabled' in data:
        prefs.ai_processing_enabled = bool(data['ai_processing_enabled'])
    if 'store_chat_history' in data:
        prefs.store_chat_history = bool(data['store_chat_history'])

    db.session.commit()

    logger.info(
        "AI preferences updated",
        extra={
            "user_id": _authenticated_user_id(),
            "preferred_provider": prefs.preferred_provider,
            "ai_processing_enabled": prefs.ai_processing_enabled,
            "store_chat_history": prefs.store_chat_history,
        },
    )
    return jsonify({"success": True, "settings": prefs.to_dict()})
