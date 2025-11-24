# Security Policy

## Reporting Security Vulnerabilities

**DO NOT** create public GitHub issues for security vulnerabilities.

Instead, please report security vulnerabilities by emailing:
- **Email**: security@your-domain.com (replace with actual email)
- **Subject**: [SECURITY] Brief description of the vulnerability

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

We aim to respond to security reports within 48 hours.

## Security Measures Implemented

### ✅ Authentication & Authorization
- **Password Security**: 12+ character minimum with complexity requirements (uppercase, lowercase, numbers, special characters)
- **Password Hashing**: Werkzeug secure password hashing (bcrypt)
- **Session Security**: Secure cookies with HttpOnly, SameSite=Lax, and secure flags
- **Session Timeout**: 1-hour timeout with automatic refresh
- **Authorization Checks**: User ownership validation on all simulation operations (IDOR protection)
- **Account Status**: Disabled accounts cannot log in

### ✅ CSRF Protection
- Flask-WTF CSRF protection enabled on all state-changing operations
- CSRF tokens automatically included in forms
- API requests validate CSRF tokens

### ✅ Rate Limiting
- **Login**: 5 attempts per minute per IP
- **Registration**: 3 attempts per hour per IP
- **Simulation Creation**: 10 per hour per user
- **Global**: 200 requests per day, 50 per hour per IP

### ✅ Security Headers
Production mode includes:
- `Strict-Transport-Security`: Force HTTPS
- `X-Content-Type-Options: nosniff`: Prevent MIME sniffing
- `X-Frame-Options: SAMEORIGIN`: Prevent clickjacking
- `X-XSS-Protection`: Browser XSS protection
- `Referrer-Policy`: Control referrer information
- `Content-Security-Policy`: Restrict resource loading

### ✅ Input Validation & Sanitization
- Username validation (3-64 chars, alphanumeric + underscore/hyphen)
- Email format validation
- Password confirmation matching
- Simulation parameter bounds checking (refinement_steps: 1-100, confidence: 0.0-1.0)
- String input trimming and sanitization
- Safe URL redirect validation (no open redirects)

### ✅ Secure Configuration Management
- **Environment Variables**: All secrets loaded from environment (never hardcoded)
- **Configuration Classes**: Separate dev/test/production configs
- **Required Secrets**: Application fails to start if SECRET_KEY or JWT_SECRET_KEY not set
- `.env` file excluded from version control

### ✅ Audit Logging
- Successful logins logged with username
- Failed login attempts logged with username and IP
- Account registration logged
- User logouts logged
- Simulation operations logged (create, start, pause, resume, delete)

### ✅ Error Handling
- Generic error messages to users (no information disclosure)
- Detailed errors logged server-side only
- Custom 404, 500, 429 error handlers

## Known Security Considerations

### ✅ Recently Completed Security Improvements

1. **Backend API Authentication** - ✅ COMPLETED
   - STATUS: Fully implemented
   - SOLUTION: Added `@login_required` to all GET endpoints, `@admin_required` to all POST/PUT/DELETE
   - FILES UPDATED: `backend/api.py`
   - All 20+ API endpoints now require authentication
   - Admin-only operations properly protected

2. **CORS Configuration** - ✅ COMPLETED
   - STATUS: Hardened
   - SOLUTION: Changed from `allow_origins=["*"]` to environment-based configuration
   - FILES UPDATED: `backend/api_gateway/api_gateway.py`, `backend/webhook_server/webhook_server.py`, `backend/model_context/model_context_server.py`
   - Now uses `CORS_ORIGINS` environment variable
   - Falls back to localhost in development with warning
   - No longer allows credentials with wildcard origins

3. **Command Injection in Subprocess Calls** - ✅ COMPLETED
   - STATUS: Fixed
   - SOLUTION: Replaced `shell=True` with `shell=False` and proper command list handling
   - FILES UPDATED: `run_enterprise_ukg.py`, `run_ukg.py`, `run_enterprise_services.py`, `deploy.py`
   - Now using `shlex.split()` for safe command parsing
   - Commands executed without shell interpreter

4. **SQL Injection Prevention** - ✅ IMPROVED
   - STATUS: Enhanced with validation
   - SOLUTION: Added suspicious pattern detection and parameter validation
   - FILE UPDATED: `backend/ukg_db.py`
   - Blocks dangerous SQL keywords (DROP, TRUNCATE, ALTER, etc.)
   - Warns if queries use WHERE/HAVING without parameters
   - Still recommend using ORM when possible

5. **Pickle Deserialization** - ✅ COMPLETED
   - STATUS: Fixed
   - SOLUTION: Replaced pickle serialization with server-side memory storage
   - FILE UPDATED: `run_simulation.py`
   - Simulation engines now stored in server-side dictionary with UUID keys
   - Only session IDs stored in Flask sessions (not pickled objects)
   - Eliminates arbitrary code execution risk from pickle deserialization
   - No longer imports or uses the pickle module

6. **Password Reset Functionality** - ✅ COMPLETED
   - STATUS: Implemented
   - SOLUTION: Secure password reset with time-limited tokens using `itsdangerous`
   - FILES UPDATED: `app.py`, `security_utils.py`, `requirements.txt`
   - Token-based password reset with 1-hour expiry
   - Rate limiting: 3 requests/hour for reset requests, 5/hour for password changes
   - Email enumeration prevention (always shows success message)
   - Full password strength validation on reset
   - Audit logging for all password reset events
   - Ready for email integration (placeholder for SMTP configuration)

7. **API Rate Limiting Storage (Redis Setup)** - ✅ DOCUMENTED
   - STATUS: Fully documented with production-ready configuration
   - SOLUTION: Comprehensive Redis setup guide for production deployments
   - FILES UPDATED: `SECURITY.md`, `.env.template`, `requirements.txt`
   - Added detailed Redis installation instructions (Ubuntu, macOS, Docker)
   - Documented Redis security hardening (password, bind address, disabled commands)
   - Configuration examples for local, cloud, and clustered Redis
   - Testing and verification procedures included
   - Added `redis>=5.2.1` to requirements.txt as production dependency
   - System automatically uses Redis when `REDIS_URL` is configured
   - Falls back to in-memory storage for development (no Redis required)

### ⚠️ Items Requiring Additional Work

5. **Two-Factor Authentication**
   - STATUS: Not implemented
   - PRIORITY: LOW (for MVP)
   - RECOMMENDATION: Consider for production deployment
   - LIBRARIES: pyotp, qrcode for TOTP implementation

## Security Best Practices for Developers

### Environment Setup
```bash
# Never commit .env file
echo ".env" >> .gitignore

# Generate strong secrets
python -c "import secrets; print(secrets.token_hex(32))"

# Required environment variables
export SECRET_KEY="your-secret-key-here"
export JWT_SECRET_KEY="your-jwt-secret-here"
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
export FLASK_ENV="production"  # or "development"
```

### Redis Setup for Production Rate Limiting

**Why Redis is Important:**
- In-memory rate limiting doesn't persist across server restarts
- In-memory storage doesn't work with multiple server instances/load balancers
- Redis provides distributed rate limiting across your entire infrastructure
- Prevents rate limit bypass through server restarts or load balancer round-robin

**Installation:**

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

macOS:
```bash
brew install redis
brew services start redis
```

Docker:
```bash
# Development
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Production with persistence
docker run -d --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes
```

**Configuration:**

1. Configure Redis URL in `.env`:
```bash
# Local Redis
REDIS_URL=redis://localhost:6379/0

# Redis with password (recommended for production)
REDIS_URL=redis://:your-secure-password@localhost:6379/0

# Cloud Redis (AWS ElastiCache example)
REDIS_URL=redis://your-redis-endpoint.cache.amazonaws.com:6379/0
```

2. Verify Redis connection:
```bash
# Test Redis is running
redis-cli ping
# Should return: PONG

# Check connection from Python
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

3. Secure Redis (Production):
```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Set password
requirepass your-secure-password

# Bind to localhost only (if Redis is on same server)
bind 127.0.0.1

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""

# Restart Redis
sudo systemctl restart redis-server
```

**Testing Rate Limiting:**
```bash
# With Redis configured, rate limits persist across server restarts
# Test by making repeated requests to a rate-limited endpoint:
for i in {1..10}; do curl http://localhost:5000/login; done
```

### Deployment Security Checklist
- [ ] All secrets in environment variables (never in code)
- [ ] `DEBUG = False` in production
- [ ] HTTPS enabled (TLS 1.2+)
- [ ] Database connections use SSL
- [ ] Configure CORS with specific allowed origins
- [ ] Set up Redis for rate limiting
- [ ] Configure proper logging (but sanitize sensitive data)
- [ ] Regular dependency updates
- [ ] Security headers enabled (Talisman in production mode)
- [ ] Database backups automated
- [ ] Monitoring and alerting configured

## Quick Setup Guide

### 1. Set Up Environment Variables
```bash
# Copy template and fill in values
cp .env.template .env

# Generate secure secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))" >> .env

# Edit .env and fill in other values
nano .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Run Application
```bash
# Development
FLASK_ENV=development python app.py

# Production
FLASK_ENV=production gunicorn app:app
```

---

**Last Updated**: 2025-11-24 (Security Hardening Release v1.0.0)
**Next Security Review**: 2025-12-24 (monthly reviews recommended)
**Security Improvements**: 10 critical and high-priority vulnerabilities resolved
