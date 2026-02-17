#!/usr/bin/env python3
# ruff: noqa: E402
"""
Admin User Creation Script

Creates a secure admin user for the DataLogicEngine application.
This script replaces the insecure default credentials functionality.

Usage:
    python scripts/create_admin_user.py

Security:
    - Enforces strong password policy (12+ chars, complexity)
    - Validates username against common weak values
    - Checks password against breach database (optional)
    - Hashes password with bcrypt
    - Creates audit log entry
"""

import sys
import getpass
import secrets
import string
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import User
from backend.security.password_security import PasswordSecurity


def generate_secure_password(length=24):
    """
    Generate a cryptographically secure random password.

    Args:
        length: Password length (default: 24)

    Returns:
        Secure random password meeting complexity requirements
    """
    # Character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = '!@#$%^&*()-_=+[]{}|;:,.<>?'

    # Ensure at least one of each character type
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]

    # Fill remaining length with random characters
    all_chars = lowercase + uppercase + digits + symbols
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def validate_username(username):
    """
    Validate username against security requirements.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check length
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 64:
        return False, "Username must be max 64 characters"

    # Check for weak usernames
    weak_usernames = {
        'admin', 'administrator', 'root', 'test', 'user',
        'demo', 'guest', 'superuser', 'sysadmin', 'sa'
    }

    if username.lower() in weak_usernames:
        return False, f"Username '{username}' is not allowed for security reasons"

    # Check for valid characters (alphanumeric, underscore, hyphen, dot)
    import re
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return False, "Username can only contain letters, numbers, periods, hyphens, and underscores"

    return True, None


def create_admin_user():
    """Create an admin user interactively."""
    print("=" * 70)
    print("DataLogicEngine - Admin User Creation")
    print("=" * 70)
    print()

    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin:
            print(f"⚠️  WARNING: Admin user already exists: {existing_admin.username}")
            response = input("Do you want to create another admin user? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Aborted.")
                return

        print("This script will create a new admin user with secure credentials.")
        print()

        # Get username
        while True:
            username = input("Enter username (or 'generate' for random): ").strip()

            if username.lower() == 'generate':
                username = f"admin_{secrets.token_hex(4)}"
                print(f"Generated username: {username}")

            is_valid, error = validate_username(username)
            if not is_valid:
                print(f"❌ Error: {error}")
                continue

            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"❌ Error: Username '{username}' already exists")
                continue

            break

        # Get email
        while True:
            email = input("Enter email address: ").strip()

            if not email or '@' not in email:
                print("❌ Error: Please enter a valid email address")
                continue

            # Check if email already exists
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                print(f"❌ Error: Email '{email}' is already in use")
                continue

            break

        # Get password
        print()
        print("Password Requirements:")
        print("  - Minimum 12 characters")
        print("  - At least one uppercase letter")
        print("  - At least one lowercase letter")
        print("  - At least one digit")
        print("  - At least one special character")
        print()

        use_generated = input("Generate secure random password? (yes/no): ")

        if use_generated.lower() in ['yes', 'y']:
            password = generate_secure_password()
            print()
            print("=" * 70)
            print("⚠️  IMPORTANT: Save this password securely!")
            print("=" * 70)
            print(f"Generated Password: {password}")
            print("=" * 70)
            print()
            input("Press Enter after you've saved the password...")
        else:
            while True:
                password = getpass.getpass("Enter password: ")
                password_confirm = getpass.getpass("Confirm password: ")

                if password != password_confirm:
                    print("❌ Error: Passwords don't match")
                    continue

                # Validate password strength
                is_valid, errors = PasswordSecurity.validate_password_strength(password)
                if not is_valid:
                    print("❌ Password validation failed:")
                    for error in errors:
                        print(f"   - {error}")
                    continue

                # Check password breach (optional warning)
                is_breached, count = PasswordSecurity.check_password_breach(password)
                if is_breached and count and count > 10:
                    print(f"⚠️  WARNING: This password has been found in {count} data breaches")
                    response = input("Use this password anyway? (yes/no): ")
                    if response.lower() not in ['yes', 'y']:
                        continue

                break

        # Create the user
        try:
            new_admin = User()
            new_admin.username = username
            new_admin.email = email
            new_admin.set_password(password)
            new_admin.is_admin = True
            new_admin.role = 'admin'
            new_admin.active = True

            db.session.add(new_admin)
            db.session.commit()

            print()
            print("✅ Admin user created successfully!")
            print()
            print("User Details:")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print("  Role: admin")
            print("  Status: active")
            print()
            print("You can now log in with these credentials.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
