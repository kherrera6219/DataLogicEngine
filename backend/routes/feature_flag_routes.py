"""
Feature Flag Routes

Runtime endpoints for reading and managing feature flags.
- GET  /api/v1/feature-flags          — public: returns current flag state for the caller
- PATCH /api/v1/admin/feature-flags/<key> — admin: toggle a flag value remotely
- GET  /api/v1/admin/feature-flags/audit  — admin: audit trail for flag changes
"""

import logging
from flask import Blueprint, jsonify, request

from extensions import db
from backend.auth.api_decorators import (
    api_session_login_required,
    current_user_is_owner,
    get_authenticated_principal,
)

logger = logging.getLogger(__name__)

feature_flag_bp = Blueprint('feature_flags', __name__)


def _admin_required(fn):
    """Simple decorator that returns 403 for non-admins."""
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_authenticated_principal()
        if not getattr(user, 'is_authenticated', True) or not current_user_is_owner():
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)

    return wrapper


@feature_flag_bp.route('/api/v1/feature-flags', methods=['GET'])
@api_session_login_required
def get_feature_flags():
    """Return the current feature flag state for the authenticated user."""
    from models import FeatureFlag
    flags = FeatureFlag.query.all()
    user = get_authenticated_principal()
    user_role = getattr(user, 'role', 'user')

    result = {}
    for flag in flags:
        # Evaluate target_roles restriction.
        target_roles = flag.target_roles
        if target_roles and isinstance(target_roles, list) and user_role not in target_roles:
            continue
        result[flag.flag_key] = {
            'value': flag.value,
            'is_locked': flag.is_locked,
            'rollout_percentage': flag.rollout_percentage,
        }
    return jsonify({'success': True, 'flags': result})


@feature_flag_bp.route('/api/v1/admin/feature-flags/<string:flag_key>', methods=['PATCH'])
@api_session_login_required
@_admin_required
def update_feature_flag(flag_key: str):
    """Toggle or update a feature flag (admin only)."""
    from models import FeatureFlag, FeatureFlagAuditEvent
    data = request.get_json() or {}
    user = get_authenticated_principal()

    flag = FeatureFlag.query.filter_by(flag_key=flag_key).first()
    if not flag:
        # Auto-create the flag if it doesn't exist yet.
        flag = FeatureFlag(flag_key=flag_key, value=False)
        db.session.add(flag)

    old_value = flag.value

    if 'value' in data:
        flag.value = bool(data['value'])
    if 'rollout_percentage' in data:
        pct = int(data['rollout_percentage'])
        flag.rollout_percentage = max(0, min(100, pct))
    if 'target_roles' in data:
        flag.target_roles = data['target_roles'] if isinstance(data['target_roles'], list) else None
    if 'is_locked' in data:
        flag.is_locked = bool(data['is_locked'])
    if 'description' in data:
        flag.description = str(data['description'])

    flag.updated_by = user.id

    # Write immutable audit record.
    audit = FeatureFlagAuditEvent(
        flag_key=flag_key,
        old_value=old_value,
        new_value=flag.value,
        actor_id=user.id,
        actor_username=getattr(user, 'username', None),
        change_reason=data.get('reason'),
        source='api',
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'success': True, 'flag': flag.to_dict()})


@feature_flag_bp.route('/api/v1/admin/feature-flags/audit', methods=['GET'])
@api_session_login_required
@_admin_required
def get_feature_flag_audit():
    """Return the audit trail for all feature flag changes (admin only)."""
    from models import FeatureFlagAuditEvent
    limit = min(int(request.args.get('limit', 100)), 500)
    flag_key = request.args.get('flag_key')

    query = FeatureFlagAuditEvent.query.order_by(FeatureFlagAuditEvent.created_at.desc())
    if flag_key:
        query = query.filter_by(flag_key=flag_key)

    events = query.limit(limit).all()
    return jsonify({'success': True, 'events': [e.to_dict() for e in events]})
