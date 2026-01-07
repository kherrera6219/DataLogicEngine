#!/usr/bin/env python3
"""
Production Security Validator for DataLogicEngine

Run this script before deployment to verify security configuration.
Usage: python validate_production.py
"""

import os
import sys
import re
from pathlib import Path

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[0;33m'
NC = '\033[0m'

def ok(msg):
    print(f"{GREEN}✓{NC} {msg}")

def warn(msg):
    print(f"{YELLOW}⚠{NC} {msg}")

def fail(msg):
    print(f"{RED}✗{NC} {msg}")

def main():
    print("=" * 60)
    print("DataLogicEngine Production Security Validator")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # Check environment
    flask_env = os.environ.get('FLASK_ENV', '')
    if flask_env == 'production':
        ok(f"FLASK_ENV is set to production")
    elif flask_env == 'development':
        warn("FLASK_ENV is development (change for production)")
        warnings.append("FLASK_ENV should be 'production'")
    else:
        warn(f"FLASK_ENV is '{flask_env}' (set to 'production')")
        warnings.append("FLASK_ENV should be 'production'")
    
    # Check SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY', '')
    if len(secret_key) >= 32:
        ok(f"SECRET_KEY is set ({len(secret_key)} chars)")
    elif secret_key:
        fail(f"SECRET_KEY too short ({len(secret_key)} chars, need 32+)")
        errors.append("SECRET_KEY must be at least 32 characters")
    else:
        fail("SECRET_KEY is not set")
        errors.append("SECRET_KEY is required")
    
    # Check SESSION_SECRET
    session_secret = os.environ.get('SESSION_SECRET', '')
    if len(session_secret) >= 32:
        ok(f"SESSION_SECRET is set ({len(session_secret)} chars)")
    elif session_secret:
        fail(f"SESSION_SECRET too short")
        errors.append("SESSION_SECRET must be at least 32 characters")
    else:
        fail("SESSION_SECRET is not set")
        errors.append("SESSION_SECRET is required")
    
    # Check DATABASE_URL
    db_url = os.environ.get('DATABASE_URL', '')
    if 'postgresql' in db_url:
        ok("DATABASE_URL is PostgreSQL")
        if 'localhost' in db_url or '127.0.0.1' in db_url:
            warn("DATABASE_URL points to localhost")
            warnings.append("DATABASE_URL should use production host")
    elif 'sqlite' in db_url:
        fail("DATABASE_URL is SQLite (use PostgreSQL for production)")
        errors.append("Use PostgreSQL in production")
    elif db_url:
        warn(f"DATABASE_URL: {db_url[:30]}...")
    else:
        fail("DATABASE_URL is not set")
        errors.append("DATABASE_URL is required")
    
    # Check admin credentials
    admin_user = os.environ.get('ADMIN_USERNAME', '')
    admin_pass = os.environ.get('ADMIN_PASSWORD', '')
    
    insecure_users = {'admin', 'root', 'administrator', 'test', 'user'}
    insecure_passes = {'admin', 'admin123', 'password', 'password123', '123456', 'test'}
    
    if admin_user.lower() in insecure_users:
        fail(f"ADMIN_USERNAME is insecure: '{admin_user}'")
        errors.append("Change ADMIN_USERNAME to something unique")
    elif admin_user:
        ok(f"ADMIN_USERNAME is custom")
    
    if admin_pass in insecure_passes:
        fail("ADMIN_PASSWORD is insecure")
        errors.append("Change ADMIN_PASSWORD to a strong password")
    elif len(admin_pass) < 12:
        fail(f"ADMIN_PASSWORD too short ({len(admin_pass)} chars, need 12+)")
        errors.append("ADMIN_PASSWORD must be at least 12 characters")
    elif admin_pass:
        ok("ADMIN_PASSWORD meets requirements")
    
    # Check SESSION_COOKIE_SECURE
    cookie_secure = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower()
    if cookie_secure == 'true':
        ok("SESSION_COOKIE_SECURE is enabled")
    else:
        fail("SESSION_COOKIE_SECURE should be 'true' for HTTPS")
        errors.append("Set SESSION_COOKIE_SECURE=true")
    
    # Check for .env file
    env_file = Path('.env')
    if env_file.exists():
        ok(".env file exists")
    else:
        warn(".env file not found (using environment variables)")
        warnings.append("No .env file found")
    
    # Check requirements
    req_file = Path('requirements.txt')
    if req_file.exists():
        content = req_file.read_text()
        if 'sentry-sdk' in content:
            ok("sentry-sdk in requirements")
        else:
            warn("sentry-sdk not in requirements (add for error tracking)")
            warnings.append("Add sentry-sdk for error tracking")
    
    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if errors:
        print(f"{RED}ERRORS ({len(errors)}):{NC}")
        for e in errors:
            print(f"  - {e}")
    
    if warnings:
        print(f"{YELLOW}WARNINGS ({len(warnings)}):{NC}")
        for w in warnings:
            print(f"  - {w}")
    
    if not errors and not warnings:
        print(f"{GREEN}All checks passed!{NC}")
        return 0
    elif errors:
        print(f"\n{RED}Fix errors before deploying to production!{NC}")
        return 1
    else:
        print(f"\n{YELLOW}Review warnings before deploying.{NC}")
        return 0

if __name__ == '__main__':
    sys.exit(main())
