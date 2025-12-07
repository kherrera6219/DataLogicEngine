import os
import re
import uuid
import logging
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file
load_dotenv()

# Configure logging - use INFO in production, DEBUG in development
log_level = logging.DEBUG if os.environ.get("FLASK_ENV") == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Server configuration
DEFAULT_PORT = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", 8080)))

# Create Flask app
app = Flask(__name__)
# Security: Get secret key from environment, fallback only for development
if os.environ.get('FLASK_ENV') == 'development':
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-for-local-development-only")
else:
    app.secret_key = os.environ.get("SECRET_KEY")
    if not app.secret_key:
        raise ValueError("SECRET_KEY environment variable must be set for production!")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Session hardening
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", 30))
)

# Configure database
database_url = os.environ.get("DATABASE_URL", "sqlite:///ukg_database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[os.environ.get("GLOBAL_RATE_LIMIT", "200 per hour")],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)

# Initialize extensions with app
from extensions import db, login_manager
db.init_app(app)
login_manager.init_app(app)

# Initialize security headers (Phase 1 security hardening)
from backend.security.security_headers import configure_security_headers
configure_security_headers(app, {'ENV': os.environ.get('FLASK_ENV', 'production')})

# Initialize request limits (Phase 1 security hardening)
from backend.middleware.request_limits import configure_request_limits
configure_request_limits(app, {
    'MAX_CONTENT_LENGTH': int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
})

# Import models (after extensions initialization)
# Note: Importing models ensures SQLAlchemy creates their tables during db.create_all()
from sqlalchemy import text

from models import User, SimulationSession, KnowledgeGraphNode, KnowledgeGraphEdge, MCPServer, MCPResource, MCPTool, MCPPrompt, PasswordHistory  # noqa: F401

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def password_meets_policy(password: str) -> bool:
    """Enforce a basic password policy for initial hardening."""
    if not password or len(password) < 12:
        return False
    has_upper = re.search(r"[A-Z]", password)
    has_lower = re.search(r"[a-z]", password)
    has_digit = re.search(r"\d", password)
    has_symbol = re.search(r"[^A-Za-z0-9]", password)
    return all([has_upper, has_lower, has_digit, has_symbol])

# Create tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

# Register MCP blueprint
from backend.mcp_api import mcp_bp
app.register_blueprint(mcp_bp)
logger.info("MCP blueprint registered")

# Routes
@app.route('/')
def index():
    return render_template('index.html')


def _config_health() -> dict:
    """Summarize configuration readiness for lightweight health checks."""

    secret_key_status = "set" if app.secret_key else "missing"
    environment = os.environ.get("FLASK_ENV", "production")
    return {
        "environment": environment,
        "secret_key": secret_key_status,
    }


def _database_health() -> dict:
    """Confirm database connectivity with a trivial query."""

    try:
        db.session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        logger.error("Database connectivity check failed", exc_info=exc)
        return {"status": "error", "detail": str(exc)}

    return {"status": "ok"}


@app.route("/health", methods=["GET"])
def health() -> tuple:
    """Lightweight health endpoint for runtime monitoring."""

    config_state = _config_health()
    database_state = _database_health()

    overall_status = "ok"
    http_status = 200

    if database_state.get("status") != "ok":
        overall_status = "error"
        http_status = 503
    elif config_state.get("secret_key") == "missing":
        overall_status = "degraded"

    payload = {
        "status": overall_status,
        "config": config_state,
        "database": database_state,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return jsonify(payload), http_status

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            session.permanent = True
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to the requested page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        if not password_meets_policy(password):
            flash('Password must be at least 12 characters and include upper, lower, digit, and symbol characters.', 'error')
            return render_template('register.html')
        
        # Check for existing user
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            flash('An error occurred during registration', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # For now, just render a simple dashboard
    return render_template('dashboard.html')

@app.route('/simulations')
@login_required
def simulations():
    # Get user's simulation sessions
    user_simulations = SimulationSession.query.filter_by(user_id=current_user.id).order_by(SimulationSession.created_at.desc()).all()
    return render_template('simulations.html', simulations=user_simulations)

@app.route('/create_simulation', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def create_simulation():
    # Get simulation parameters from form
    name = request.form.get('name')
    description = request.form.get('description', '')
    sim_type = request.form.get('sim_type')
    refinement_steps = int(request.form.get('refinement_steps', 12))
    confidence_threshold = float(request.form.get('confidence_threshold', 0.85))
    entropy_sampling = 'entropy_sampling' in request.form
    auto_start = 'auto_start' in request.form
    
    # Validate input
    if not name or not sim_type:
        flash('Simulation name and type are required', 'error')
        return redirect(url_for('simulations'))
    
    # Create simulation parameters
    parameters = {
        'simulation_type': sim_type,
        'refinement_steps': refinement_steps,
        'confidence_threshold': confidence_threshold,
        'entropy_sampling': entropy_sampling
    }
    
    # Create new simulation session
    new_simulation = SimulationSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=name,
        description=description,
        parameters=parameters,
        status='pending' if not auto_start else 'running',
        current_step=0,
        total_steps=8,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow() if auto_start else None
    )
    
    try:
        db.session.add(new_simulation)
        db.session.commit()
        
        if auto_start:
            flash(f'Simulation "{name}" created and started successfully', 'success')
        else:
            flash(f'Simulation "{name}" created successfully', 'success')
        
        return redirect(url_for('simulations'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating simulation: {e}")
        flash('An error occurred while creating the simulation', 'error')
        return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/start', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def start_simulation(sim_id):
    """Start a pending simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'pending':
        flash('Only pending simulations can be started', 'error')
        return redirect(url_for('simulations'))
    
    try:
        simulation.status = 'running'
        simulation.started_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" started successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting simulation: {e}")
        flash('An error occurred while starting the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/pause', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def pause_simulation(sim_id):
    """Pause a running simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'running':
        flash('Only running simulations can be paused', 'error')
        return redirect(url_for('simulations'))
    
    try:
        simulation.status = 'paused'
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" paused successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error pausing simulation: {e}")
        flash('An error occurred while pausing the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/resume', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def resume_simulation(sim_id):
    """Resume a paused simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'paused':
        flash('Only paused simulations can be resumed', 'error')
        return redirect(url_for('simulations'))
    
    try:
        simulation.status = 'running'
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" resumed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resuming simulation: {e}")
        flash('An error occurred while resuming the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/delete', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def delete_simulation(sim_id):
    """Delete a simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(simulation)
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting simulation: {e}")
        flash('An error occurred while deleting the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>')
@login_required
def view_simulation(sim_id):
    """View simulation details"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    return render_template('simulation_details.html', simulation=simulation)

@app.route('/simulation/<int:sim_id>/results')
@login_required
def simulation_results(sim_id):
    """View simulation results"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'completed':
        flash('Results are only available for completed simulations', 'warning')
        return redirect(url_for('view_simulation', sim_id=sim_id))
    
    return render_template('simulation_results.html', simulation=simulation)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Profile routes
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

# Run the application
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=DEFAULT_PORT, debug=debug_mode)