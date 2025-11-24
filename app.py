import os
import uuid
import logging
import re
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file
load_dotenv()

# Configure logging - use INFO in production, DEBUG in development
log_level = logging.DEBUG if os.environ.get("FLASK_ENV") == "development" else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Load configuration from config module
from config import get_config
app.config.from_object(get_config())

# Apply proxy fix for proper IP detection behind reverse proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)

# Initialize CSRF Protection
csrf = CSRFProtect(app)
logger.info("CSRF protection enabled")

# Initialize Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[app.config.get('RATELIMIT_DEFAULT', "200 per day, 50 per hour")],
    storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
)
logger.info("Rate limiting enabled")

# Initialize Security Headers (Talisman)
# Disable in development, enable in production
if app.config.get('ENV') == 'production':
    Talisman(app,
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        content_security_policy=app.config.get('CONTENT_SECURITY_POLICY'),
        content_security_policy_nonce_in=['script-src', 'style-src']
    )
    logger.info("Security headers enabled (production mode)")
else:
    logger.info("Security headers disabled (development mode)")

# Initialize extensions with app
from extensions import db, login_manager
db.init_app(app)
login_manager.init_app(app)

# Import models (after extensions initialization)
from models import User, SimulationSession, KnowledgeGraphNode, KnowledgeGraphEdge, MCPServer, MCPResource, MCPTool, MCPPrompt
from security_utils import PasswordValidator, URLValidator, InputSanitizer, validate_simulation_parameters, PasswordResetManager

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    headers = app.config.get('SECURITY_HEADERS', {})
    for header, value in headers.items():
        response.headers[header] = value
    return response

# Create tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

# Register MCP blueprint
try:
    from backend.mcp_api import mcp_bp
    app.register_blueprint(mcp_bp)
    logger.info("MCP blueprint registered")
except ImportError as e:
    logger.warning(f"Could not register MCP blueprint: {e}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limit login attempts
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = 'remember' in request.form

        # Input validation
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')

        # Query user
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Check if account is active
            if not user.active:
                flash('Account is disabled. Please contact administrator.', 'error')
                logger.warning(f"Login attempt for disabled account: {username}")
                return render_template('login.html')

            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            logger.info(f"Successful login: {username}")

            # Safe redirect
            next_page = request.args.get('next')
            if next_page and URLValidator.is_safe_redirect_url(next_page):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            # Don't reveal whether username or password was wrong
            flash('Invalid credentials', 'error')
            logger.warning(f"Failed login attempt: {username}")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # Rate limit registration
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')

        # Validate username
        if len(username) < 3 or len(username) > 64:
            flash('Username must be between 3 and 64 characters', 'error')
            return render_template('register.html')

        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            flash('Username can only contain letters, numbers, underscores, and hyphens', 'error')
            return render_template('register.html')

        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Invalid email address', 'error')
            return render_template('register.html')

        # Validate password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        # Validate password strength
        is_valid, message = PasswordValidator.validate(password)
        if not is_valid:
            flash(f'Password validation failed: {message}', 'error')
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
            logger.info(f"New user registered: {username}")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user {username}: {e}")
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # Rate limit password reset requests
def forgot_password():
    """Request a password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        # Validate email
        if not email:
            flash('Email address is required', 'error')
            return render_template('forgot_password.html')

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Invalid email address', 'error')
            return render_template('forgot_password.html')

        # Look up user by email
        user = User.query.filter_by(email=email).first()

        # SECURITY: Always show success message even if email doesn't exist
        # This prevents email enumeration attacks
        if user:
            # Generate reset token
            token = PasswordResetManager.generate_reset_token(user.email)

            # TODO: Send email with reset link
            # For now, log the token (in production, this should send an email)
            reset_url = url_for('reset_password', token=token, _external=True)
            logger.info(f"Password reset requested for {email}")
            logger.info(f"Reset URL (EMAIL NOT CONFIGURED): {reset_url}")

            # In production, send email here:
            # send_password_reset_email(user.email, reset_url)

        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # Rate limit password reset attempts
def reset_password(token):
    """Reset password using a valid token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Verify token
        email = PasswordResetManager.verify_reset_token(token, max_age=3600)  # 1 hour expiry
        if not email:
            flash('Invalid or expired password reset link', 'error')
            return redirect(url_for('forgot_password'))

        # Get new password from form
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate passwords
        if not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)

        # Validate password strength
        is_valid, message = PasswordValidator.validate(password)
        if not is_valid:
            flash(f'Password validation failed: {message}', 'error')
            return render_template('reset_password.html', token=token)

        # Look up user and update password
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('login'))

        # Update password
        user.set_password(password)

        try:
            db.session.commit()
            logger.info(f"Password reset successful for {email}")
            flash('Your password has been reset successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting password for {email}: {e}")
            flash('An error occurred while resetting your password. Please try again.', 'error')
            return render_template('reset_password.html', token=token)

    # GET request - verify token and show form
    email = PasswordResetManager.verify_reset_token(token, max_age=3600)
    if not email:
        flash('Invalid or expired password reset link', 'error')
        return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', token=token)

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
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
    # Get user's simulation sessions - with proper authorization
    user_simulations = SimulationSession.query.filter_by(
        user_id=current_user.id
    ).order_by(SimulationSession.created_at.desc()).all()
    return render_template('simulations.html', simulations=user_simulations)

@app.route('/create_simulation', methods=['POST'])
@login_required
@limiter.limit("10 per hour")  # Rate limit simulation creation
def create_simulation():
    # Get simulation parameters from form
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    sim_type = request.form.get('sim_type', '').strip()

    # Validate input
    if not name or not sim_type:
        flash('Simulation name and type are required', 'error')
        return redirect(url_for('simulations'))

    if len(name) > 128:
        flash('Simulation name must be less than 128 characters', 'error')
        return redirect(url_for('simulations'))

    # Parse and validate numeric parameters
    refinement_steps_str = request.form.get('refinement_steps', '12')
    confidence_threshold_str = request.form.get('confidence_threshold', '0.85')

    valid, refinement_steps = InputSanitizer.validate_integer_range(refinement_steps_str, 1, 100)
    if not valid:
        flash('Refinement steps must be between 1 and 100', 'error')
        return redirect(url_for('simulations'))

    valid, confidence_threshold = InputSanitizer.validate_float_range(confidence_threshold_str, 0.0, 1.0)
    if not valid:
        flash('Confidence threshold must be between 0.0 and 1.0', 'error')
        return redirect(url_for('simulations'))

    entropy_sampling = 'entropy_sampling' in request.form
    auto_start = 'auto_start' in request.form

    # Create simulation parameters
    parameters = {
        'simulation_type': sim_type,
        'refinement_steps': refinement_steps,
        'confidence_threshold': confidence_threshold,
        'entropy_sampling': entropy_sampling
    }

    # Validate parameters
    is_valid, error_msg = validate_simulation_parameters(parameters)
    if not is_valid:
        flash(f'Invalid parameters: {error_msg}', 'error')
        return redirect(url_for('simulations'))

    # Create new simulation session
    new_simulation = SimulationSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.id,  # Tie to current user
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

        logger.info(f"Simulation created: {name} by user {current_user.username}")

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
@login_required
def start_simulation(sim_id):
    """Start a pending simulation - with authorization check"""
    simulation = SimulationSession.query.filter_by(
        id=sim_id,
        user_id=current_user.id  # Authorization check
    ).first_or_404()

    if simulation.status != 'pending':
        flash('Only pending simulations can be started', 'error')
        return redirect(url_for('simulations'))

    try:
        simulation.status = 'running'
        simulation.started_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Simulation started: {simulation.name} by {current_user.username}")
        flash(f'Simulation "{simulation.name}" started successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting simulation: {e}")
        flash('An error occurred while starting the simulation', 'error')

    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/pause', methods=['POST'])
@login_required
def pause_simulation(sim_id):
    """Pause a running simulation - with authorization check"""
    simulation = SimulationSession.query.filter_by(
        id=sim_id,
        user_id=current_user.id  # Authorization check
    ).first_or_404()

    if simulation.status != 'running':
        flash('Only running simulations can be paused', 'error')
        return redirect(url_for('simulations'))

    try:
        simulation.status = 'paused'
        db.session.commit()

        logger.info(f"Simulation paused: {simulation.name} by {current_user.username}")
        flash(f'Simulation "{simulation.name}" paused successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error pausing simulation: {e}")
        flash('An error occurred while pausing the simulation', 'error')

    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/resume', methods=['POST'])
@login_required
def resume_simulation(sim_id):
    """Resume a paused simulation - with authorization check"""
    simulation = SimulationSession.query.filter_by(
        id=sim_id,
        user_id=current_user.id  # Authorization check
    ).first_or_404()

    if simulation.status != 'paused':
        flash('Only paused simulations can be resumed', 'error')
        return redirect(url_for('simulations'))

    try:
        simulation.status = 'running'
        db.session.commit()

        logger.info(f"Simulation resumed: {simulation.name} by {current_user.username}")
        flash(f'Simulation "{simulation.name}" resumed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resuming simulation: {e}")
        flash('An error occurred while resuming the simulation', 'error')

    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/delete', methods=['POST'])
@login_required
def delete_simulation(sim_id):
    """Delete a simulation - with authorization check"""
    simulation = SimulationSession.query.filter_by(
        id=sim_id,
        user_id=current_user.id  # Authorization check
    ).first_or_404()

    sim_name = simulation.name

    try:
        db.session.delete(simulation)
        db.session.commit()

        logger.info(f"Simulation deleted: {sim_name} by {current_user.username}")
        flash(f'Simulation "{sim_name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting simulation: {e}")
        flash('An error occurred while deleting the simulation', 'error')

    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>')
@login_required
def view_simulation(sim_id):
    """View simulation details - with authorization check"""
    simulation = SimulationSession.query.filter_by(
        id=sim_id,
        user_id=current_user.id  # Authorization check
    ).first_or_404()
    return render_template('simulation_details.html', simulation=simulation)

@app.route('/simulation/<int:sim_id>/results')
@login_required
def simulation_results(sim_id):
    """View simulation results - with authorization check"""
    simulation = SimulationSession.query.filter_by(
        id=sim_id,
        user_id=current_user.id  # Authorization check
    ).first_or_404()

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
    logger.error(f"Internal server error: {e}")
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded. Please try again later."), 429

# Run the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
