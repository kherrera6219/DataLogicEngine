from datetime import datetime, UTC
from extensions import db
from sqlalchemy.dialects.postgresql import JSON

def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(UTC)

class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    
    messages = db.relationship('Message', backref='chat', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'messages_count': self.messages.count()
        }


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

class UkgSession(db.Model):
    """Model representing a user interaction session with the UKG"""
    __tablename__ = 'ukg_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Optional link to a user
    user_query = db.Column(db.Text, nullable=True)
    target_confidence = db.Column(db.Float, default=0.85)
    final_confidence = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='active')
    started_at = db.Column(db.DateTime, default=_utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    memory_entries = db.relationship('MemoryEntry', backref='session', lazy='dynamic')
    user = db.relationship('User', backref='ukg_sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'user_query': self.user_query,
            'target_confidence': self.target_confidence,
            'final_confidence': self.final_confidence,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class MemoryEntry(db.Model):
    """Model representing entries in the structured memory store"""
    __tablename__ = 'memory_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(255), db.ForeignKey('ukg_sessions.session_id'), nullable=False)
    entry_type = db.Column(db.String(100), nullable=False, index=True)
    pass_num = db.Column(db.Integer, default=0)
    layer_num = db.Column(db.Integer, default=0)
    content = db.Column(JSON, nullable=True)
    confidence = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=_utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'session_id': self.session_id,
            'entry_type': self.entry_type,
            'pass_num': self.pass_num,
            'layer_num': self.layer_num,
            'content': self.content,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
