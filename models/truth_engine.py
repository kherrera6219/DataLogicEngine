from datetime import datetime, UTC
from extensions import db

def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(UTC)

class TruthSession(db.Model):
    """Track Truth Engine reasoning sessions with 5-tier workflow support"""
    __tablename__ = 'truth_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    
    tier = db.Column(db.String(20), default='trivial')
    status = db.Column(db.String(20), default='pending')
    
    query = db.Column(db.Text)
    response = db.Column(db.Text)
    
    budget_limit = db.Column(db.Float, default=0.0)
    budget_spent = db.Column(db.Float, default=0.0)
    token_count = db.Column(db.Integer, default=0)
    
    confidence_score = db.Column(db.Float, default=0.0)
    safety_score = db.Column(db.Float, default=1.0)
    
    llm_model = db.Column(db.String(64))
    routing_profile = db.Column(db.String(32))
    
    personas_used = db.Column(db.JSON)
    axis_context = db.Column(db.JSON)
    workflow_steps = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=_utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('truth_sessions', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'tier': self.tier,
            'status': self.status,
            'query': self.query,
            'response': self.response,
            'budget_limit': self.budget_limit,
            'budget_spent': self.budget_spent,
            'token_count': self.token_count,
            'confidence_score': self.confidence_score,
            'safety_score': self.safety_score,
            'llm_model': self.llm_model,
            'routing_profile': self.routing_profile,
            'personas_used': self.personas_used,
            'axis_context': self.axis_context,
            'workflow_steps': self.workflow_steps,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class TruthAuditEvent(db.Model):
    """EU AI Act Article 53 compliant audit trail with hash chain immutability"""
    __tablename__ = 'truth_audit_events'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(64), db.ForeignKey('truth_sessions.session_id'), index=True)
    
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_category = db.Column(db.String(50))
    
    event_data = db.Column(db.JSON)
    decision_rationale = db.Column(db.Text)
    
    hash_chain = db.Column(db.String(64), nullable=False)
    previous_hash = db.Column(db.String(64))
    
    actor_id = db.Column(db.String(64))
    actor_type = db.Column(db.String(32))
    
    axis_involved = db.Column(db.JSON)
    compliance_flags = db.Column(db.JSON)
    
    timestamp = db.Column(db.DateTime, default=_utcnow, index=True)
    retention_until = db.Column(db.DateTime)

    session = db.relationship('TruthSession', backref=db.backref('audit_events', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'session_id': self.session_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'event_data': self.event_data,
            'decision_rationale': self.decision_rationale,
            'hash_chain': self.hash_chain,
            'previous_hash': self.previous_hash,
            'actor_id': self.actor_id,
            'actor_type': self.actor_type,
            'axis_involved': self.axis_involved,
            'compliance_flags': self.compliance_flags,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'retention_until': self.retention_until.isoformat() if self.retention_until else None
        }


class TruthArtifact(db.Model):
    """Store simulation outputs, graphs, deliverables with 7-year retention"""
    __tablename__ = 'truth_artifacts'

    id = db.Column(db.Integer, primary_key=True)
    artifact_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(64), db.ForeignKey('truth_sessions.session_id'), index=True)
    
    artifact_type = db.Column(db.String(50), nullable=False)
    artifact_name = db.Column(db.String(256))
    
    content = db.Column(db.JSON)
    content_hash = db.Column(db.String(64))
    file_path = db.Column(db.String(512))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(128))
    
    artifact_metadata = db.Column(db.JSON)
    tags = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=_utcnow)
    retention_until = db.Column(db.DateTime)
    
    session = db.relationship('TruthSession', backref=db.backref('artifacts', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'artifact_id': self.artifact_id,
            'session_id': self.session_id,
            'artifact_type': self.artifact_type,
            'artifact_name': self.artifact_name,
            'content': self.content,
            'content_hash': self.content_hash,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'metadata': self.artifact_metadata,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'retention_until': self.retention_until.isoformat() if self.retention_until else None
        }


class TruthBudget(db.Model):
    """Per-tenant budget tracking with kill-switch capability"""
    __tablename__ = 'truth_budgets'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    budget_limit = db.Column(db.Float, default=100.0)
    budget_spent = db.Column(db.Float, default=0.0)
    budget_period = db.Column(db.String(20), default='monthly')
    
    kill_switch_triggered = db.Column(db.Boolean, default=False)
    kill_switch_threshold = db.Column(db.Float, default=0.95)
    downgrade_tier = db.Column(db.String(20), default='trivial')
    
    tier_limits = db.Column(db.JSON)
    
    alerts_enabled = db.Column(db.Boolean, default=True)
    alert_thresholds = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=_utcnow)
    reset_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    user = db.relationship('User', backref=db.backref('truth_budgets', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'budget_limit': self.budget_limit,
            'budget_spent': self.budget_spent,
            'budget_period': self.budget_period,
            'budget_remaining': self.budget_limit - self.budget_spent,
            'budget_utilization': (self.budget_spent / self.budget_limit * 100) if self.budget_limit > 0 else 0,
            'kill_switch_triggered': self.kill_switch_triggered,
            'kill_switch_threshold': self.kill_switch_threshold,
            'downgrade_tier': self.downgrade_tier,
            'tier_limits': self.tier_limits,
            'alerts_enabled': self.alerts_enabled,
            'alert_thresholds': self.alert_thresholds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reset_at': self.reset_at.isoformat() if self.reset_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TruthMetric(db.Model):
    """MLflow-style metrics tracking for Truth Engine performance"""
    __tablename__ = 'truth_metrics'

    id = db.Column(db.Integer, primary_key=True)
    metric_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(64), db.ForeignKey('truth_sessions.session_id'), nullable=True, index=True)
    
    metric_name = db.Column(db.String(128), nullable=False, index=True)
    metric_value = db.Column(db.Float, nullable=False)
    metric_unit = db.Column(db.String(32))
    
    metric_type = db.Column(db.String(32), default='gauge')
    
    tier = db.Column(db.String(20))
    llm_model = db.Column(db.String(64))
    
    labels = db.Column(db.JSON)
    
    timestamp = db.Column(db.DateTime, default=_utcnow, index=True)

    session = db.relationship('TruthSession', backref=db.backref('metrics', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'metric_id': self.metric_id,
            'session_id': self.session_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'metric_type': self.metric_type,
            'tier': self.tier,
            'llm_model': self.llm_model,
            'labels': self.labels,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class TruthLinkMessage(db.Model):
    """Inter-module messaging for TruthLink event bus"""
    __tablename__ = 'truth_link_messages'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    source_module = db.Column(db.String(32), nullable=False)
    target_module = db.Column(db.String(32))
    
    message_type = db.Column(db.String(50), nullable=False, index=True)
    priority = db.Column(db.Integer, default=1)
    
    payload = db.Column(db.JSON)
    
    status = db.Column(db.String(20), default='pending')
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
