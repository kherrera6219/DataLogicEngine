from datetime import datetime, timedelta
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from extensions import db

logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    # Basic fields
    username = db.Column(db.String(64), unique=True, nullable=False)
    _email = db.Column('email', db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    @property
    def email(self):
        if not self._email:
            return None
        from extensions import encryption_manager
        try:
            return encryption_manager.decrypt(self._email, field_name='email')
        except Exception:
            # Fallback for if it's not encrypted yet (during migration)
            return self._email

    @email.setter
    def email(self, value):
        if not value:
            self._email = None
            return
        from extensions import encryption_manager
        self._email = encryption_manager.encrypt(value, field_name='email')
    active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # MFA fields
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(255))
    backup_codes = db.Column(JSONB)  # Encrypted list of backup codes
    
    # Account security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_successful_login = db.Column(db.DateTime)
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        from backend.security.password_security import PasswordSecurity
        is_strong, errors = PasswordSecurity.validate_password_strength(password)
        if not is_strong:
            raise ValueError(f"Password too weak: {', '.join(errors)}")
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_account_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def record_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Lock account for 30 minutes
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
            logger.warning(f"Account locked for user {self.username} due to failed logins")

    def record_successful_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_successful_login = datetime.utcnow()

    def is_password_expired(self):
        from backend.security.password_security import PasswordSecurity
        return PasswordSecurity.is_password_expired(self.last_password_change)

    def verify_totp(self, token):
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        from backend.security.mfa import MFAManager
        return MFAManager.verify_totp(self.mfa_secret, token)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,  # Should be decrypted in real scenario via property
            'active': self.active,
            'is_admin': self.is_admin,
            'role': self.role,
            'mfa_enabled': self.mfa_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_successful_login.isoformat() if self.last_successful_login else None
        }

    @staticmethod
    def from_dict(data):
        user = User()
        for field in ['username', 'email', 'role', 'active', 'is_admin']:
            if field in data:
                setattr(user, field, data[field])
        return user

class SimulationSession(db.Model):
    __tablename__ = 'simulation_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _name = db.Column('name', db.String(100))
    _description = db.Column('description', db.Text)
    
    @property
    def name(self):
        if not self._name: return None
        from extensions import encryption_manager
        try: return encryption_manager.decrypt(self._name, field_name='sim_name')
        except: return self._name

    @name.setter
    def name(self, value):
        from extensions import encryption_manager
        self._name = encryption_manager.encrypt(value, field_name='sim_name')

    @property
    def description(self):
        if not self._description: return None
        from extensions import encryption_manager
        try: return encryption_manager.decrypt(self._description, field_name='sim_desc')
        except: return self._description

    @description.setter
    def description(self, value):
        from extensions import encryption_manager
        self._description = encryption_manager.encrypt(value, field_name='sim_desc')
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
