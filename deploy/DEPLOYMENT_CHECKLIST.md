# DataLogicEngine Production Deployment Checklist

## Pre-Deployment

### Environment Setup

- [ ] Production server provisioned (Linux recommended)
- [ ] PostgreSQL database created
- [ ] Redis server running (optional but recommended)
- [ ] Domain name configured with DNS pointing to server

### Configuration

- [ ] Copy `.env.template` to `.env`
- [ ] Generate secure SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Generate secure JWT_SECRET_KEY
- [ ] Generate secure SESSION_SECRET
- [ ] Set `FLASK_ENV=production`
- [ ] Configure `DATABASE_URL` with production credentials
- [ ] Configure `REDIS_URL` if using Redis
- [ ] Set admin credentials (NOT default values!)

### Security Verification

```bash
# Run security scan
bandit -r . -ll --exclude .venv,tests

# Check dependencies
pip-audit
safety check
```

- [ ] No critical vulnerabilities
- [ ] No default credentials

---

## Deployment Steps

### 1. SSL/HTTPS Setup

```bash
# On production server
sudo ./deploy/setup_ssl.sh your-domain.com admin@your-domain.com
```

- [ ] SSL certificate obtained
- [ ] Auto-renewal configured

### 2. Nginx Configuration

```bash
# Copy and configure nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/datalogicengine
sudo nano /etc/nginx/sites-available/datalogicengine  # Update domain name
sudo ln -s /etc/nginx/sites-available/datalogicengine /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

- [ ] Nginx configured
- [ ] HTTPS working

### 3. Database Setup

```bash
# Initialize database
flask db upgrade
python backend/seed_data.py  # Optional: seed initial data
```

- [ ] Database migrated
- [ ] Admin user created

### 4. Application Deployment

```bash
# Using gunicorn with supervisord or systemd
gunicorn --bind 127.0.0.1:5000 --workers 4 --threads 2 wsgi:app
```

- [ ] Application running
- [ ] Health check passing: `curl https://your-domain.com/health`

### 5. Backup Configuration

```bash
# Set up daily backups via cron
sudo cp deploy/backup_database.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/backup_database.sh
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup_database.sh
```

- [ ] Backup script installed
- [ ] Cron job configured
- [ ] Test backup successful

---

## Post-Deployment Verification

### Functionality

- [ ] Homepage loads
- [ ] Login works
- [ ] Dashboard accessible
- [ ] API health check: `GET /api/health` returns 200
- [ ] Database queries working

### Security Headers

```bash
# Check security headers
curl -I https://your-domain.com
```

- [ ] `Strict-Transport-Security` present
- [ ] `X-Frame-Options` present
- [ ] `X-Content-Type-Options` present
- [ ] `Content-Security-Policy` present

### SSL Verification

```bash
# Test SSL grade
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

- [ ] SSL grade A or A+

### Performance

- [ ] Response time < 500ms
- [ ] No console errors
- [ ] Compression working (check Content-Encoding header)

---

## Monitoring Setup

### Error Tracking (Sentry)

```python
# In app.py (add after app = Flask(__name__))
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
    environment=os.environ.get("FLASK_ENV", "production")
)
```

- [ ] Sentry DSN configured
- [ ] Test error captured

### Uptime Monitoring

- [ ] Uptime monitoring configured (UptimeRobot, Pingdom, etc.)
- [ ] Alerting configured

---

## Rollback Plan

### Quick Rollback

```bash
# Stop current version
sudo systemctl stop datalogicengine

# Switch to previous version
cd /var/www/datalogicengine
git checkout <previous-commit>
pip install -r requirements.txt

# Start
sudo systemctl start datalogicengine
```

### Database Rollback

```bash
# Restore from backup
gunzip -c /var/backups/datalogicengine/latest.sql.gz | psql -U postgres -d ukg_database
```

---

## Emergency Contacts

| Role             | Contact        |
| ---------------- | -------------- |
| On-call Engineer | [Your contact] |
| DevOps Lead      | [Your contact] |
| Security Team    | [Your contact] |

---

_Last Updated: 2026-01-06_
