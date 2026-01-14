# HTTPS/SSL Configuration Guide

> Complete guide for configuring SSL/TLS certificates for production deployment

## Overview

DataLogicEngine **requires HTTPS in production** for:
- Secure cookie transmission (`SESSION_COOKIE_SECURE=true`)
- API security and data encryption
- Compliance requirements (SOC2, HIPAA, GDPR)
- SSO/OIDC authentication

---

## 🚨 Production Requirements

### Mandatory

- ✅ Valid SSL/TLS certificate (not self-signed)
- ✅ TLS 1.2 or higher (TLS 1.3 recommended)
- ✅ Strong cipher suites
- ✅ HSTS headers enabled
- ✅ Certificate auto-renewal configured

### Optional (Recommended)

- Certificate pinning for API clients
- OCSP stapling for revocation checking
- CAA DNS records
- Certificate Transparency monitoring

---

## Certificate Options

### Option 1: Let's Encrypt (Recommended for Most)

**Pros:**
- Free certificates
- Automatic renewal
- Widely trusted
- Easy setup with Certbot

**Cons:**
- 90-day validity (requires automation)
- Rate limits (50 certs per domain/week)

### Option 2: Commercial CA (Enterprise)

**Pros:**
- Extended validation (EV) certificates
- 1-2 year validity
- Premium support
- Organization validation

**Cons:**
- Paid ($50-$500+/year)
- Manual renewal process

### Option 3: Cloud Provider Certificates

**Pros:**
- Integrated with cloud services
- Automatic renewal
- Free or low cost

**Cons:**
- Vendor lock-in
- Limited portability

---

## Setup Methods

## Method 1: Let's Encrypt with Certbot

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### Basic Setup

```bash
# Stop your application
sudo systemctl stop ukg-backend

# Obtain certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d api.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# Certificates will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/datalogicengine

server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com api.yourdomain.com;

    # SSL Certificate Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # SSL Session Settings
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy to Flask Backend
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend Static Files (if hosting frontend separately)
    location /static {
        alias /var/www/datalogicengine/frontend/build/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Enable Configuration

```bash
# Test configuration
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/datalogicengine /etc/nginx/sites-enabled/

# Reload Nginx
sudo systemctl reload nginx

# Start application
sudo systemctl start ukg-backend
```

### Automatic Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab
sudo crontab -e

# Add this line (runs twice daily)
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## Method 2: AWS Certificate Manager (ACM)

### Prerequisites

- AWS account
- Domain managed in Route 53 (or manual DNS verification)
- Application Load Balancer or CloudFront distribution

### Setup Steps

1. **Request Certificate**

```bash
aws acm request-certificate \
  --domain-name yourdomain.com \
  --subject-alternative-names api.yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

2. **Verify Domain Ownership**

```bash
# Get validation records
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:... \
  --query 'Certificate.DomainValidationOptions'

# Add CNAME records to Route 53
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch file://validation-records.json
```

3. **Attach to Load Balancer**

```bash
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

**Note:** ACM handles automatic renewal - no action required!

---

## Method 3: Azure App Service Certificates

### Prerequisites

- Azure subscription
- App Service or Application Gateway
- Custom domain configured

### Setup Steps

1. **Create Certificate in Azure Portal**
   - Navigate to App Services → SSL/TLS Settings
   - Click "Create App Service Managed Certificate"
   - Select your custom domain

2. **Or use Azure Key Vault**

```bash
# Import certificate to Key Vault
az keyvault certificate import \
  --vault-name myKeyVault \
  --name myAppCertificate \
  --file certificate.pfx \
  --password $CERT_PASSWORD
```

3. **Bind Certificate to App Service**

```bash
az webapp config ssl bind \
  --resource-group myResourceGroup \
  --name myAppService \
  --certificate-thumbprint $THUMBPRINT \
  --ssl-type SNI
```

**Note:** Azure automatically renews certificates!

---

## Method 4: Self-Signed (Development Only)

⚠️ **WARNING: Never use self-signed certificates in production!**

### Generate Self-Signed Certificate

```bash
# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"

# For development with Flask
python -c "from werkzeug.serving import run_simple; \
  run_simple('0.0.0.0', 5000, app, ssl_context=('cert.pem', 'key.pem'))"
```

---

## Verification

### 1. Test SSL Configuration

```bash
# Check certificate validity
curl -v https://yourdomain.com 2>&1 | grep -A 5 "SSL connection"

# Use SSL Labs (comprehensive test)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

### 2. Verify HSTS

```bash
curl -I https://yourdomain.com | grep -i strict-transport
# Should show: Strict-Transport-Security: max-age=63072000
```

### 3. Check Certificate Expiration

```bash
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# Expected output:
# notBefore=...
# notAfter=...
```

### 4. Verify Cipher Strength

```bash
nmap --script ssl-enum-ciphers -p 443 yourdomain.com
```

---

## Application Configuration

### Update .env for HTTPS

```bash
# .env.production
FLASK_ENV=production

# Enable secure cookies
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict

# Update URLs to HTTPS
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
REACT_APP_API_URL=https://api.yourdomain.com
```

### Update Flask App

```python
# app.py
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Trust proxy headers for HTTPS detection
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enforce HTTPS in production
if not app.debug:
    @app.before_request
    def enforce_https():
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
```

---

## Monitoring & Maintenance

### Certificate Expiration Monitoring

```bash
# Add to monitoring script
check_cert_expiration() {
    DOMAIN=$1
    EXPIRY=$(echo | openssl s_client -connect $DOMAIN:443 2>/dev/null | \
             openssl x509 -noout -enddate | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
    NOW=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW) / 86400 ))

    if [ $DAYS_LEFT -lt 30 ]; then
        echo "WARNING: Certificate expires in $DAYS_LEFT days!"
        # Send alert
    fi
}
```

### Renewal Testing

```bash
# Test Let's Encrypt renewal monthly
sudo certbot renew --dry-run

# Check renewal logs
sudo cat /var/log/letsencrypt/letsencrypt.log
```

---

## Troubleshooting

### Common Issues

#### 1. Certificate Not Trusted

**Symptom:** Browser shows "Not Secure" or SSL error

**Solutions:**
```bash
# Verify certificate chain
openssl s_client -connect yourdomain.com:443 -showcerts

# Ensure fullchain.pem is used (not just cert.pem)
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
```

#### 2. Mixed Content Warnings

**Symptom:** Console errors about insecure resources

**Solution:**
- Update all URLs to HTTPS
- Use relative URLs where possible
- Add CSP header to upgrade insecure requests

```nginx
add_header Content-Security-Policy "upgrade-insecure-requests" always;
```

#### 3. Redirect Loop

**Symptom:** Infinite redirects between HTTP and HTTPS

**Solution:**
```nginx
# Trust X-Forwarded-Proto header
proxy_set_header X-Forwarded-Proto $scheme;
```

#### 4. Certificate Renewal Fails

**Symptom:** Certbot renewal error

**Solutions:**
```bash
# Check port 80 is accessible
sudo netstat -tulpn | grep :80

# Ensure .well-known directory is accessible
# Add to nginx config:
location /.well-known/acme-challenge/ {
    root /var/www/html;
}

# Manually renew with verbose output
sudo certbot renew --verbose
```

---

## Security Best Practices

1. **Use Strong Ciphers Only**
   - Disable SSLv3, TLS 1.0, TLS 1.1
   - Use modern cipher suites
   - Enable PFS (Perfect Forward Secrecy)

2. **Enable HSTS**
   - Start with short max-age (e.g., 300 seconds)
   - Gradually increase to 2 years
   - Add to HSTS preload list

3. **Monitor Certificate Expiration**
   - Set up alerts 30 days before expiry
   - Test renewal process regularly
   - Have backup certificates ready

4. **Regular Security Audits**
   - Run SSL Labs tests quarterly
   - Review cipher suites annually
   - Update certificates promptly

5. **Secure Private Keys**
   - Restrict file permissions: `chmod 600`
   - Never commit to version control
   - Use hardware security modules (HSM) for enterprise

---

## References

- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

**Last Updated:** 2026-01-14
**Maintainer:** Security Team
