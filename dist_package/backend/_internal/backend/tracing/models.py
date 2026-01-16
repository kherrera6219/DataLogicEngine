"""
Tracing Models for Enterprise Chatbot

Full traceability data models for capturing run execution,
stages, evidence, claims, personas, KAs, and policy decisions.
"""

import uuid
from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import JSON as JSONB
from sqlalchemy.types import Uuid as UUID, Uuid
from extensions import db


class TraceRun(db.Model):
    """Top-level trace run capturing a complete chat interaction."""
    __tablename__ = 'trace_runs'
    
    run_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), nullable=True)
    tenant_id = db.Column(db.String(100), nullable=True)
    workspace_id = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    correlation_id = db.Column(db.String(100), nullable=True)
    
    # Status and timing
    status = db.Column(db.String(20), default='running')  # running, pass, warn, fail
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Model and policy context
    model_name = db.Column(db.String(100), nullable=True)
    model_version = db.Column(db.String(50), nullable=True)
    policy_pack_id = db.Column(db.String(100), nullable=True)
    policy_pack_version = db.Column(db.String(50), nullable=True)
    
    # Data snapshot references
    data_snapshot = db.Column(JSONB, nullable=True)  # ukg_snapshot, uskd_snapshot, index_versions
    
    # Scores
    confidence = db.Column(db.Float, default=0.0)
    entropy = db.Column(db.Float, default=0.0)
    bias_risk = db.Column(db.Float, default=0.0)
    
    # Input/Output
    input_message = db.Column(db.Text, nullable=True)
    final_answer = db.Column(db.Text, nullable=True)
    
    # Relationships
    stages = db.relationship('TraceStage', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    evidence_items = db.relationship('TraceEvidence', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    claims = db.relationship('TraceClaim', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    personas = db.relationship('TracePersona', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    ka_invocations = db.relationship('TraceKAInvocation', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    policy_decisions = db.relationship('TracePolicyDecision', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    memory_events = db.relationship('TraceMemoryEvent', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'run_id': str(self.run_id),
            'session_id': str(self.session_id) if self.session_id else None,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'model': {'name': self.model_name, 'version': self.model_version},
            'policy_pack': {'id': self.policy_pack_id, 'version': self.policy_pack_version},
            'data_snapshot': self.data_snapshot,
            'scores': {
                'confidence': self.confidence,
                'entropy': self.entropy,
                'bias_risk': self.bias_risk
            },
            'input_message': self.input_message,
            'final_answer': self.final_answer
        }


class TraceStage(db.Model):
    """Individual stage in the execution pipeline (Layer 1-10 or Step 1-12)."""
    __tablename__ = 'trace_stages'
    
    stage_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    
    # Stage identification
    name = db.Column(db.String(100), nullable=False)
    stage_type = db.Column(db.String(20), default='layer')  # layer, step
    layer_index = db.Column(db.Integer, nullable=True)  # 1-10 for layers
    step_index = db.Column(db.Integer, nullable=True)   # 1-12 for steps
    
    # Status and timing
    status = db.Column(db.String(20), default='running')  # running, pass, warn, fail, skipped
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    
    # Inputs/Outputs (artifact references)
    inputs = db.Column(JSONB, nullable=True)   # [{artifact_id, label}]
    outputs = db.Column(JSONB, nullable=True)  # [{artifact_id, label}]
    
    # Decisions made at this stage
    decisions = db.Column(JSONB, nullable=True)  # [{description, rationale, alternatives}]
    
    # Metrics
    metrics = db.Column(JSONB, nullable=True)  # tokens_in, tokens_out, retrieval_count, cache_hits, retries
    
    def to_dict(self):
        return {
            'stage_id': str(self.stage_id),
            'run_id': str(self.run_id),
            'name': self.name,
            'type': self.stage_type,
            'layer_index': self.layer_index,
            'step_index': self.step_index,
            'status': self.status,
            'timing': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_ms': self.duration_ms
            },
            'inputs': self.inputs,
            'outputs': self.outputs,
            'decisions': self.decisions,
            'metrics': self.metrics
        }


class TraceEvidence(db.Model):
    """Evidence item used in a run."""
    __tablename__ = 'trace_evidence'
    
    evidence_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    
    # Source information
    source_type = db.Column(db.String(50), nullable=True)  # doc, url, db_record, user_upload
    source_id = db.Column(db.String(255), nullable=True)
    source_title = db.Column(db.String(500), nullable=True)
    authority = db.Column(db.String(20), default='medium')  # high, medium, low
    
    # Location within source
    locator = db.Column(JSONB, nullable=True)  # page, section, line_range, url
    
    # Content
    snippet = db.Column(db.Text, nullable=True)
    content_hash = db.Column(db.String(100), nullable=True)  # sha256
    
    # Retrieval metadata
    retrieval_method = db.Column(db.String(50), nullable=True)  # vector, graph, rules, manual
    relevance_score = db.Column(db.Float, nullable=True)
    axis_match_score = db.Column(db.Float, nullable=True)
    
    # Usage tracking
    used_by_claims = db.Column(JSONB, nullable=True)    # [claim_id]
    used_by_personas = db.Column(JSONB, nullable=True)  # [persona_id]
    used_by_stages = db.Column(JSONB, nullable=True)    # [stage_id]
    
    # Conflicts
    conflicts_with = db.Column(JSONB, nullable=True)  # [evidence_id]
    
    def to_dict(self):
        return {
            'evidence_id': str(self.evidence_id),
            'run_id': str(self.run_id),
            'source': {
                'type': self.source_type,
                'id': self.source_id,
                'title': self.source_title,
                'authority': self.authority
            },
            'locator': self.locator,
            'snippet': self.snippet,
            'hash': self.content_hash,
            'retrieval': {
                'method': self.retrieval_method,
                'relevance_score': self.relevance_score,
                'axis_match': self.axis_match_score
            },
            'used_by': {
                'claims': self.used_by_claims,
                'personas': self.used_by_personas,
                'stages': self.used_by_stages
            },
            'conflicts_with': self.conflicts_with
        }


class TraceClaim(db.Model):
    """Individual claim extracted from the final answer."""
    __tablename__ = 'trace_claims'
    
    claim_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    
    # Claim content
    text = db.Column(db.Text, nullable=False)
    answer_span_start = db.Column(db.Integer, nullable=True)
    answer_span_end = db.Column(db.Integer, nullable=True)
    
    # Support status
    status = db.Column(db.String(20), default='pending')  # supported, partial, unsupported, contested
    confidence = db.Column(db.Float, default=0.0)
    
    # Evidence links
    evidence_ids = db.Column(JSONB, nullable=True)  # [evidence_id]
    stage_ids = db.Column(JSONB, nullable=True)     # [stage_id]
    
    def to_dict(self):
        return {
            'claim_id': str(self.claim_id),
            'run_id': str(self.run_id),
            'text': self.text,
            'answer_span': {'start': self.answer_span_start, 'end': self.answer_span_end},
            'support': {
                'status': self.status,
                'confidence': self.confidence,
                'evidence_ids': self.evidence_ids,
                'stage_ids': self.stage_ids
            }
        }


class TraceAxisVector(db.Model):
    """17-axis coordinate vector for a run."""
    __tablename__ = 'trace_axis_vectors'
    
    vector_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False, unique=True)
    
    # Per-axis data
    axes = db.Column(JSONB, nullable=False)  # [{axis_id, name, selected, candidates, trigger_evidence}]
    
    # Coordinate hash for comparison
    coordinate_hash = db.Column(db.String(100), nullable=True)
    
    def to_dict(self):
        return {
            'vector_id': str(self.vector_id),
            'run_id': str(self.run_id),
            'axes': self.axes,
            'coordinate_hash': self.coordinate_hash
        }


class TracePersona(db.Model):
    """Persona execution trace (Quad Persona + custom)."""
    __tablename__ = 'trace_personas'
    
    persona_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    
    # Persona identification
    persona_type = db.Column(db.String(50), nullable=False)  # analyst, expert, critic, synthesizer, custom
    persona_name = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, running, pass, warn, fail
    
    # Inputs (what this persona was given)
    evidence_ids = db.Column(JSONB, nullable=True)
    context_scope = db.Column(db.Text, nullable=True)
    
    # Output
    draft_text = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, default=0.0)
    
    # Objections and consensus
    objections = db.Column(JSONB, nullable=True)  # [{type, detail}]
    consensus_impact = db.Column(JSONB, nullable=True)  # {changed_answer, delta_summary}
    
    def to_dict(self):
        return {
            'persona_id': str(self.persona_id),
            'run_id': str(self.run_id),
            'persona_type': self.persona_type,
            'persona_name': self.persona_name,
            'status': self.status,
            'inputs': {
                'evidence_ids': self.evidence_ids,
                'context_scope': self.context_scope
            },
            'draft': {
                'text': self.draft_text,
                'confidence': self.confidence
            },
            'objections': self.objections,
            'consensus_impact': self.consensus_impact
        }


class TraceKAInvocation(db.Model):
    """Knowledge Algorithm invocation trace."""
    __tablename__ = 'trace_ka_invocations'
    
    invocation_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)
    
    # KA identification
    ka_id = db.Column(db.String(100), nullable=False)
    ka_name = db.Column(db.String(200), nullable=True)
    ka_version = db.Column(db.String(50), nullable=True)
    
    # Execution
    status = db.Column(db.String(20), default='pending')
    duration_ms = db.Column(db.Integer, nullable=True)
    
    # Inputs/Outputs
    inputs = db.Column(JSONB, nullable=True)
    outputs = db.Column(JSONB, nullable=True)
    
    # Routing decision
    routing = db.Column(JSONB, nullable=True)  # {complexity_score, axis_triggers, reason}
    
    # Side effects
    side_effects = db.Column(JSONB, nullable=True)  # [{type, ref_id}]
    
    def to_dict(self):
        return {
            'invocation_id': str(self.invocation_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'ka_id': self.ka_id,
            'ka_name': self.ka_name,
            'ka_version': self.ka_version,
            'status': self.status,
            'timing': {'duration_ms': self.duration_ms},
            'inputs': self.inputs,
            'outputs': self.outputs,
            'routing': self.routing,
            'side_effects': self.side_effects
        }


class TracePolicyDecision(db.Model):
    """Policy/guardrail decision trace."""
    __tablename__ = 'trace_policy_decisions'
    
    decision_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)
    
    # Decision
    policy_rule_id = db.Column(db.String(100), nullable=True)
    decision_type = db.Column(db.String(20), nullable=False)  # allow, deny, redact, warn
    reason = db.Column(db.Text, nullable=True)
    
    # What was affected
    affected = db.Column(JSONB, nullable=True)  # {artifact_ids, evidence_ids, text_spans}
    
    # Actor and timing
    actor = db.Column(db.String(50), default='system')  # system, admin, user
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'decision_id': str(self.decision_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'policy_rule_id': self.policy_rule_id,
            'type': self.decision_type,
            'reason': self.reason,
            'affected': self.affected,
            'actor': self.actor,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class TraceMemoryEvent(db.Model):
    """Memory access/writeback trace."""
    __tablename__ = 'trace_memory_events'
    
    event_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)
    
    # Event type
    event_type = db.Column(db.String(50), nullable=False)  # recall, writeback_proposed, writeback_committed, snapshot
    target = db.Column(db.String(20), nullable=True)  # working, ukg, uskd
    
    # Items involved
    items = db.Column(JSONB, nullable=True)  # [{item_id, coordinate, hash}]
    
    # Gating (for writebacks)
    gating = db.Column(JSONB, nullable=True)  # {confidence, threshold, approved, reason}
    
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'event_id': str(self.event_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'type': self.event_type,
            'target': self.target,
            'items': self.items,
            'gating': self.gating,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class TraceArtifact(db.Model):
    """Artifact (input/output blob) storage."""
    __tablename__ = 'trace_artifacts'
    
    artifact_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)
    
    # Artifact metadata
    artifact_type = db.Column(db.String(50), default='json')  # json, text, table, graph, binary_ref
    label = db.Column(db.String(200), nullable=True)
    
    # Content
    content = db.Column(JSONB, nullable=True)  # For JSON/text
    content_ref = db.Column(db.String(500), nullable=True)  # For binary/large content
    content_hash = db.Column(db.String(100), nullable=True)
    
    # Redactions applied
    redactions = db.Column(JSONB, nullable=True)  # [{start, end, reason_code, policy_rule_id}]
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'artifact_id': str(self.artifact_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'type': self.artifact_type,
            'label': self.label,
            'content': self.content,
            'content_ref': self.content_ref,
            'hash': self.content_hash,
            'redactions': self.redactions
        }


# ============== Phase 4 Models ==============

class ChatSession(db.Model):
    """Chat session for grouping related runs."""
    __tablename__ = 'chat_sessions'
    
    session_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(255), nullable=True)
    mode = db.Column(db.String(20), default='chat')  # chat, explain, trace
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Settings/constraints
    constraints = db.Column(JSONB, nullable=True)  # {offline_only, strict_citations, no_writeback}
    
    # Relationships
    runs = db.relationship('TraceRun', backref='session', lazy='dynamic',
                          primaryjoin='ChatSession.session_id==TraceRun.session_id',
                          foreign_keys='TraceRun.session_id')
    
    def to_dict(self):
        return {
            'session_id': str(self.session_id),
            'user_id': self.user_id,
            'title': self.title,
            'mode': self.mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'constraints': self.constraints
        }


class ClaimEvidenceLink(db.Model):
    """Junction table for claim-evidence relationships."""
    __tablename__ = 'claim_evidence_links'
    
    claim_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_claims.claim_id'), primary_key=True)
    evidence_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), primary_key=True)
    
    strength = db.Column(db.Float, default=1.0)
    contradicts = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'claim_id': str(self.claim_id),
            'evidence_id': str(self.evidence_id),
            'strength': self.strength,
            'contradicts': self.contradicts
        }


class TraceSpan(db.Model):
    """OpenTelemetry-style trace span for observability."""
    __tablename__ = 'trace_spans'
    
    span_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    parent_span_id = db.Column(UUID(as_uuid=True), nullable=True)
    
    name = db.Column(db.String(200), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)
    
    start_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    end_at = db.Column(db.DateTime, nullable=True)
    
    attributes = db.Column(JSONB, nullable=True)  # Key-value pairs
    events = db.Column(JSONB, nullable=True)      # [{name, time, attributes}]
    
    def to_dict(self):
        return {
            'span_id': str(self.span_id),
            'run_id': str(self.run_id),
            'parent_span_id': str(self.parent_span_id) if self.parent_span_id else None,
            'name': self.name,
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'start_at': self.start_at.isoformat() if self.start_at else None,
            'end_at': self.end_at.isoformat() if self.end_at else None,
            'duration_ms': int((self.end_at - self.start_at).total_seconds() * 1000) if self.end_at and self.start_at else None,
            'attributes': self.attributes,
            'events': self.events
        }


class StageLog(db.Model):
    """Log entries for a stage (debug/info/warn/error)."""
    __tablename__ = 'stage_logs'
    
    log_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)
    
    level = db.Column(db.String(10), nullable=False)  # debug, info, warn, error
    message = db.Column(db.Text, nullable=False)
    data = db.Column(JSONB, nullable=True)
    
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'log_id': str(self.log_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'level': self.level,
            'message': self.message,
            'data': self.data,
            'time': self.timestamp.isoformat() if self.timestamp else None
        }


class TraceExport(db.Model):
    """Export bundle tracking for audit."""
    __tablename__ = 'trace_exports'
    
    export_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, ready, failed
    bundle_ref = db.Column(db.String(500), nullable=True)  # Blob storage pointer
    manifest_hash = db.Column(db.String(100), nullable=True)  # SHA256
    
    file_size_bytes = db.Column(db.Integer, nullable=True)
    format = db.Column(db.String(20), default='json')  # json, zip
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    expires_at = db.Column(db.DateTime, nullable=True)  # For temporary exports
    
    export_options = db.Column(JSONB, nullable=True)  # Additional export options
    
    def to_dict(self):
        return {
            'export_id': str(self.export_id),
            'run_id': str(self.run_id),
            'user_id': self.user_id,
            'status': self.status,
            'bundle_ref': self.bundle_ref,
            'manifest_hash': self.manifest_hash,
            'file_size_bytes': self.file_size_bytes,
            'format': self.format,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


# ============== Enterprise Compliance Models ==============

class ComplianceMapping(db.Model):
    """Mapping of runs to compliance framework controls (SOC2, ISO27001, NIST, FedRAMP)."""
    __tablename__ = 'compliance_mappings'
    
    mapping_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    
    framework = db.Column(db.String(50), nullable=False)  # SOC2, ISO27001, NIST800-53, FedRAMP
    control_id = db.Column(db.String(50), nullable=False)  # e.g., CC6.1, A.12.1.1
    
    relevance_reason = db.Column(db.Text, nullable=True)
    evidence_ids = db.Column(JSONB, nullable=True)  # [evidence_id UUIDs]
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'mapping_id': str(self.mapping_id),
            'run_id': str(self.run_id),
            'framework': self.framework,
            'control_id': self.control_id,
            'relevance_reason': self.relevance_reason,
            'evidence_ids': self.evidence_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ArtifactRedaction(db.Model):
    """Redaction record for sensitive content in artifacts."""
    __tablename__ = 'artifact_redactions'
    
    redaction_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_artifacts.artifact_id'), nullable=False)
    
    start_pos = db.Column(db.Integer, nullable=False)
    end_pos = db.Column(db.Integer, nullable=False)
    reason_code = db.Column(db.String(50), nullable=False)  # PII, SENSITIVE, CLASSIFIED, etc.
    policy_rule_id = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'redaction_id': str(self.redaction_id),
            'artifact_id': str(self.artifact_id),
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'reason_code': self.reason_code,
            'policy_rule_id': self.policy_rule_id
        }


class EvidenceConflict(db.Model):
    """Explicit conflict relationships between evidence items."""
    __tablename__ = 'evidence_conflicts'
    
    evidence_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), primary_key=True)
    conflicts_with = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), primary_key=True)
    
    reason = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self):
        return {
            'evidence_id': str(self.evidence_id),
            'conflicts_with': str(self.conflicts_with),
            'reason': self.reason,
            'severity': self.severity
        }


class PersonaEvidenceLink(db.Model):
    """Junction table linking personas to evidence they used."""
    __tablename__ = 'persona_evidence_links'
    
    persona_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_personas.persona_id'), primary_key=True)
    evidence_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), primary_key=True)
    
    relevance_score = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        return {
            'persona_id': str(self.persona_id),
            'evidence_id': str(self.evidence_id),
            'relevance_score': self.relevance_score
        }


class StageArtifactLink(db.Model):
    """Junction table linking stages to their input/output artifacts."""
    __tablename__ = 'stage_artifact_links'
    
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), primary_key=True)
    artifact_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_artifacts.artifact_id'), primary_key=True)
    direction = db.Column(db.String(10), primary_key=True)  # input, output
    
    label = db.Column(db.String(200), nullable=True)
    
    def to_dict(self):
        return {
            'stage_id': str(self.stage_id),
            'artifact_id': str(self.artifact_id),
            'direction': self.direction,
            'label': self.label
        }


class KAArtifactLink(db.Model):
    """Junction table linking KA invocations to their input/output artifacts."""
    __tablename__ = 'ka_artifact_links'
    
    invocation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_ka_invocations.invocation_id'), primary_key=True)
    artifact_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_artifacts.artifact_id'), primary_key=True)
    direction = db.Column(db.String(10), primary_key=True)  # input, output
    
    def to_dict(self):
        return {
            'invocation_id': str(self.invocation_id),
            'artifact_id': str(self.artifact_id),
            'direction': self.direction
        }
