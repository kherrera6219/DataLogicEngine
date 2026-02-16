"""
Tracing API Endpoints

REST API for accessing trace data with RBAC-aware filtering.
"""

import json
from flask import Blueprint, jsonify, request, Response
from flask_login import login_required, current_user

from extensions import db
from backend.security.export_integrity import build_trace_export_document
from models import (
    TraceRun, TraceStage, TraceEvidence, TraceClaim,
    TraceAxisVector, TracePersona, TraceKAInvocation,
    TracePolicyDecision, TraceMemoryEvent, TraceArtifact,
    ChatSession, TraceSpan, StageLog, TraceExport,
    ClaimEvidenceLink, ComplianceMapping
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
    
    export_options = request.get_json(silent=True) or {}
    sign_bundle = bool(export_options.get("sign_bundle", True))
    encrypt_bundle = bool(export_options.get("encrypt_bundle", False))

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

    try:
        export_document = build_trace_export_document(
            bundle,
            exported_by=str(current_user.id),
            sign_bundle=sign_bundle,
            encrypt_bundle=encrypt_bundle,
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    export_suffix = "encrypted" if encrypt_bundle else "signed"
    return Response(
        json.dumps(export_document, indent=2, default=str),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=run_{run_id}_{export_suffix}.json'}
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
    
    # Feature: Automated replay is currently scheduled for future release.
    # Current implementation provides metadata for external replay orchestration.
    
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


# ============== Phase 4: Sessions ==============

@trace_bp.route('/sessions', methods=['GET'])
@login_required
def list_sessions():
    """List chat sessions for the current user."""
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(
        ChatSession.updated_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'sessions': [s.to_dict() for s in sessions.items],
        'total': sessions.total,
        'page': page,
        'pages': sessions.pages
    })


@trace_bp.route('/sessions', methods=['POST'])
@login_required
def create_session():
    """Create a new chat session."""
    
    data = request.get_json() or {}
    
    session = ChatSession(
        user_id=current_user.id,
        title=data.get('title', 'New Chat'),
        mode=data.get('mode', 'chat'),
        constraints=data.get('constraints')
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify(session.to_dict()), 201


@trace_bp.route('/sessions/<session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    """Get a specific session."""
    
    session = ChatSession.query.filter_by(session_id=session_id).first_or_404()
    
    if session.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(session.to_dict())


@trace_bp.route('/sessions/<session_id>', methods=['PATCH'])
@login_required
def update_session(session_id):
    """Update a session (title, mode, constraints)."""
    
    session = ChatSession.query.filter_by(session_id=session_id).first_or_404()
    
    if session.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json() or {}
    
    if 'title' in data:
        session.title = data['title']
    if 'mode' in data:
        session.mode = data['mode']
    if 'constraints' in data:
        session.constraints = data['constraints']
    
    db.session.commit()
    
    return jsonify(session.to_dict())


# ============== Phase 4: Spans (OpenTelemetry) ==============

@trace_bp.route('/runs/<run_id>/spans', methods=['GET'])
@login_required
def get_run_spans(run_id):
    """Get OpenTelemetry spans for a run."""
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    spans = TraceSpan.query.filter_by(run_id=run_id).order_by(TraceSpan.start_at).all()
    
    return jsonify({
        'spans': [s.to_dict() for s in spans]
    })


# ============== Phase 4: Logs ==============

@trace_bp.route('/runs/<run_id>/logs', methods=['GET'])
@login_required
def get_run_logs(run_id):
    """Get logs for a run."""
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    stage_id = request.args.get('stage_id')
    level = request.args.get('level')
    
    query = StageLog.query.filter_by(run_id=run_id)
    
    if stage_id:
        query = query.filter_by(stage_id=stage_id)
    if level:
        query = query.filter_by(level=level)
    
    logs = query.order_by(StageLog.timestamp).all()
    
    return jsonify({
        'logs': [l.to_dict() for l in logs]
    })


# ============== Phase 4: Exports ==============

@trace_bp.route('/exports', methods=['GET'])
@login_required
def list_exports():
    """List exports for the current user."""
    
    exports = TraceExport.query.filter_by(user_id=current_user.id).order_by(
        TraceExport.created_at.desc()
    ).limit(50).all()
    
    return jsonify({
        'exports': [e.to_dict() for e in exports]
    })


@trace_bp.route('/exports/<export_id>', methods=['GET'])
@login_required
def get_export(export_id):
    """Get a specific export."""
    
    export = TraceExport.query.filter_by(export_id=export_id).first_or_404()
    
    if export.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(export.to_dict())


@trace_bp.route('/exports/<export_id>/download', methods=['GET'])
@login_required
def download_export(export_id):
    """Download an export bundle."""
    
    export = TraceExport.query.filter_by(export_id=export_id).first_or_404()
    
    if export.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    if export.status != 'ready':
        return jsonify({'error': 'Export not ready'}), 400
    
    # For now, return the bundle reference
    # In production, this would stream from blob storage
    return jsonify({
        'bundle_ref': export.bundle_ref,
        'manifest_hash': export.manifest_hash,
        'file_size_bytes': export.file_size_bytes
    })


# ============== Claim-Evidence Links ==============

@trace_bp.route('/runs/<run_id>/claims/<claim_id>/evidence', methods=['GET'])
@login_required
def get_claim_evidence(run_id, claim_id):
    """Get evidence linked to a specific claim."""
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    links = ClaimEvidenceLink.query.filter_by(claim_id=claim_id).all()
    
    # Get full evidence items
    evidence_list = []
    for link in links:
        evidence = TraceEvidence.query.filter_by(evidence_id=link.evidence_id).first()
        if evidence:
            item = evidence.to_dict()
            item['link'] = link.to_dict()
            evidence_list.append(item)
    
    return jsonify({
        'claim_id': claim_id,
        'evidence': evidence_list
    })


# ============== Compliance Mapping ==============

@trace_bp.route('/runs/<run_id>/compliance', methods=['GET'])
@login_required
def get_run_compliance(run_id):
    """Get compliance framework mappings for a run."""
    
    run = TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    if run.user_id != current_user.id and not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Access denied'}), 403
    
    framework = request.args.get('framework')
    
    query = ComplianceMapping.query.filter_by(run_id=run_id)
    if framework:
        query = query.filter_by(framework=framework)
    
    mappings = query.all()
    
    # Group by framework
    by_framework = {}
    for m in mappings:
        if m.framework not in by_framework:
            by_framework[m.framework] = []
        by_framework[m.framework].append(m.to_dict())
    
    return jsonify({
        'run_id': run_id,
        'compliance_mappings': by_framework,
        'total': len(mappings)
    })


@trace_bp.route('/runs/<run_id>/compliance', methods=['POST'])
@login_required
def add_compliance_mapping(run_id):
    """Add a compliance mapping for a run (admin only)."""
    
    # Only admins can add compliance mappings
    if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        return jsonify({'error': 'Admin access required'}), 403
    
    TraceRun.query.filter_by(run_id=run_id).first_or_404()
    
    data = request.get_json() or {}
    if not data.get('framework') or not data.get('control_id'):
        return jsonify({'error': 'framework and control_id required'}), 400
    
    mapping = ComplianceMapping(
        run_id=run_id,
        framework=data['framework'],
        control_id=data['control_id'],
        relevance_reason=data.get('relevance_reason'),
        evidence_ids=data.get('evidence_ids')
    )
    
    db.session.add(mapping)
    db.session.commit()
    
    return jsonify(mapping.to_dict()), 201
