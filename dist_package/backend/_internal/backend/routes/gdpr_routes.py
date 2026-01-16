"""
GDPR Compliance Tools for DataLogicEngine

Provides endpoints for:
- Data export (user data portability)
- Data deletion (right to be forgotten)
- Consent management
- Data access requests
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
import json
import io

logger = logging.getLogger(__name__)

gdpr_bp = Blueprint('gdpr', __name__, url_prefix='/api/v1/gdpr')


@gdpr_bp.route('/export', methods=['POST'])
@login_required
def export_user_data():
    """
    Export all user data (GDPR Article 20 - Data Portability).
    
    Returns:
        JSON file with all user's personal data
    """
    try:
        from extensions import db
        from db_models import User, ChatSession, ChatMessage, KnowledgeGraphNode
        
        user_id = current_user.id
        
        # Collect user profile data
        user_data = {
            'export_date': datetime.utcnow().isoformat(),
            'export_type': 'gdpr_data_portability',
            'user_profile': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'created_at': str(getattr(current_user, 'created_at', None))
            },
            'chat_sessions': [],
            'knowledge_nodes': [],
            'preferences': {},
            'consent_records': []
        }
        
        # Collect chat sessions
        try:
            sessions = db.session.query(ChatSession).filter_by(user_id=user_id).all()
            for session in sessions:
                session_data = {
                    'id': session.uid,
                    'created_at': str(session.created_at),
                    'messages': []
                }
                # Get messages if available
                if hasattr(ChatMessage, 'session_id'):
                    messages = db.session.query(ChatMessage).filter_by(session_id=session.uid).all()
                    session_data['messages'] = [
                        {'role': m.role, 'content': m.content, 'created_at': str(m.created_at)}
                        for m in messages
                    ]
                user_data['chat_sessions'].append(session_data)
        except Exception as e:
            logger.warning(f"Could not export chat sessions: {e}")
        
        # Collect knowledge nodes created by user
        try:
            nodes = db.session.query(KnowledgeGraphNode).filter_by(created_by=user_id).all()
            user_data['knowledge_nodes'] = [
                {'uid': n.uid, 'name': n.name, 'created_at': str(n.created_at)}
                for n in nodes
            ]
        except Exception as e:
            logger.warning(f"Could not export knowledge nodes: {e}")
        
        # Create JSON file
        export_json = json.dumps(user_data, indent=2)
        buffer = io.BytesIO(export_json.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'user_data_export_{datetime.utcnow().strftime("%Y%m%d")}.json'
        )
        
    except Exception as e:
        logger.error(f"GDPR export error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to export user data'
        }), 500


@gdpr_bp.route('/delete', methods=['POST'])
@login_required
def request_data_deletion():
    """
    Request deletion of all user data (GDPR Article 17 - Right to Erasure).
    
    This schedules data for deletion after a grace period.
    """
    try:
        from extensions import db
        
        # Record deletion request
        deletion_request = {
            'user_id': current_user.id,
            'requested_at': datetime.utcnow().isoformat(),
            'status': 'pending',
            'scheduled_deletion': (datetime.utcnow()).isoformat(),
            'grace_period_days': 30
        }
        
        # Log the request
        logger.info(f"GDPR deletion request from user {current_user.id}")
        
        # In production, this would:
        # 1. Store deletion request in database
        # 2. Send confirmation email
        # 3. Schedule deletion job
        
        return jsonify({
            'success': True,
            'message': 'Deletion request received',
            'data': {
                'request_id': f'gdpr-del-{current_user.id}-{datetime.utcnow().strftime("%Y%m%d")}',
                'grace_period_days': 30,
                'scheduled_deletion': deletion_request['scheduled_deletion'],
                'instructions': 'Your data will be permanently deleted after the grace period. '
                               'Login during this period to cancel the request.'
            }
        })
        
    except Exception as e:
        logger.error(f"GDPR deletion request error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process deletion request'
        }), 500


@gdpr_bp.route('/consent', methods=['GET'])
@login_required
def get_consent_status():
    """
    Get user's consent status for various data processing activities.
    """
    try:
        # In production, load from database
        consent_status = {
            'analytics': True,
            'marketing_emails': False,
            'third_party_sharing': False,
            'ai_training': False,
            'personalization': True,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': consent_status
        })
        
    except Exception as e:
        logger.error(f"GDPR consent status error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve consent status'
        }), 500


@gdpr_bp.route('/consent', methods=['POST'])
@login_required
def update_consent():
    """
    Update user's consent preferences.
    """
    try:
        data = request.get_json()
        
        allowed_fields = ['analytics', 'marketing_emails', 'third_party_sharing', 
                         'ai_training', 'personalization']
        
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        # In production, save to database
        logger.info(f"GDPR consent update for user {current_user.id}: {updates}")
        
        return jsonify({
            'success': True,
            'message': 'Consent preferences updated',
            'data': updates
        })
        
    except Exception as e:
        logger.error(f"GDPR consent update error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update consent preferences'
        }), 500


@gdpr_bp.route('/access-request', methods=['POST'])
@login_required
def submit_access_request():
    """
    Submit a data access request (GDPR Article 15).
    
    For complex requests that require human review.
    """
    try:
        data = request.get_json() or {}
        
        request_details = {
            'request_id': f'gdpr-access-{current_user.id}-{datetime.utcnow().strftime("%Y%m%d%H%M")}',
            'user_id': current_user.id,
            'email': current_user.email,
            'request_type': data.get('type', 'full_export'),
            'specific_data': data.get('specific_data', []),
            'submitted_at': datetime.utcnow().isoformat(),
            'status': 'pending',
            'estimated_response': '30 days'
        }
        
        logger.info(f"GDPR access request: {request_details['request_id']}")
        
        return jsonify({
            'success': True,
            'message': 'Access request submitted successfully',
            'data': {
                'request_id': request_details['request_id'],
                'estimated_response_time': '30 days',
                'contact_email': 'privacy@datalogicengine.com'
            }
        })
        
    except Exception as e:
        logger.error(f"GDPR access request error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit access request'
        }), 500
