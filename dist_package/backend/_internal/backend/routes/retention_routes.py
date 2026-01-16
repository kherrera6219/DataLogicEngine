"""
Data Retention API Routes

Provides admin endpoints for managing data retention policies.
"""

import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required

from backend.decorators import admin_required
from backend.retention_service import DataRetentionService, RetentionCategory

logger = logging.getLogger(__name__)

retention_bp = Blueprint('retention', __name__, url_prefix='/api/v1/retention')


@retention_bp.route('/policies', methods=['GET'])
@login_required
@admin_required
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
    except Exception as e:
        logger.error(f"Error listing retention policies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@retention_bp.route('/policies/<category>', methods=['GET'])
@login_required
@admin_required
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
    except Exception as e:
        logger.error(f"Error getting retention policy: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@retention_bp.route('/policies/<category>', methods=['PUT'])
@login_required
@admin_required
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
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid category or value: {e}'
        }), 400
    except Exception as e:
        logger.error(f"Error updating retention policy: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@retention_bp.route('/cleanup', methods=['POST'])
@login_required
@admin_required
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
    except Exception as e:
        logger.error(f"Error running retention cleanup: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@retention_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for retention service."""
    try:
        service = DataRetentionService()
        health = service.check_health()
        
        return jsonify({
            'success': True,
            'data': health
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
