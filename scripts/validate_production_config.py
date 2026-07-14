#!/usr/bin/env python3
"""
Production Configuration Validator
Validates that all required security settings are properly configured before production deployment.

Usage:
    python scripts/validate_production_config.py

Exit codes:
    0 - All checks passed
    1 - Critical security issues found
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")

def print_pass(message):
    """Print a pass message."""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def print_fail(message):
    """Print a fail message."""
    print(f"{Colors.RED}✗{Colors.END} {message}")

def print_warn(message):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")

def print_info(message):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

class ProductionValidator:
    """Validates production configuration."""

    def __init__(self):
        self.critical_issues = []
        self.warnings = []
        self.info = []

    def check_secrets(self):
        """Check that all secrets are properly configured."""
        print_header("SECRET KEY VALIDATION")

        secrets_to_check = [
            ('SECRET_KEY', 64),
            ('JWT_SECRET_KEY', 64),
            ('SESSION_SECRET', 64),
        ]

        for secret_name, min_length in secrets_to_check:
            secret = os.getenv(secret_name)
            if not secret:
                self.critical_issues.append(f"{secret_name} is not set")
                print_fail(f"{secret_name}: NOT SET")
            elif len(secret) < min_length:
                self.critical_issues.append(f"{secret_name} is too short (min {min_length} chars)")
                print_fail(f"{secret_name}: Too short ({len(secret)} chars, need {min_length}+)")
            else:
                print_pass(f"{secret_name}: Configured ({len(secret)} characters)")

    def check_admin_credentials(self):
        """Check admin credentials are not default."""
        print_header("ADMIN CREDENTIALS VALIDATION")

        admin_user = os.getenv('ADMIN_USERNAME', '')
        admin_pass = os.getenv('ADMIN_PASSWORD', '')

        insecure_usernames = {'admin', 'administrator', 'root', 'test', 'user'}
        insecure_passwords = {'admin', 'admin123', 'password', 'password123', '123456', 'test', 'root'}

        if admin_user.lower() in insecure_usernames:
            self.critical_issues.append("Admin username is a common default")
            print_fail(f"ADMIN_USERNAME: Using default username '{admin_user}'")
        else:
            print_pass("ADMIN_USERNAME: Not a default value")

        if admin_pass in insecure_passwords or len(admin_pass) < 12:
            self.critical_issues.append("Admin password is weak or default")
            print_fail("ADMIN_PASSWORD: Weak password (min 12 chars required)")
        else:
            print_pass(f"ADMIN_PASSWORD: Strong password ({len(admin_pass)} characters)")

    def check_flask_config(self):
        """Check Flask configuration."""
        print_header("FLASK CONFIGURATION VALIDATION")

        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env != 'production':
            self.warnings.append(f"FLASK_ENV is '{flask_env}', should be 'production'")
            print_warn(f"FLASK_ENV: Set to '{flask_env}' (should be 'production' for production)")
        else:
            print_pass("FLASK_ENV: production")

        debug = os.getenv('FLASK_DEBUG', 'False').lower()
        if debug == 'true':
            self.critical_issues.append("FLASK_DEBUG is enabled in production")
            print_fail("FLASK_DEBUG: Enabled (MUST be disabled in production)")
        else:
            print_pass("FLASK_DEBUG: Disabled")

    def check_cors_config(self):
        """Check CORS configuration."""
        print_header("CORS CONFIGURATION VALIDATION")

        cors_origins = os.getenv('CORS_ORIGINS', '')
        if '*' in cors_origins or not cors_origins:
            self.critical_issues.append("CORS origins allow wildcard or not configured")
            print_fail("CORS_ORIGINS: Wildcard (*) or empty (specify exact domains)")
        else:
            print_pass("CORS_ORIGINS: Configured with specific domains")
            print_info(f"  Domains: {cors_origins}")

    def check_session_security(self):
        """Check session security settings."""
        print_header("SESSION SECURITY VALIDATION")

        session_secure = os.getenv('SESSION_COOKIE_SECURE', 'False').lower()
        if session_secure != 'true':
            self.critical_issues.append("SESSION_COOKIE_SECURE must be 'true' in production")
            print_fail("SESSION_COOKIE_SECURE: Not enabled (MUST be 'true' for HTTPS)")
        else:
            print_pass("SESSION_COOKIE_SECURE: Enabled")

        session_httponly = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower()
        if session_httponly != 'true':
            self.warnings.append("SESSION_COOKIE_HTTPONLY should be 'true'")
            print_warn("SESSION_COOKIE_HTTPONLY: Not enabled")
        else:
            print_pass("SESSION_COOKIE_HTTPONLY: Enabled")

        session_samesite = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
        if session_samesite not in ['Strict', 'Lax']:
            self.warnings.append("SESSION_COOKIE_SAMESITE should be 'Strict' or 'Lax'")
            print_warn(f"SESSION_COOKIE_SAMESITE: '{session_samesite}' (should be 'Strict' or 'Lax')")
        else:
            print_pass(f"SESSION_COOKIE_SAMESITE: {session_samesite}")

    def check_database_config(self):
        """Check database configuration."""
        print_header("DATABASE CONFIGURATION VALIDATION")

        database_url = os.getenv('DATABASE_URL', '')
        if not database_url:
            self.critical_issues.append("DATABASE_URL is not set")
            print_fail("DATABASE_URL: NOT SET")
        elif 'sqlite' in database_url.lower():
            self.warnings.append("Using SQLite (PostgreSQL recommended for production)")
            print_warn("DATABASE_URL: Using SQLite (PostgreSQL recommended)")
        elif 'postgresql' in database_url.lower():
            print_pass("DATABASE_URL: PostgreSQL configured")
            # Check for credentials in URL
            if '@localhost' in database_url or 'password' in database_url:
                print_warn("  Database credentials detected in URL (ensure they are strong)")
        else:
            print_pass("DATABASE_URL: Configured")

    def check_llm_providers(self):
        """Check LLM provider configuration."""
        print_header("LLM PROVIDER VALIDATION")

        providers = []
        if os.getenv('OPENAI_API_KEY'):
            providers.append('OpenAI')
            print_pass("OpenAI: API key configured")
        if os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY'):
            providers.append('Google')
            print_pass("Google: API key configured")

        if not providers:
            self.warnings.append("No LLM providers configured")
            print_warn("No LLM providers configured (at least one recommended)")
        else:
            print_info(f"Configured providers: {', '.join(providers)}")

    def check_security_settings(self):
        """Check additional security settings."""
        print_header("ADDITIONAL SECURITY CHECKS")

        max_content_length = os.getenv('MAX_CONTENT_LENGTH')
        if max_content_length:
            print_pass(f"MAX_CONTENT_LENGTH: {int(max_content_length) / (1024*1024):.1f} MB")
        else:
            print_warn("MAX_CONTENT_LENGTH: Not set (using defaults)")

        rate_limit = os.getenv('GLOBAL_RATE_LIMIT')
        if rate_limit:
            print_pass(f"GLOBAL_RATE_LIMIT: {rate_limit}")
        else:
            print_warn("GLOBAL_RATE_LIMIT: Not set (using defaults)")

    def print_summary(self):
        """Print validation summary."""
        print_header("VALIDATION SUMMARY")

        if self.critical_issues:
            print(f"\n{Colors.RED}{Colors.BOLD}CRITICAL ISSUES FOUND: {len(self.critical_issues)}{Colors.END}")
            for issue in self.critical_issues:
                print(f"{Colors.RED}  ✗ {issue}{Colors.END}")
            print(f"\n{Colors.RED}🚫 DEPLOYMENT BLOCKED - Fix critical issues before deploying{Colors.END}\n")
            return False

        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS: {len(self.warnings)}{Colors.END}")
            for warning in self.warnings:
                print(f"{Colors.YELLOW}  ⚠ {warning}{Colors.END}")

        if not self.critical_issues and not self.warnings:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED{Colors.END}")
            print(f"{Colors.GREEN}Configuration is ready for production deployment{Colors.END}\n")
            return True

        if not self.critical_issues:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ WARNINGS PRESENT BUT NO CRITICAL ISSUES{Colors.END}")
            print(f"{Colors.YELLOW}Review warnings before deploying{Colors.END}\n")
            return True

    def validate(self):
        """Run all validation checks."""
        print_header("DataLogicEngine Production Configuration Validator")

        self.check_secrets()
        self.check_admin_credentials()
        self.check_flask_config()
        self.check_cors_config()
        self.check_session_security()
        self.check_database_config()
        self.check_llm_providers()
        self.check_security_settings()

        return self.print_summary()

def main():
    """Main entry point."""
    validator = ProductionValidator()
    success = validator.validate()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
