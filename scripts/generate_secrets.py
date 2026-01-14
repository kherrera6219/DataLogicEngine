#!/usr/bin/env python3
"""
Generate secure secrets for production deployment.
Run this script to generate cryptographically secure keys for your .env file.

Usage:
    python scripts/generate_secrets.py

Output:
    Prints secure secrets that should be added to your .env.production file
"""

import secrets
import sys

def generate_secret(length=32):
    """Generate a cryptographically secure secret key."""
    return secrets.token_hex(length)

def main():
    print("=" * 80)
    print("DataLogicEngine - Production Secrets Generator")
    print("=" * 80)
    print()
    print("⚠️  SECURITY WARNING:")
    print("   - Never commit these secrets to version control")
    print("   - Store them securely (password manager, vault, etc.)")
    print("   - Generate NEW secrets for each environment")
    print("   - Rotate secrets regularly (every 90 days recommended)")
    print()
    print("=" * 80)
    print()

    # Generate secrets
    secret_key = generate_secret(32)  # 64 characters
    jwt_secret_key = generate_secret(32)  # 64 characters
    session_secret = generate_secret(32)  # 64 characters

    # Display in .env format
    print("Add these lines to your .env.production file:")
    print()
    print("# ============================================================================")
    print("# SECURITY SETTINGS - Generated on", __import__('datetime').datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC'))
    print("# ============================================================================")
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret_key}")
    print(f"SESSION_SECRET={session_secret}")
    print()
    print("# ============================================================================")
    print("# ADMIN CREDENTIALS - CHANGE THESE!")
    print("# ============================================================================")
    print("# Generate strong admin credentials:")
    admin_username = f"admin_{secrets.token_hex(4)}"
    admin_password = secrets.token_urlsafe(24)  # 24 characters, URL-safe
    print(f"ADMIN_USERNAME={admin_username}")
    print(f"ADMIN_PASSWORD={admin_password}")
    print()

    # Additional security tokens
    print("# ============================================================================")
    print("# OPTIONAL: Additional Security Tokens")
    print("# ============================================================================")
    csrf_key = generate_secret(32)
    encryption_key = generate_secret(32)
    print(f"WTF_CSRF_SECRET_KEY={csrf_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()

    print("=" * 80)
    print("✅ Secrets generated successfully!")
    print()
    print("NEXT STEPS:")
    print("1. Copy the secrets above to your .env.production file")
    print("2. Set FLASK_ENV=production")
    print("3. Configure CORS_ORIGINS with your actual domains")
    print("4. Set SESSION_COOKIE_SECURE=true")
    print("5. Configure your SSL/TLS certificates")
    print("6. Run: python scripts/validate_production_config.py")
    print("=" * 80)

if __name__ == "__main__":
    # Import datetime for timestamp
    from datetime import UTC
    main()
