"""
Flask extensions initialization module.

This module initializes Flask extensions to avoid circular imports.
All extensions should be initialized here and imported by other modules.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS
from backend.security.audit_logger import AuditLogger
from backend.security.rbac import RBACManager
from backend.security.encryption_manager import EncryptionManager
from backend.security.mfa import MFAManager


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Security & Performance: Enable SQLite WAL mode and Foreign Keys
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and Foreign Keys for SQLite connections."""
    # Check if we are really dealing with a sqlite3 connection
    if type(dbapi_connection).__module__ == 'sqlite3':
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
audit_logger = AuditLogger()
cache = Cache()
compress = Compress()
cors = CORS()
rbac_manager = RBACManager(audit_logger=audit_logger)
encryption_manager = EncryptionManager(audit_logger=audit_logger)
mfa_manager = MFAManager()

login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'info'

# Initialize Limiter with key_func but deferred app init
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
