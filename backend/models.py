from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSON
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin', etc.
    
    chats = db.relationship('Chat', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'role': self.role
        }


class Chat(db.Model):
    __tablename__ = 'chats'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }


# Universal Knowledge Graph (UKG) Models
class UkgNode(db.Model):
    """Model representing nodes in the Universal Knowledge Graph"""
    __tablename__ = 'ukg_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False, index=True)
    node_type = db.Column(db.String(100), nullable=False, index=True)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    original_id = db.Column(db.String(255), nullable=True, index=True)
    axis_number = db.Column(db.Integer, nullable=True, index=True)
    level = db.Column(db.Integer, nullable=True)
    attributes = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    outgoing_edges = db.relationship('UkgEdge', foreign_keys='UkgEdge.source_id', backref='source', lazy='dynamic')
    incoming_edges = db.relationship('UkgEdge', foreign_keys='UkgEdge.target_id', backref='target', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'node_type': self.node_type,
            'label': self.label,
            'description': self.description,
            'original_id': self.original_id,
            'axis_number': self.axis_number,
            'level': self.level,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UkgEdge(db.Model):
    """Model representing connections between nodes in the Universal Knowledge Graph"""
    __tablename__ = 'ukg_edges'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False, index=True)
    edge_type = db.Column(db.String(100), nullable=False, index=True)
    source_id = db.Column(db.Integer, db.ForeignKey('ukg_nodes.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('ukg_nodes.id'), nullable=False)
    label = db.Column(db.String(255), nullable=True)
    weight = db.Column(db.Float, default=1.0)
    attributes = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'edge_type': self.edge_type,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'label': self.label,
            'weight': self.weight,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KnowledgeAlgorithm(db.Model):
    """Model for storing metadata about Knowledge Algorithms"""
    __tablename__ = 'knowledge_algorithms'
    
    id = db.Column(db.Integer, primary_key=True)
    ka_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    input_schema = db.Column(JSON, nullable=True)
    output_schema = db.Column(JSON, nullable=True)
    version = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = db.relationship('KaExecution', backref='algorithm', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'ka_id': self.ka_id,
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KaExecution(db.Model):
    """Model for tracking executions of Knowledge Algorithms"""
    __tablename__ = 'ka_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    algorithm_id = db.Column(db.Integer, db.ForeignKey('knowledge_algorithms.id'), nullable=False)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    pass_num = db.Column(db.Integer, default=0)
    layer_num = db.Column(db.Integer, default=0)
    input_data = db.Column(JSON, nullable=True)
    output_data = db.Column(JSON, nullable=True)
    confidence = db.Column(db.Float, default=0.0)
    execution_time = db.Column(db.Float, nullable=True)  # in milliseconds
    status = db.Column(db.String(50), default='pending')
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'algorithm_id': self.algorithm_id,
            'session_id': self.session_id,
            'pass_num': self.pass_num,
            'layer_num': self.layer_num,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'confidence': self.confidence,
            'execution_time': self.execution_time,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
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
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
