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

# Database setup
class Base(DeclarativeBase):
    pass

# Initialize extensions (without app)
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

# Configure login manager
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'info'
