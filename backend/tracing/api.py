"""
Tracing API Endpoints

REST API for accessing trace data with RBAC-aware filtering.
"""

import json
import logging
import uuid
from datetime import datetime
from flask import Blueprint, abort, jsonify, request, Response
from flask_login import current_user
from werkzeug.exceptions import HTTPException
from backend.auth.api_decorators import api_session_login_required

from extensions import db, limiter
from backend.security.export_integrity import build_trace_export_document
from models import (
    TraceRun, TraceStage, TraceEvidence, TraceClaim,
    TraceAxisVector, TracePersona, TraceKAInvocation,
    TracePolicyDecision, TraceMemoryEvent, TraceArtifact,
    ChatSession, TraceSpan, StageLog, TraceExport,
    ClaimEvidenceLink, ComplianceMapping, KAExecution
)

trace_bp = Blueprint('trace', __name__, url_prefix='/api/v1/trace')
logger = logging.getLogger(__name__)


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


def _user_is_owner() -> bool:
    """Single-mode authorization: the one authenticated OS user is the owner.

    Multi-user roles/admin were removed (auth-deprecation Phase E). The owner has
    full access, so this is always True for an authenticated request. Kept as a
    single function so trace access checks read intentionally and there is one
    place to change if a multi-user model is ever reintroduced.
    """
    return True


def user_has_permission(permission: str) -> bool:
    """Check if current user has a trace permission."""
    # Default: grant basic permissions to authenticated users
    basic_perms = ['TRACE_VIEW_BASIC', 'TRACE_VIEW_EVIDENCE', 'TRACE_VIEW_ARTIFACTS']
    if permission in basic_perms:
        return True
    
    # Admin gets all permissions
    if _user_is_owner():
        return True
    
    # Check user roles for specific permissions
    if hasattr(current_user, 'permissions'):
        return permission in current_user.permissions
    
    return False


def filter_by_permissions(data: dict) -> dict:
    """Filter response data based on user permissions."""
    # For now, return full data - implement redaction as needed
    return data


def _user_can_access_run(run: TraceRun) -> bool:
    return run.user_id == current_user.id or _user_is_owner()


def _parse_run_id(run_id: str):
    try:
        return uuid.UUID(str(run_id))
    except (TypeError, ValueError):
        abort(404)


def _get_run_or_404(run_id: str) -> TraceRun:
    return TraceRun.query.filter_by(run_id=_parse_run_id(run_id)).first_or_404()


def _get_export_or_404(export_id: str) -> TraceExport:
    return TraceExport.query.filter_by(export_id=_parse_run_id(export_id)).first_or_404()


def _latest_accessible_run() -> TraceRun | None:
    query = TraceRun.query
    if not _user_is_owner():
        query = query.filter_by(user_id=current_user.id)
    running = query.filter_by(status='running').order_by(TraceRun.created_at.desc()).first()
    if running:
        return running
    return query.order_by(TraceRun.created_at.desc()).first()


def _confidence_from_payload(payload: dict | None) -> float | None:
    if not isinstance(payload, dict):
        return None
    for key in ("confidence", "confidence_score", "collective_confidence"):
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _count_frost_snapshots(stages: list[TraceStage], run: TraceRun) -> int:
    count = int(run.frost_depth or 0)
    for stage in stages:
        metrics = stage.metrics if isinstance(stage.metrics, dict) else {}
        for key in ("frost_depth", "frost_snapshot_count", "recursive_snapshots"):
            value = metrics.get(key)
            if isinstance(value, int):
                count = max(count, value)
    return count


def _serialize_layer_progress(run: TraceRun) -> dict:
    stages = TraceStage.query.filter_by(run_id=run.run_id).order_by(
        TraceStage.layer_index, TraceStage.step_index
    ).all()
    current_stage = (
        next((stage for stage in stages if stage.status == 'running'), None)
        or next((stage for stage in stages if stage.status not in {'pass', 'completed', 'skipped'}), None)
        or (stages[-1] if stages else None)
    )
    kas = TraceKAInvocation.query.filter_by(run_id=run.run_id).all()
    personas = TracePersona.query.filter_by(run_id=run.run_id).all()
    active_kas = [
        {
            "ka_id": ka.ka_id,
            "ka_name": ka.ka_name,
            "status": ka.status,
            "confidence": _confidence_from_payload(ka.outputs),
            "duration_ms": ka.duration_ms,
        }
        for ka in kas
        if ka.status in {'pending', 'running'}
    ]
    if not active_kas:
        active_kas = [
            {
                "ka_id": ka.ka_id,
                "ka_name": ka.ka_name,
                "status": ka.status,
                "confidence": _confidence_from_payload(ka.outputs),
                "duration_ms": ka.duration_ms,
            }
            for ka in kas[-6:]
        ]

    return {
        "active_run_id": str(run.run_id),
        "status": run.status,
        "current_layer": current_stage.layer_index if current_stage else None,
        "layer_name": current_stage.name if current_stage else None,
        "kas_running": active_kas,
        "confidence_so_far": run.confidence,
        "persona_confidences": [
            {
                "persona": persona.persona_name or persona.persona_type,
                "persona_type": persona.persona_type,
                "confidence": persona.confidence,
                "status": persona.status,
            }
            for persona in personas
        ],
        "frost_snapshot_count": _count_frost_snapshots(stages, run),
        "updated_at": datetime.now().isoformat(),
    }


def _idle_progress_payload(error: str | None = None) -> dict:
    payload = {
        "active_run_id": None,
        "status": "idle",
        "current_layer": None,
        "layer_name": None,
        "kas_running": [],
        "confidence_so_far": None,
        "persona_confidences": [],
        "frost_snapshot_count": 0,
        "updated_at": datetime.now().isoformat(),
    }
    if error:
        payload["degraded"] = True
        payload["error"] = error
    return payload


def _empty_trace_bundle(run_id: str, error: str | None = None) -> dict:
    payload = {
        "run": None,
        "run_id": str(run_id),
        "status": "unavailable",
        "frost_layers": [],
        "stages": [],
        "evidence_sources": [],
        "evidence": [],
        "claims": [],
        "persona_positions": [],
        "personas": [],
        "ka_invocations": [],
        "kas": [],
        "coordinate": None,
        "axes": None,
        "policy_decisions": [],
        "memory_events": [],
        "metrics": {
            "total_duration_ms": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_retrievals": 0,
            "stage_count": 0,
            "confidence": None,
            "entropy": None,
        },
        "export_url": None,
    }
    if error:
        payload["degraded"] = True
        payload["error"] = error
    return payload


def _rollback_trace_session() -> None:
    try:
        db.session.rollback()
    except Exception:
        pass


def _build_trace_bundle(run: TraceRun) -> dict:
    stages = TraceStage.query.filter_by(run_id=run.run_id).order_by(
        TraceStage.layer_index, TraceStage.step_index
    ).all()
    evidence = TraceEvidence.query.filter_by(run_id=run.run_id).all()
    claims = TraceClaim.query.filter_by(run_id=run.run_id).all()
    personas = TracePersona.query.filter_by(run_id=run.run_id).all()
    kas = TraceKAInvocation.query.filter_by(run_id=run.run_id).all()
    axis_vector = TraceAxisVector.query.filter_by(run_id=run.run_id).first()
    policy = TracePolicyDecision.query.filter_by(run_id=run.run_id).all()
    memory = TraceMemoryEvent.query.filter_by(run_id=run.run_id).all()

    stage_duration = sum(stage.duration_ms or 0 for stage in stages)
    total_duration = max(stage_duration, int(run.latency_ms or 0))
    total_tokens_in = sum((stage.metrics or {}).get('tokens_in', 0) for stage in stages)
    total_tokens_out = sum((stage.metrics or {}).get('tokens_out', 0) for stage in stages)
    total_retrievals = sum((stage.metrics or {}).get('retrieval_count', 0) for stage in stages)

    return {
        'run': run.to_dict(),
        'run_id': str(run.run_id),
        'status': run.status,
        'frost_layers': [stage.to_dict() for stage in stages],
        'stages': [stage.to_dict() for stage in stages],
        'evidence_sources': [item.to_dict() for item in evidence],
        'evidence': [item.to_dict() for item in evidence],
        'claims': [claim.to_dict() for claim in claims],
        'persona_positions': [persona.to_dict() for persona in personas],
        'personas': [persona.to_dict() for persona in personas],
        'ka_invocations': [ka.to_dict() for ka in kas],
        'kas': [ka.to_dict() for ka in kas],
        'coordinate': axis_vector.to_dict() if axis_vector else None,
        'axes': axis_vector.to_dict() if axis_vector else None,
        'policy_decisions': [decision.to_dict() for decision in policy],
        'memory_events': [event.to_dict() for event in memory],
        'metrics': {
            'total_duration_ms': total_duration,
            'total_tokens_in': total_tokens_in,
            'total_tokens_out': total_tokens_out,
            'total_retrievals': total_retrievals,
            'stage_count': len(stages),
            'confidence': run.confidence,
            'entropy': run.entropy,
        },
        'export_url': f'/api/v1/trace/runs/{run.run_id}/export',
    }


@trace_bp.route('/live-progress', methods=['GET'])
@limiter.exempt
@api_session_login_required
def get_live_progress():
    """Return current reasoning layer progress for desktop IPC."""
    try:
        run = _latest_accessible_run()
        if not run:
            return jsonify(_idle_progress_payload())
        if not _user_can_access_run(run):
            return jsonify({'error': 'Access denied'}), 403
        return jsonify(_serialize_layer_progress(run))
    except Exception as exc:
        logger.warning("live_progress degraded (startup race or schema mismatch): %s", exc)
        _rollback_trace_session()
        return jsonify(_idle_progress_payload("Trace progress unavailable"))


@trace_bp.route('/ka-execution-feed', methods=['GET'])
@api_session_login_required
def get_ka_execution_feed():
    """Return recent KA execution activity for desktop IPC."""
    requested_limit = request.args.get('limit', 20, type=int)
    if requested_limit is None:
        requested_limit = 20
    limit = min(max(requested_limit, 1), 100)
    query = KAExecution.query
    tenant_id = getattr(current_user, 'tenant_id', None)
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    executions = query.order_by(KAExecution.started_at.desc()).limit(limit).all()
    return jsonify({
        "items": [execution.to_dict() for execution in executions],
        "limit": limit,
        "updated_at": datetime.now().isoformat(),
    })


# ============== Run Endpoints ==============

@trace_bp.route('/runs', methods=['GET'])
@limiter.exempt
@api_session_login_required
def list_runs():
    """List trace runs with filtering."""
    import logging as _logging
    _log = _logging.getLogger(__name__)

    requested_page = request.args.get('page', 1, type=int)
    requested_per_page = request.args.get('per_page', 20, type=int)
    page = max(requested_page or 1, 1)
    per_page = min(max(requested_per_page or 20, 1), 100)
    status = request.args.get('status')

    try:
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
    except Exception as exc:
        # Gracefully degrade during startup race or when trace tables aren't
        # fully migrated yet.  Roll back the broken session so it can be reused
        # and return an empty run list (HTTP 200) rather than a 500 that would
        # surface as an error banner in the Live Trace panel.
        _log.warning("list_runs degraded (startup race or schema mismatch): %s", exc)
        try:
            from extensions import db as _db
            _db.session.rollback()
        except Exception:
            pass
        return jsonify({'runs': [], 'total': 0, 'page': page, 'per_page': per_page, 'pages': 0})


@trace_bp.route('/runs/<run_id>', methods=['GET'])
@api_session_login_required
def get_run(run_id):
    """Get a specific trace run."""
    run = _get_run_or_404(run_id)
    
    # Check access
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(filter_by_permissions(run.to_dict()))


@trace_bp.route('/runs/<run_id>/bundle', methods=['GET'])
@limiter.exempt
@api_session_login_required
def get_run_bundle(run_id):
    """Get an aggregate trace bundle for frontend trace panels."""
    try:
        run = _get_run_or_404(run_id)
    except HTTPException:
        _rollback_trace_session()
        return jsonify(_empty_trace_bundle(run_id, "Trace bundle is not available yet"))
    except Exception as exc:
        logger.warning("trace bundle lookup degraded for %s: %s", run_id, exc)
        _rollback_trace_session()
        return jsonify(_empty_trace_bundle(run_id, "Trace bundle unavailable"))

    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403

    try:
        return jsonify(filter_by_permissions(_build_trace_bundle(run)))
    except Exception as exc:
        logger.warning("trace bundle build degraded for %s: %s", run_id, exc)
        _rollback_trace_session()
        return jsonify(_empty_trace_bundle(run_id, "Trace bundle unavailable"))


@trace_bp.route('/runs/<run_id>/stages', methods=['GET'])
@api_session_login_required
def get_run_stages(run_id):
    """Get stages for a run."""
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    stages = TraceStage.query.filter_by(run_id=run.run_id).order_by(
        TraceStage.layer_index, TraceStage.step_index
    ).all()
    
    return jsonify({
        'stages': [s.to_dict() for s in stages]
    })


@trace_bp.route('/runs/<run_id>/evidence', methods=['GET'])
@api_session_login_required
def get_run_evidence(run_id):
    """Get evidence items for a run."""
    if not user_has_permission('TRACE_VIEW_EVIDENCE'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    evidence = TraceEvidence.query.filter_by(run_id=run.run_id).all()
    
    return jsonify({
        'evidence': [e.to_dict() for e in evidence]
    })


@trace_bp.route('/runs/<run_id>/claims', methods=['GET'])
@api_session_login_required
def get_run_claims(run_id):
    """Get claims for a run."""
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    claims = TraceClaim.query.filter_by(run_id=run.run_id).all()
    
    return jsonify({
        'claims': [c.to_dict() for c in claims]
    })


@trace_bp.route('/runs/<run_id>/axes', methods=['GET'])
@api_session_login_required
def get_run_axes(run_id):
    """Get axis vector for a run."""
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    axis_vector = TraceAxisVector.query.filter_by(run_id=run.run_id).first()
    
    return jsonify({
        'axes': axis_vector.to_dict() if axis_vector else None
    })


@trace_bp.route('/runs/<run_id>/personas', methods=['GET'])
@api_session_login_required
def get_run_personas(run_id):
    """Get persona traces for a run."""
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    personas = TracePersona.query.filter_by(run_id=run.run_id).all()
    
    return jsonify({
        'personas': [p.to_dict() for p in personas]
    })


@trace_bp.route('/runs/<run_id>/kas', methods=['GET'])
@api_session_login_required
def get_run_kas(run_id):
    """Get KA invocation traces for a run."""
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    kas = TraceKAInvocation.query.filter_by(run_id=run.run_id).all()
    
    return jsonify({
        'kas': [k.to_dict() for k in kas]
    })


@trace_bp.route('/runs/<run_id>/policy', methods=['GET'])
@api_session_login_required
def get_run_policy(run_id):
    """Get policy decisions for a run."""
    if not user_has_permission('TRACE_VIEW_POLICIES'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    decisions = TracePolicyDecision.query.filter_by(run_id=run.run_id).all()
    
    return jsonify({
        'policy_decisions': [d.to_dict() for d in decisions]
    })


@trace_bp.route('/runs/<run_id>/memory', methods=['GET'])
@api_session_login_required
def get_run_memory(run_id):
    """Get memory events for a run."""
    if not user_has_permission('TRACE_VIEW_MEMORY'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    events = TraceMemoryEvent.query.filter_by(run_id=run.run_id).all()
    
    return jsonify({
        'memory_events': [e.to_dict() for e in events]
    })


@trace_bp.route('/runs/<run_id>/metrics', methods=['GET'])
@api_session_login_required
def get_run_metrics(run_id):
    """Get observability metrics for a run."""
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    # Aggregate metrics from stages
    stages = TraceStage.query.filter_by(run_id=run.run_id).all()
    
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
@api_session_login_required
def export_run(run_id):
    """Export full run bundle."""
    if not user_has_permission('TRACE_EXPORT_BUNDLE'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    raw_options = request.get_json(silent=True)
    export_options = raw_options if isinstance(raw_options, dict) else {}
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
    axis_vector = TraceAxisVector.query.filter_by(run_id=run.run_id).first()
    bundle['axes'] = axis_vector.to_dict() if axis_vector else None

    try:
        export_document = build_trace_export_document(
            bundle,
            exported_by=str(current_user.id),
            sign_bundle=sign_bundle,
            encrypt_bundle=encrypt_bundle,
        )
    except ValueError:
        logger.exception("Trace export document build rejected the requested options")
        return jsonify({'error': 'Trace export could not be prepared'}), 400

    serialized_export = json.dumps(export_document, indent=2, default=str)
    manifest = export_document.get("manifest", {}) if isinstance(export_document, dict) else {}
    export_id = uuid.uuid4()
    export_record = TraceExport(
        export_id=export_id,
        run_id=run.run_id,
        user_id=current_user.id,
        format="json",
        destination="download",
        status="ready",
        bundle_ref=f"/api/v1/trace/exports/{export_id}/download",
        manifest_hash=manifest.get("envelope_hash") or manifest.get("bundle_hash"),
        file_size_bytes=len(serialized_export.encode("utf-8")),
        payload=export_document,
        options={
            "sign_bundle": sign_bundle,
            "encrypt_bundle": encrypt_bundle,
        },
        encrypted=bool(manifest.get("encrypted")),
        signed=manifest.get("signature_algorithm") != "none",
    )
    db.session.add(export_record)
    db.session.commit()

    export_suffix = "encrypted" if encrypt_bundle else "signed"
    return Response(
        serialized_export,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=run_{run_id}_{export_suffix}.json'}
    )


# ============== Replay Endpoint ==============

@trace_bp.route('/runs/<run_id>/replay', methods=['POST'])
@api_session_login_required
def replay_run(run_id):
    """Replay a run (placeholder for implementation)."""
    if not user_has_permission('TRACE_REPLAY'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
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
@api_session_login_required
def get_artifact(run_id, artifact_id):
    """Get a specific artifact."""
    if not user_has_permission('TRACE_VIEW_ARTIFACTS'):
        return jsonify({'error': 'Permission denied'}), 403
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    artifact = TraceArtifact.query.filter_by(
        artifact_id=artifact_id, run_id=run.run_id
    ).first_or_404()
    
    return jsonify(artifact.to_dict())


# ============== Phase 4: Sessions ==============

@trace_bp.route('/sessions', methods=['GET'])
@api_session_login_required
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
@api_session_login_required
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
@api_session_login_required
def get_session(session_id):
    """Get a specific session."""
    
    session = ChatSession.query.filter_by(session_id=session_id).first_or_404()
    
    if session.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(session.to_dict())


@trace_bp.route('/sessions/<session_id>', methods=['PATCH'])
@api_session_login_required
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
@api_session_login_required
def get_run_spans(run_id):
    """Get OpenTelemetry spans for a run."""
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    spans = TraceSpan.query.filter_by(run_id=run.run_id).order_by(TraceSpan.start_time).all()
    
    return jsonify({
        'spans': [s.to_dict() for s in spans]
    })


# ============== Phase 4: Logs ==============

@trace_bp.route('/runs/<run_id>/logs', methods=['GET'])
@api_session_login_required
def get_run_logs(run_id):
    """Get logs for a run."""
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    stage_id = request.args.get('stage_id')
    level = request.args.get('level')
    
    stage_ids = [stage.stage_id for stage in TraceStage.query.filter_by(run_id=run.run_id).all()]
    query = StageLog.query.filter(StageLog.stage_id.in_(stage_ids))
    
    if stage_id:
        query = query.filter_by(stage_id=stage_id)
    if level:
        query = query.filter_by(level=level)
    
    logs = query.order_by(StageLog.timestamp).all()
    
    return jsonify({
        'logs': [log_entry.to_dict() for log_entry in logs]
    })


# ============== Phase 4: Exports ==============

@trace_bp.route('/exports', methods=['GET'])
@api_session_login_required
def list_exports():
    """List exports for the current user."""
    
    exports = (
        TraceExport.query.filter_by(user_id=current_user.id)
        .order_by(TraceExport.exported_at.desc())
        .limit(50)
        .all()
    )
    
    return jsonify({
        'exports': [e.to_dict() for e in exports]
    })


@trace_bp.route('/exports/<export_id>', methods=['GET'])
@api_session_login_required
def get_export(export_id):
    """Get a specific export."""
    
    export = _get_export_or_404(export_id)
    
    if export.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(export.to_dict())


@trace_bp.route('/exports/<export_id>/download', methods=['GET'])
@api_session_login_required
def download_export(export_id):
    """Download an export bundle."""
    
    export = _get_export_or_404(export_id)
    
    if export.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    if export.status != 'ready':
        return jsonify({'error': 'Export not ready'}), 400
    
    if not export.payload:
        return jsonify({
            'bundle_ref': export.bundle_ref,
            'manifest_hash': export.manifest_hash,
            'file_size_bytes': export.file_size_bytes
        })

    return Response(
        json.dumps(export.payload, indent=2, default=str),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=trace_export_{export_id}.json'}
    )


# ============== Claim-Evidence Links ==============

@trace_bp.route('/runs/<run_id>/claims/<claim_id>/evidence', methods=['GET'])
@api_session_login_required
def get_claim_evidence(run_id, claim_id):
    """Get evidence linked to a specific claim."""
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
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
@api_session_login_required
def get_run_compliance(run_id):
    """Get compliance framework mappings for a run."""
    
    run = _get_run_or_404(run_id)
    
    if run.user_id != current_user.id and not _user_is_owner():
        return jsonify({'error': 'Access denied'}), 403
    
    framework = request.args.get('framework')
    
    query = ComplianceMapping.query.filter_by(run_id=run.run_id)
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
@api_session_login_required
def add_compliance_mapping(run_id):
    """Add a compliance mapping for a run (admin only)."""
    
    # Only admins can add compliance mappings
    if not _user_is_owner():
        return jsonify({'error': 'Admin access required'}), 403
    
    run = _get_run_or_404(run_id)
    
    data = request.get_json() or {}
    if not data.get('framework') or not data.get('control_id'):
        return jsonify({'error': 'framework and control_id required'}), 400
    
    mapping = ComplianceMapping(
        run_id=run.run_id,
        framework=data['framework'],
        control_id=data['control_id'],
        relevance_reason=data.get('relevance_reason'),
        evidence_ids=data.get('evidence_ids')
    )
    
    db.session.add(mapping)
    db.session.commit()
    
    return jsonify(mapping.to_dict()), 201
