from datetime import datetime, UTC
from extensions import db
from sqlalchemy.orm import relationship, backref

def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(UTC)

class SimulationSession(db.Model):
    """Model for tracking simulation sessions"""
    __tablename__ = 'simulation_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True, default='')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(128), default='')
    description = db.Column(db.Text, default='')
    parameters = db.Column(db.JSON, default=dict)
    status = db.Column(db.String(20), default='pending')
    current_step = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, default=8)
    results = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=_utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('simulations', lazy='dynamic'))
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'status': self.status,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'results': self.results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
