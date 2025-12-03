# Secrets Management Guide

> **CRITICAL SECURITY DOCUMENT**
> This guide explains how to securely manage secrets and credentials for the DataLogicEngine (Universal Knowledge Graph) system.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Generating Secure Secrets](#generating-secure-secrets)
- [Environment Configuration](#environment-configuration)
- [Production Deployment](#production-deployment)
- [Secret Rotation](#secret-rotation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

### What Are Secrets?

Secrets are sensitive configuration values that should NEVER be committed to version control:

- **SECRET_KEY**: Flask session encryption key
- **JWT_SECRET_KEY**: JWT token signing key
- **SESSION_SECRET**: Additional session security key
- **Database passwords**: PostgreSQL, Redis credentials
- **API keys**: Azure OpenAI, Azure AD, third-party services
- **Admin credentials**: Initial admin username and password

### Why Secrets Management Matters

❌ **NEVER DO THIS:**
- Commit secrets to Git repositories
- Use default/weak passwords like "admin123"
- Share secrets via email, Slack, or other insecure channels
- Hardcode secrets in application code
- Use the same secrets across environments (dev/staging/prod)

✅ **ALWAYS DO THIS:**
- Generate cryptographically secure random secrets
- Store secrets in secure secret managers (AWS Secrets Manager, Azure Key Vault)
- Use different secrets for each environment
- Rotate secrets regularly
- Limit access to secrets to only those who need them

## Quick Start

### 1. Generate Production Secrets

Run this command to generate secure secrets for production:

```bash
python3 << 'EOF'
import secrets
import string

print("=" * 80)
print("PRODUCTION SECRETS - DataLogicEngine")
print("=" * 80)
print("\nIMPORTANT: Store these in your secrets manager (AWS Secrets Manager, Azure Key Vault)")
print("DO NOT commit these to version control!")
print("\n# Flask & Session Security\n")
print(f"SECRET_KEY={secrets.token_hex(32)}")
print(f"JWT_SECRET_KEY={secrets.token_hex(32)}")
print(f"SESSION_SECRET={secrets.token_hex(32)}")
print("\n# Admin Credentials\n")
username = f"admin_{secrets.token_hex(6)}"
alphabet = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(alphabet) for _ in range(32))
print(f"ADMIN_USERNAME={username}")
print(f"ADMIN_PASSWORD={password}")
print("\n# Database (Generate a secure password)\n")
db_password = ''.join(secrets.choice(alphabet) for _ in range(32))
print(f"PGPASSWORD={db_password}")
print("\n" + "=" * 80)
print("SAVE THESE IMMEDIATELY - They will not be shown again!")
print("=" * 80)
EOF
```

### 2. Set Up Environment Variables

**Development (Local):**

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and fill in the secrets you generated:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. Ensure `.env` is in `.gitignore` (already done if using this repo)

**Production:**

Use a secrets manager instead of `.env` files:

- **AWS**: AWS Secrets Manager or AWS Systems Manager Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Google Cloud Secret Manager
- **Self-hosted**: HashiCorp Vault

## Generating Secure Secrets

### Flask SECRET_KEY (64 characters)

```python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Output example: `e59b3c37eaf5d0e1860f946c2a14e9af7ec05710f2521d72fe41f30b5ca3a28e`

### JWT Secret Key (64 characters)

```python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Secure Admin Password (32+ characters)

```python
python3 -c "import secrets, string; alphabet = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(alphabet) for _ in range(32)))"
```

Output example: `{P=9~2g1%/SMY1vqPxIzKj?W^dLt\COT`

### Unique Admin Username

```python
python3 -c "import secrets; print(f'admin_{secrets.token_hex(6)}')"
```

Output example: `admin_705abd5e922e`

## Environment Configuration

### Required Secrets

The following secrets MUST be set for production:

```bash
# Application Security
SECRET_KEY=<64-char-hex-string>
JWT_SECRET_KEY=<64-char-hex-string>
SESSION_SECRET=<64-char-hex-string>

# Database
DATABASE_URL=postgresql://user:password@host:5432/database
PGPASSWORD=<secure-database-password>

# Admin User
ADMIN_USERNAME=<unique-admin-username>
ADMIN_PASSWORD=<strong-password-32+-chars>
ADMIN_EMAIL=<admin-email-address>
```

### Optional Secrets (if using Azure)

```bash
# Azure AD / Entra ID
AZURE_AD_TENANT_ID=<your-tenant-id>
AZURE_AD_CLIENT_ID=<your-client-id>
AZURE_AD_CLIENT_SECRET=<your-client-secret>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=<your-connection-string>
```

## Production Deployment

### AWS Deployment

**Using AWS Secrets Manager:**

1. Create secrets in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
     --name datalogicengine/production/secret-key \
     --secret-string "e59b3c37eaf5d0e1860f946c2a14e9af7ec05710f2521d72fe41f30b5ca3a28e"
   ```

2. Grant IAM permissions to your EC2/ECS/Lambda:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "secretsmanager:GetSecretValue"
         ],
         "Resource": "arn:aws:secretsmanager:region:account-id:secret:datalogicengine/*"
       }
     ]
   }
   ```

3. Fetch secrets in your application startup script:
   ```bash
   export SECRET_KEY=$(aws secretsmanager get-secret-value \
     --secret-id datalogicengine/production/secret-key \
     --query SecretString --output text)
   ```

### Azure Deployment

**Using Azure Key Vault:**

1. Create secrets in Azure Key Vault:
   ```bash
   az keyvault secret set \
     --vault-name datalogicengine-vault \
     --name SECRET-KEY \
     --value "e59b3c37eaf5d0e1860f946c2a14e9af7ec05710f2521d72fe41f30b5ca3a28e"
   ```

2. Grant access to your App Service/AKS:
   ```bash
   az keyvault set-policy \
     --name datalogicengine-vault \
     --object-id <your-app-identity-object-id> \
     --secret-permissions get list
   ```

3. Use managed identity or reference secrets in App Settings

### Docker Deployment

**Using Docker Secrets:**

```bash
# Create secret files
echo "e59b3c37eaf5d0e1860f946c2a14e9af..." > secret_key.txt

# Pass secrets to container
docker run -d \
  --secret secret_key \
  -e SECRET_KEY_FILE=/run/secrets/secret_key \
  datalogicengine:latest
```

**Using Environment Variables (Less Secure):**

```bash
docker run -d \
  -e SECRET_KEY="e59b3c37eaf5d0e1860f946c2a14e9af..." \
  -e JWT_SECRET_KEY="f0a00ba66d2f331c1672..." \
  datalogicengine:latest
```

## Secret Rotation

### Why Rotate Secrets?

- **Security best practice**: Limit exposure window if a secret is compromised
- **Compliance requirements**: Many frameworks (SOC 2, PCI-DSS) require regular rotation
- **Employee turnover**: Rotate when team members leave

### Rotation Schedule

| Secret Type | Recommended Frequency |
|-------------|----------------------|
| SECRET_KEY, JWT_SECRET_KEY | Every 90 days |
| Admin passwords | Every 60 days or when staff changes |
| Database passwords | Every 90 days |
| API keys (Azure, etc.) | Every 180 days |

### Rotation Procedure

**Phase 1: Generate New Secrets**

```bash
# Generate new secrets
NEW_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
NEW_JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo "New secrets generated. Store securely!"
echo "SECRET_KEY=$NEW_SECRET_KEY"
echo "JWT_SECRET_KEY=$NEW_JWT_SECRET_KEY"
```

**Phase 2: Update Secrets Manager**

```bash
# AWS
aws secretsmanager update-secret \
  --secret-id datalogicengine/production/secret-key \
  --secret-string "$NEW_SECRET_KEY"

# Azure
az keyvault secret set \
  --vault-name datalogicengine-vault \
  --name SECRET-KEY \
  --value "$NEW_SECRET_KEY"
```

**Phase 3: Rolling Deployment**

1. Deploy new application version with updated secrets
2. Monitor for errors
3. Roll back if issues occur
4. Once stable, old secrets can be decommissioned

**Phase 4: Verify and Document**

```bash
# Test authentication still works
curl -X POST https://your-app.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Document rotation in your security log
echo "$(date): Rotated SECRET_KEY and JWT_SECRET_KEY" >> security_rotation.log
```

## Best Practices

### ✅ DO

1. **Use strong, unique secrets**
   - Minimum 64 characters for encryption keys
   - Use cryptographically secure random generation
   - Never reuse secrets across environments

2. **Store secrets securely**
   - Production: Use secrets managers (AWS SM, Azure KV, Vault)
   - Development: Use `.env` files (never commit to Git!)
   - CI/CD: Use platform secret storage (GitHub Secrets, GitLab CI/CD Variables)

3. **Limit access**
   - Only DevOps and senior engineers should access production secrets
   - Use role-based access control (RBAC)
   - Audit secret access regularly

4. **Rotate regularly**
   - Follow the rotation schedule
   - Automate rotation where possible
   - Test rotation procedure before doing it in production

5. **Monitor and audit**
   - Log all secret access (who, when, which secret)
   - Alert on unusual access patterns
   - Regular security audits

### ❌ DON'T

1. **Never commit secrets to version control**
   ```bash
   # Check for accidentally committed secrets
   git log --all --full-history --source -- .env
   ```

2. **Never use default/weak passwords**
   - ❌ `admin` / `admin123`
   - ❌ `password`
   - ❌ `ukg-dev-key`

3. **Never share secrets insecurely**
   - ❌ Email
   - ❌ Slack/Teams messages
   - ❌ Sticky notes
   - ✅ Use 1Password, LastPass, or secrets manager sharing features

4. **Never log secrets**
   ```python
   # BAD
   logger.info(f"Using API key: {api_key}")

   # GOOD
   logger.info("Using API key: [REDACTED]")
   ```

5. **Never hardcode secrets**
   ```python
   # BAD
   SECRET_KEY = "hardcoded-secret-key"

   # GOOD
   SECRET_KEY = os.environ.get("SECRET_KEY")
   ```

## Troubleshooting

### Application won't start: "SECRET_KEY environment variable must be set"

**Cause**: SECRET_KEY not set in production environment

**Solution**:
```bash
# Check if SECRET_KEY is set
echo $SECRET_KEY

# If empty, set it
export SECRET_KEY="your-generated-secret-key"

# For permanent fix, add to secrets manager or environment config
```

### Sessions not persisting / Users logged out frequently

**Cause**: SECRET_KEY is changing between application restarts

**Solution**:
- Ensure SECRET_KEY is consistent across all app instances
- Store in secrets manager, not generated at runtime
- Verify environment variable is set correctly

### "Invalid JWT token" errors after deployment

**Cause**: JWT_SECRET_KEY changed without invalidating old tokens

**Solution**:
```python
# Option 1: Invalidate all existing tokens (forces re-login)
# Clear your token blacklist/cache

# Option 2: Support both old and new keys during transition
# (Implement dual-key validation temporarily)
```

### Forgot admin password

**Cause**: Admin password not documented or lost

**Solution**:
```bash
# Reset admin password via CLI
python3 << EOF
from app import app, db
from models import User

with app.app_context():
    admin = User.query.filter_by(username='your-admin-username').first()
    if admin:
        admin.set_password('new-secure-password-here')
        db.session.commit()
        print("Admin password reset successfully")
    else:
        print("Admin user not found")
EOF
```

### Secrets exposed in logs or error messages

**Cause**: Insufficient secret redaction in logging

**Solution**:
```python
# Implement secret redaction
import re

def redact_secrets(message):
    # Redact anything that looks like a secret key
    message = re.sub(r'[a-f0-9]{64}', '[REDACTED-KEY]', message)
    # Redact passwords
    message = re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'password=[REDACTED]', message, flags=re.IGNORECASE)
    return message

logger.info(redact_secrets(message))
```

## Emergency Procedures

### Suspected Secret Compromise

1. **Immediately rotate all affected secrets**
2. **Revoke access for compromised credentials**
3. **Review access logs for unauthorized activity**
4. **Notify security team and relevant stakeholders**
5. **Document incident for post-mortem**

### Recovery from Secret Leak

If secrets were accidentally committed to Git:

```bash
# 1. Rotate ALL secrets immediately
# 2. Remove secrets from Git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Force push (coordinate with team!)
git push origin --force --all

# 4. Notify team to re-clone repository
# 5. File incident report
```

## Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetsecurity.owasp.org/cheatsheets/Secrets_Management_CheatSheet.html)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [NIST Special Publication 800-57: Cryptographic Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)

## Support

For security concerns or questions about secrets management:

- **Security Team**: security@yourdomain.com
- **DevOps Team**: devops@yourdomain.com
- **Emergency**: Use your organization's security incident response process

---

**Document Version**: 1.0.0
**Last Updated**: December 3, 2025
**Owner**: Security & DevOps Teams
**Classification**: Internal - Sensitive
