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
from backend.security.audit_logger import AuditLogger


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
audit_logger = AuditLogger()
cache = Cache()

login_manager.login_view = 'login'  # type: ignore[assignment]
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'info'
