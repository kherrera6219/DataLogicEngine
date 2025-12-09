# Credentials Setup Guide

## ⚠️ SECURITY CRITICAL

This document explains how to properly set up secure credentials for the DataLogicEngine application.

## Quick Start

### 1. Generate Secure Secrets

Generate cryptographically strong secrets for your environment:

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"

# Generate SESSION_SECRET
python3 -c "import secrets; print('SESSION_SECRET=' + secrets.token_hex(32))"
```

### 2. Generate Admin Credentials

Use the provided script to generate secure admin credentials:

```bash
python3 scripts/generate_admin_credentials.py
```

Or generate manually with strong password requirements:

```bash
python3 -c "
import secrets, string

# Generate username
username = f'admin_{secrets.token_hex(6)}'

# Generate strong password (32 chars, mixed case, numbers, symbols)
alphabet = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(alphabet) for _ in range(32))

# Generate email
email = f'admin@ukg-{secrets.token_hex(4)}.local'

print(f'ADMIN_USERNAME={username}')
print(f'ADMIN_PASSWORD={password}')
print(f'ADMIN_EMAIL={email}')
"
```

### 3. Configure .env File

1. Copy the template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and add your generated credentials:
   - Add SECRET_KEY, JWT_SECRET_KEY, and SESSION_SECRET
   - Add ADMIN_USERNAME, ADMIN_PASSWORD, and ADMIN_EMAIL
   - Configure database connection strings
   - Set API keys for external services (Azure, OpenAI, etc.)

3. **NEVER commit .env to version control** - it's already in .gitignore

## Password Requirements

Admin passwords MUST meet these minimum requirements:
- At least 12 characters long
- Contains uppercase letters (A-Z)
- Contains lowercase letters (a-z)
- Contains numbers (0-9)
- Contains special characters (!@#$%^&*(),.?":{}|<>)

## Production Deployment

### Recommended Approach: Secrets Manager

For production deployments, use a secrets management service instead of .env files:

**Azure Key Vault:**
```bash
# Store secrets in Azure Key Vault
az keyvault secret set --vault-name myVault --name SECRET_KEY --value "your-secret-here"
```

**AWS Secrets Manager:**
```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret --name DataLogicEngine/SECRET_KEY --secret-string "your-secret-here"
```

**HashiCorp Vault:**
```bash
# Store secrets in Vault
vault kv put secret/datalogicengine SECRET_KEY="your-secret-here"
```

### Environment Variables

Set secrets as environment variables in your deployment platform:

**Docker:**
```yaml
environment:
  - SECRET_KEY=${SECRET_KEY}
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  - ADMIN_USERNAME=${ADMIN_USERNAME}
  - ADMIN_PASSWORD=${ADMIN_PASSWORD}
```

**Kubernetes:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: datalogicengine-secrets
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  JWT_SECRET_KEY: <base64-encoded-secret>
  ADMIN_PASSWORD: <base64-encoded-password>
```

## First-Time Setup Checklist

- [ ] Generate SECRET_KEY, JWT_SECRET_KEY, and SESSION_SECRET
- [ ] Generate secure admin credentials
- [ ] Copy .env.template to .env
- [ ] Configure all required environment variables
- [ ] Verify .env is in .gitignore and NOT committed to git
- [ ] Test login with generated admin credentials
- [ ] Force password change on first login (if implementing)
- [ ] Document credentials in your team's secure password manager
- [ ] Set up secrets rotation schedule (quarterly recommended)

## Security Best Practices

1. **Never use default credentials** - Always generate unique, strong credentials
2. **Rotate secrets regularly** - Change production secrets quarterly
3. **Use different secrets per environment** - Dev, staging, and production should have unique secrets
4. **Limit access** - Only authorized personnel should have access to production secrets
5. **Audit access** - Log and monitor access to secrets
6. **Backup credentials securely** - Store backup credentials in encrypted password manager

## Troubleshooting

### Application won't start in production

**Error:** `ValueError: SECRET_KEY environment variable must be set for production!`

**Solution:** Ensure SECRET_KEY is set in production environment. The application enforces this for security.

### Admin login fails

**Error:** Invalid credentials

**Solution:**
1. Verify ADMIN_USERNAME and ADMIN_PASSWORD in .env match what you're entering
2. Check that password meets requirements (12+ chars)
3. Verify database has been initialized: `python3 -c "from app import app, db; app.app_context().push(); db.create_all()"`

### Secrets in version control

**Error:** .env file is tracked by git

**Solution:**
```bash
# Remove from git tracking (keeps local file)
git rm --cached .env

# Commit the removal
git commit -m "security: Remove .env from version control"

# Verify .env is in .gitignore
grep "^\.env$" .gitignore
```

## Support

For security issues or questions:
- **Security Issues:** Report to [SECURITY.md](SECURITY.md)
- **General Questions:** See [README.md](README.md) or open an issue

## References

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)

---

**Last Updated:** December 9, 2025
**Version:** 1.0.0
