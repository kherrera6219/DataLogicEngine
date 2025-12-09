#!/usr/bin/env python3
"""
Generate Secure Admin Credentials for DataLogicEngine

This script generates cryptographically strong admin credentials
that meet security best practices.

Usage:
    python3 scripts/generate_admin_credentials.py
"""

import secrets
import string


def generate_strong_password(length=32):
    """Generate a cryptographically strong password.

    Args:
        length: Length of password (minimum 12, recommended 32+)

    Returns:
        Strong password string with mixed case, numbers, and symbols
    """
    if length < 12:
        raise ValueError("Password length must be at least 12 characters")

    # Use all character types for maximum entropy
    alphabet = string.ascii_letters + string.digits + string.punctuation

    # Generate password
    password = ''.join(secrets.choice(alphabet) for _ in range(length))

    # Verify it meets requirements (has at least one of each type)
    has_lower = any(c in string.ascii_lowercase for c in password)
    has_upper = any(c in string.ascii_uppercase for c in password)
    has_digit = any(c in string.digits for c in password)
    has_symbol = any(c in string.punctuation for c in password)

    # Regenerate if requirements not met (very rare)
    if not (has_lower and has_upper and has_digit and has_symbol):
        return generate_strong_password(length)

    return password


def generate_admin_credentials():
    """Generate complete set of admin credentials."""
    username = f"admin_{secrets.token_hex(6)}"
    password = generate_strong_password(32)
    email = f"admin@ukg-{secrets.token_hex(4)}.local"

    return username, password, email


def main():
    """Main entry point."""
    print("=" * 70)
    print("DataLogicEngine - Secure Admin Credentials Generator")
    print("=" * 70)
    print()

    username, password, email = generate_admin_credentials()

    print("Generated Admin Credentials:")
    print("-" * 70)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Email:    {email}")
    print("-" * 70)
    print()

    print("Add these to your .env file:")
    print()
    print(f"ADMIN_USERNAME={username}")
    print(f"ADMIN_PASSWORD={password}")
    print(f"ADMIN_EMAIL={email}")
    print()

    print("⚠️  SECURITY REMINDERS:")
    print("  1. Store these credentials in a secure password manager")
    print("  2. Never commit .env to version control")
    print("  3. Use different credentials for each environment")
    print("  4. Rotate credentials quarterly")
    print("  5. Consider forcing password change on first login")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
