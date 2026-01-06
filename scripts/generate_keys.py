#!/usr/bin/env python3
"""
Generate strong cryptographic keys for the application.
Usage: python scripts/generate_keys.py
"""

import secrets
import string

def generate_key(length=64):
    """Generate a cryptographically strong random string."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for i in range(length))

def generate_safe_key(length=64):
    """Generate a safe key (alphanumeric + some safe symbols) to avoid shell escaping issues."""
    alphabet = string.ascii_letters + string.digits + "-_!@#%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))

def main():
    print("=" * 60)
    print("   DataLogicEngine Security Key Generator")
    print("=" * 60)
    print("\nCopy these values to your .env file:\n")

    keys = {
        "SECRET_KEY": generate_safe_key(64),
        "SECURITY_PASSWORD_SALT": generate_safe_key(32),
        "JWT_SECRET_KEY": generate_safe_key(64),
        "WTF_CSRF_SECRET_KEY": generate_safe_key(64),
        "SESSION_SECRET": generate_safe_key(64)
    }

    for key, value in keys.items():
        print(f"{key}={value}")

    print("\n" + "=" * 60)
    print("WARNING: Keep these keys secret! Do not commit them to version control.")
    print("=" * 60)

if __name__ == "__main__":
    main()
