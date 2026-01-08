"""
Tracing API Endpoints

REST API for accessing trace data with RBAC-aware filtering.
"""

import uuid
import json
import hashlib
from datetime import datetime, UTC
from flask import Blueprint, jsonify, request, Response
from flask_login import login_required, current_user

from extensions import db
from backend.tracing.models import (
    TraceRun, TraceStage, TraceEvidence, TraceClaim,
    TraceAxisVector, TracePersona, TraceKAInvocation,
    TracePolicyDecision, TraceMemoryEvent, TraceArtifact
)

trace_bp = Blueprint('trace', __name__, url_prefix='/api/v1/trace')


# ============== Permission Helpers ==============

TRACE_PERMISSIONS = {
    'TRACE_VIEW_BASIC': ['status', 'timing', 'scores'],
    'TRACE_VIEW_EVIDENCE': ['evidence', 'claims'],
    'TRACE_VIEW_ARTIFACTS': ['artifacts', 'inputs', 'outputs'],
    'TRACE_VIEW_POLICIES': ['policy_decisions'],
    'TRACE_VIEW_MEMORY': ['memory_events'],
    'TRACE_EXPORT_BUNDLE': ['export'],
    'TRACE_VIEW_REDACTED': ['redacted'],
    'TRACE_REPLAY': ['replay']
}


def user_has_permission(permission: str) -> bool:
    """Check if current user has a trace permission."""
    # Default: grant basic permissions to authenticated users
    basic_perms = ['TRACE_VIEW_BASIC', 'TRACE_VIEW_EVIDENCE', 'TRACE_VIEW_ARTIFACTS']
    if permission in basic_perms:
        return True
    
    # Admin gets all permissions
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        return True
    
    # Check user roles for specific permissions
    if hasattr(current_user, 'permissions'):
        return permission in current_user.permissions
    
    return False


def filter_by_permissions(data: dict) -> dict:
    """Filter response data based on user permissions."""
    # For now, return full data - implement redaction as needed
    return data


# ============== Run Endpoints ==============

@trace_bp.route('/runs', methods=['GET'])
@login_required
def list_runs():
    """List trace runs with filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = TraceRun.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    runs = query.order_by(TraceRun.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'runs': [r.to_dict() for r in runs.items],
        'total': runs.total,
        'page': page,
        'per_page': per_page,
        'pages': runs.pages
    })


@trace_bp.route('/runs/<run_id>', methods=['GET'])
@login_required
def get_run(run_id):
    """Get a specific trace run."""
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    # Check access
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(filter_by_permissions(run.to_dict()))


@trace_bp.route('/runs/<run_id>/stages', methods=['GET'])
@login_required
def get_run_stages(run_id):
    """Get stages for a run."""
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    stages = TraceStage.query.filter_by(run_id=run_id).order_by(
        TraceStage.layer_index, TraceStage.step_index
    ).all()
    
    return jsonify({
        'stages': [s.to_dict() for s in stages]
    })


@trace_bp.route('/runs/<run_id>/evidence', methods=['GET'])
@login_required
def get_run_evidence(run_id):
    """Get evidence items for a run."""
    if not user_has_permission('TRACE_VIEW_EVIDENCE'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    evidence = TraceEvidence.query.filter_by(run_id=run_id).all()
    
    return jsonify({
        'evidence': [e.to_dict() for e in evidence]
    })


@trace_bp.route('/runs/<run_id>/claims', methods=['GET'])
@login_required
def get_run_claims(run_id):
    """Get claims for a run."""
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    claims = TraceClaim.query.filter_by(run_id=run_id).all()
    
    return jsonify({
        'claims': [c.to_dict() for c in claims]
    })


@trace_bp.route('/runs/<run_id>/axes', methods=['GET'])
@login_required
def get_run_axes(run_id):
    """Get axis vector for a run."""
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    axis_vector = TraceAxisVector.query.filter_by(run_id=run_id).first()
    
    return jsonify({
        'axes': axis_vector.to_dict() if axis_vector else None
    })


@trace_bp.route('/runs/<run_id>/personas', methods=['GET'])
@login_required
def get_run_personas(run_id):
    """Get persona traces for a run."""
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    personas = TracePersona.query.filter_by(run_id=run_id).all()
    
    return jsonify({
        'personas': [p.to_dict() for p in personas]
    })


@trace_bp.route('/runs/<run_id>/kas', methods=['GET'])
@login_required
def get_run_kas(run_id):
    """Get KA invocation traces for a run."""
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    kas = TraceKAInvocation.query.filter_by(run_id=run_id).all()
    
    return jsonify({
        'kas': [k.to_dict() for k in kas]
    })


@trace_bp.route('/runs/<run_id>/policy', methods=['GET'])
@login_required
def get_run_policy(run_id):
    """Get policy decisions for a run."""
    if not user_has_permission('TRACE_VIEW_POLICIES'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    decisions = TracePolicyDecision.query.filter_by(run_id=run_id).all()
    
    return jsonify({
        'policy_decisions': [d.to_dict() for d in decisions]
    })


@trace_bp.route('/runs/<run_id>/memory', methods=['GET'])
@login_required
def get_run_memory(run_id):
    """Get memory events for a run."""
    if not user_has_permission('TRACE_VIEW_MEMORY'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    events = TraceMemoryEvent.query.filter_by(run_id=run_id).all()
    
    return jsonify({
        'memory_events': [e.to_dict() for e in events]
    })


@trace_bp.route('/runs/<run_id>/metrics', methods=['GET'])
@login_required
def get_run_metrics(run_id):
    """Get observability metrics for a run."""
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    # Aggregate metrics from stages
    stages = TraceStage.query.filter_by(run_id=run_id).all()
    
    total_duration = sum(s.duration_ms or 0 for s in stages)
    total_tokens_in = sum((s.metrics or {}).get('tokens_in', 0) for s in stages)
    total_tokens_out = sum((s.metrics or {}).get('tokens_out', 0) for s in stages)
    total_retrievals = sum((s.metrics or {}).get('retrieval_count', 0) for s in stages)
    
    return jsonify({
        'metrics': {
            'total_duration_ms': total_duration,
            'total_tokens_in': total_tokens_in,
            'total_tokens_out': total_tokens_out,
            'total_retrievals': total_retrievals,
            'stage_count': len(stages),
            'confidence': run.confidence,
            'entropy': run.entropy
        }
    })


# ============== Export Endpoint ==============

@trace_bp.route('/runs/<run_id>/export', methods=['POST'])
@login_required
def export_run(run_id):
    """Export full run bundle."""
    if not user_has_permission('TRACE_EXPORT_BUNDLE'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    # Build export bundle
    bundle = {
        'run': run.to_dict(),
        'stages': [s.to_dict() for s in run.stages.all()],
        'evidence': [e.to_dict() for e in run.evidence_items.all()],
        'claims': [c.to_dict() for c in run.claims.all()],
        'personas': [p.to_dict() for p in run.personas.all()],
        'kas': [k.to_dict() for k in run.ka_invocations.all()],
        'policy': [d.to_dict() for d in run.policy_decisions.all()],
        'memory': [m.to_dict() for m in run.memory_events.all()]
    }
    
    # Add axis vector
    axis_vector = TraceAxisVector.query.filter_by(run_id=run_id).first()
    bundle['axes'] = axis_vector.to_dict() if axis_vector else None
    
    # Compute hashes
    hashes = {}
    for key, value in bundle.items():
        if value:
            hashes[key] = hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
    
    bundle['hashes'] = hashes
    bundle['manifest'] = {
        'exported_at': datetime.now(UTC).isoformat(),
        'exported_by': current_user.id,
        'version': '1.0'
    }
    
    return Response(
        json.dumps(bundle, indent=2, default=str),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=run_{run_id}.json'}
    )


# ============== Replay Endpoint ==============

@trace_bp.route('/runs/<run_id>/replay', methods=['POST'])
@login_required
def replay_run(run_id):
    """Replay a run (placeholder for implementation)."""
    if not user_has_permission('TRACE_REPLAY'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json() or {}
    same_seed = data.get('same_seed', True)
    from_stage = data.get('from_stage')
    
    # TODO: Implement actual replay logic
    # This would create a new TraceRun with same inputs and snapshot
    
    return jsonify({
        'message': 'Replay initiated',
        'original_run_id': run_id,
        'same_seed': same_seed,
        'from_stage': from_stage,
        'new_run_id': None  # Would be set after actual replay
    })


# ============== Artifacts Endpoint ==============

@trace_bp.route('/runs/<run_id>/artifacts/<artifact_id>', methods=['GET'])
@login_required
def get_artifact(run_id, artifact_id):
    """Get a specific artifact."""
    if not user_has_permission('TRACE_VIEW_ARTIFACTS'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    artifact = TraceArtifact.query.filter_by(
        artifact_id=artifact_id, run_id=run_id
    ).first_or_404()
    
    return jsonify(artifact.to_dict())
