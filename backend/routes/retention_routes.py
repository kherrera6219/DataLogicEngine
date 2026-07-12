"""
Data Retention API Routes

Provides admin endpoints for managing data retention policies.
"""

import logging
from flask import Blueprint, jsonify, request

from backend.auth.api_decorators import api_admin_required
from backend.retention_service import DataRetentionService, RetentionCategory

logger = logging.getLogger(__name__)

retention_bp = Blueprint('retention', __name__, url_prefix='/api/v1/retention')


@retention_bp.route('/policies', methods=['GET'])
@api_admin_required
def list_policies():
    """
    List all data retention policies.
    
    Returns:
        JSON list of all retention policies with their configurations
    """
    try:
        service = DataRetentionService()
        policies = service.list_policies()
        
        return jsonify({
            'success': True,
            'data': {
                'policies': policies,
                'categories': [c.value for c in RetentionCategory]
            }
        })
    except Exception:
        logger.exception("Error listing retention policies")
        return jsonify({
            'success': False,
            'error': 'Retention policies are unavailable'
        }), 500


@retention_bp.route('/policies/<category>', methods=['GET'])
@api_admin_required
def get_policy(category: str):
    """
    Get a specific retention policy.
    
    Args:
        category: The retention category name
        
    Returns:
        JSON with the policy configuration
    """
    try:
        retention_category = RetentionCategory(category)
        service = DataRetentionService()
        policy = service.get_policy(retention_category)
        
        if not policy:
            return jsonify({
                'success': False,
                'error': f'No policy found for category: {category}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'category': policy.category.value,
                'retention_days': policy.retention_days,
                'description': policy.description,
                'enabled': policy.enabled,
                'archive_before_delete': policy.archive_before_delete,
                'cutoff_date': service.get_cutoff_date(retention_category).isoformat()
            }
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'Invalid category: {category}'
        }), 400
    except Exception:
        logger.exception("Error getting retention policy")
        return jsonify({
            'success': False,
            'error': 'Retention policy is unavailable'
        }), 500


@retention_bp.route('/policies/<category>', methods=['PUT'])
@api_admin_required
def update_policy(category: str):
    """
    Update a retention policy.
    
    Args:
        category: The retention category name
        
    Request Body:
        retention_days: Number of days to retain data
        archive_before_delete: Whether to archive before deletion (optional)
        enabled: Whether the policy is active (optional)
        
    Returns:
        JSON with the updated policy
    """
    try:
        retention_category = RetentionCategory(category)
        data = request.get_json()
        
        if not data or 'retention_days' not in data:
            return jsonify({
                'success': False,
                'error': 'retention_days is required'
            }), 400
        
        retention_days = int(data['retention_days'])
        if retention_days < 1:
            return jsonify({
                'success': False,
                'error': 'retention_days must be at least 1'
            }), 400
        
        service = DataRetentionService()
        policy = service.set_policy(
            category=retention_category,
            retention_days=retention_days,
            archive_before_delete=data.get('archive_before_delete', True),
            enabled=data.get('enabled', True)
        )
        
        logger.info(f"Retention policy updated: {category} = {retention_days} days")
        
        return jsonify({
            'success': True,
            'data': {
                'category': policy.category.value,
                'retention_days': policy.retention_days,
                'description': policy.description,
                'enabled': policy.enabled,
                'archive_before_delete': policy.archive_before_delete
            }
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid category or retention value'
        }), 400
    except Exception:
        logger.exception("Error updating retention policy")
        return jsonify({
            'success': False,
            'error': 'Retention policy update failed'
        }), 500


@retention_bp.route('/cleanup', methods=['POST'])
@api_admin_required
def run_cleanup():
    """
    Run data retention cleanup.
    
    Query Parameters:
        dry_run: If 'true', only report what would be deleted (default: true)
        
    Returns:
        JSON with cleanup results
    """
    try:
        dry_run = request.args.get('dry_run', 'true').lower() == 'true'
        
        service = DataRetentionService()
        results = service.run_cleanup(dry_run=dry_run)
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception:
        logger.exception("Error running retention cleanup")
        return jsonify({
            'success': False,
            'error': 'Retention cleanup failed'
        }), 500


@retention_bp.route('/health', methods=['GET'])
@api_admin_required
def health_check():
    """Health check for retention service."""
    try:
        service = DataRetentionService()
        health = service.check_health()
        
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception:
        logger.exception("Error checking retention service health")
        return jsonify({
            'success': False,
            'error': 'Retention service health is unavailable'
        }), 500
