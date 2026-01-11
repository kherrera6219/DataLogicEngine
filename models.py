from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SimulationSession(db.Model):
    __tablename__ = 'simulation_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    parameters = db.Column(JSONB)
    status = db.Column(db.String(20))
    current_step = db.Column(db.Integer)
    total_steps = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    results = db.Column(JSONB)

    user = db.relationship('User', backref=db.backref('simulations', lazy=True))

class KnowledgeGraphNode(db.Model):
    __tablename__ = 'kg_nodes'

    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.String(50), unique=True, nullable=False)
    node_type = db.Column(db.String(50))
    label = db.Column(db.String(100))
    description = db.Column(db.Text)
    axis_number = db.Column(db.Integer)
    data = db.Column(JSONB)

class KnowledgeGraphEdge(db.Model):
    __tablename__ = 'kg_edges'

    id = db.Column(db.Integer, primary_key=True)
    edge_id = db.Column(db.String(50), unique=True, nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False)
    edge_type = db.Column(db.String(50))
    weight = db.Column(db.Float)
    data = db.Column(JSONB)

    source = db.relationship('KnowledgeGraphNode', foreign_keys=[source_id], backref='out_edges')
    target = db.relationship('KnowledgeGraphNode', foreign_keys=[target_id], backref='in_edges')
