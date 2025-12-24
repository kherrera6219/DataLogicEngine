"""
Authentication Routes Blueprint

Handles user login, logout, and registration.
"""

import datetime
from datetime import UTC
import logging
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required

from extensions import db
from models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


def is_safe_redirect_url(target: str) -> bool:
    """Check if redirect URL is safe (same host, no external redirects)."""
    if not target:
        return False
    parsed = urlparse(target)
    return parsed.netloc == '' and target.startswith('/')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with security checks."""
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
        if user.is_account_locked():
            flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'danger')
            return render_template('login.html')
        
        if not user.check_password(password):
            user.record_failed_login()
            db.session.commit()
            remaining = max(0, 5 - user.failed_login_attempts)
            if remaining > 0:
                flash(f'Invalid username or password. {remaining} attempts remaining.', 'danger')
            else:
                flash('Account locked due to too many failed attempts. Try again in 30 minutes.', 'danger')
            return render_template('login.html')
        
        if user.is_password_expired():
            flash('Your password has expired. Please contact an administrator to reset it.', 'warning')
            return render_template('login.html')
        
        if user.force_password_change:
            flash('You must change your password before continuing.', 'warning')
            return render_template('login.html')
        
        user.record_successful_login()
        login_user(user, remember=remember)
        db.session.commit()
        
        days_until_expiry = user.days_until_password_expiry()
        if days_until_expiry is not None and 0 < days_until_expiry <= 7:
            flash(f'Your password will expire in {days_until_expiry} days. Please change it soon.', 'warning')
        
        next_page = request.args.get('next')
        if next_page and is_safe_redirect_url(next_page):
            return redirect(next_page)
        return redirect(url_for('pages.dashboard'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('pages.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('pages.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        try:
            user = User()
            user.username = username
            user.email = email
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration', 'danger')
    
    return render_template('register.html')
