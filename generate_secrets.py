#!/usr/bin/env python3
"""
Generate secure random secrets for the UKG system.

Run this script to generate secure SECRET_KEY and JWT_SECRET_KEY values
for your .env file.
"""

import secrets
import os

def generate_secret(length=64):
    """Generate a cryptographically secure random secret."""
    return secrets.token_hex(length)

def main():
    print("=" * 70)
    print("UKG System - Secure Secret Generator")
    print("=" * 70)
    print()
    print("Add these values to your .env file:")
    print()
    print("-" * 70)
    print(f"SECRET_KEY={generate_secret(32)}")
    print(f"JWT_SECRET_KEY={generate_secret(32)}")
    print("-" * 70)
    print()
    print("⚠️  Keep these secrets secure and never commit them to version control!")
    print()

    # Check if .env file exists
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        print(f"✓ Found existing .env file at: {env_path}")
        print("  Please update it manually with the values above.")
    else:
        print(f"⚠️  No .env file found at: {env_path}")
        print("  Copy .env.template to .env and add the values above.")
    print()

if __name__ == "__main__":
    main()
