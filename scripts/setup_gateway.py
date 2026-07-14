#!/usr/bin/env python
# ruff: noqa: E402
"""
LLM Gateway Setup Script

Creates default LLM provider configurations for the gateway.
Run after database migration: flask db upgrade
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from extensions import db
from models import LLMProvider, ExternalAPIKey, User
from backend.llm_gateway.model_defaults import (
    GOOGLE_PRIMARY_MODEL,
    OPENAI_STANDARD_MODEL,
)


def setup_default_providers():
    """Create default provider configurations based on environment variables."""
    
    providers_created = []
    
    with app.app_context():
        # Check for existing providers
        existing = LLMProvider.query.count()
        if existing > 0:
            print(f"Found {existing} existing providers. Skipping setup.")
            return
        
        # OpenAI (default if OPENAI_API_KEY is set)
        if os.environ.get("OPENAI_API_KEY"):
            provider = LLMProvider(
                name="OpenAI",
                provider_type="openai",
                model_id=OPENAI_STANDARD_MODEL,
                is_active=True,
                is_default=True,
                priority=10,
                timeout_seconds=60,
                max_retries=2,
                config={"availability_status": "stored"},
            )
            provider.set_api_key(os.environ["OPENAI_API_KEY"])
            db.session.add(provider)
            providers_created.append("OpenAI")
        
        # Google Gemini
        google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if google_key:
            provider = LLMProvider(
                name="Google Gemini",
                provider_type="google",
                model_id=GOOGLE_PRIMARY_MODEL,
                is_active=True,
                is_default=not bool(os.environ.get("OPENAI_API_KEY")),
                priority=20,
                timeout_seconds=60,
                max_retries=2,
                config={"availability_status": "stored"},
            )
            provider.set_api_key(google_key)
            db.session.add(provider)
            providers_created.append("Google Gemini")
        
        if providers_created:
            db.session.commit()
            print(f"Created {len(providers_created)} providers: {', '.join(providers_created)}")
        else:
            print("No API keys found in environment. Set one of:")
            print("  - OPENAI_API_KEY")
            print("  - GOOGLE_API_KEY or GEMINI_API_KEY")


def create_test_api_key():
    """Create a test API key for development."""

    with app.app_context():
        # Check for existing keys
        existing = ExternalAPIKey.query.filter_by(name="Development Key").first()
        if existing:
            print(f"Development key already exists: {existing.key_prefix}...")
            return
        
        # Generate new key
        full_key, prefix, key_hash = ExternalAPIKey.generate_key()
        
        # Need a user - single-mode has one owner; use the first user.
        user = User.query.first()
        
        if not user:
            print("No users found. Create a user first.")
            return
        
        api_key = ExternalAPIKey(
            name="Development Key",
            key_prefix=prefix,
            key_hash=key_hash,
            user_id=user.id,
            permissions={"scopes": ["chat", "stream", "models:read", "run:cancel"]},
            rate_limit_rpm=1000,
        )
        db.session.add(api_key)
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("DEVELOPMENT API KEY CREATED")
        print("=" * 60)
        print(f"Key: {full_key}")
        print("=" * 60)
        print("SAVE THIS KEY - IT WILL NOT BE SHOWN AGAIN")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Gateway Setup")
    parser.add_argument("--providers", action="store_true", help="Set up default providers from env")
    parser.add_argument("--api-key", action="store_true", help="Create development API key")
    parser.add_argument("--all", action="store_true", help="Run all setup steps")
    
    args = parser.parse_args()
    
    if args.all or args.providers:
        setup_default_providers()
    
    if args.all or args.api_key:
        create_test_api_key()
    
    if not any([args.all, args.providers, args.api_key]):
        parser.print_help()
