# DataLogicEngine Disaster Recovery Runbook

## Overview

This document outlines procedures for recovering from system failures.

---

## 1. Database Recovery

### Complete Database Restore

```bash
# 1. Stop application
sudo systemctl stop datalogicengine

# 2. List available backups
ls -la /var/backups/datalogicengine/

# 3. Verify backup integrity
sha256sum -c /var/backups/datalogicengine/<backup>.sha256

# 4. Restore database
gunzip -c /var/backups/datalogicengine/<backup>.sql.gz | \
  psql -h <host> -U <user> -d ukg_database

# 5. Restart application
sudo systemctl start datalogicengine

# 6. Verify
curl https://your-domain.com/health
```

### Point-in-Time Recovery (if using WAL archiving)

```bash
# Configure recovery.conf
restore_command = 'cp /var/lib/postgresql/wal/%f %p'
recovery_target_time = '2026-01-06 19:00:00'
```

---

## 2. Application Recovery

### Rollback to Previous Version

```bash
# 1. Stop application
sudo systemctl stop datalogicengine

# 2. Identify previous working commit
git log --oneline -10

# 3. Checkout previous version
git checkout <commit-hash>

# 4. Reinstall dependencies
pip install -r requirements.txt

# 5. Restart
sudo systemctl start datalogicengine
```

### Full Redeploy

```bash
# 1. Clone fresh copy
git clone https://github.com/kherrera6219/DataLogicEngine.git /tmp/fresh

# 2. Copy configuration
cp /var/www/datalogicengine/.env /tmp/fresh/

# 3. Swap directories
mv /var/www/datalogicengine /var/www/datalogicengine.old
mv /tmp/fresh /var/www/datalogicengine

# 4. Install dependencies
cd /var/www/datalogicengine
pip install -r requirements.txt

# 5. Restart
sudo systemctl restart datalogicengine
```

---

## 3. SSL Certificate Issues

### Certificate Expired

```bash
# Force renewal
sudo certbot renew --force-renewal

# Reload nginx
sudo systemctl reload nginx
```

### Certificate Not Found

```bash
# Re-issue certificate
sudo ./deploy/setup_ssl.sh your-domain.com admin@your-domain.com
```

---

## 4. Redis Recovery

### Redis Not Responding

```bash
# Check status
sudo systemctl status redis

# Restart
sudo systemctl restart redis

# Verify
redis-cli ping
```

### Clear Redis Cache (if corrupted)

```bash
redis-cli FLUSHALL
```

---

## 5. Nginx Issues

### Configuration Error

```bash
# Test configuration
sudo nginx -t

# View error
sudo tail -50 /var/log/nginx/error.log

# Restore default config
sudo cp /etc/nginx/sites-available/datalogicengine.backup \
        /etc/nginx/sites-available/datalogicengine
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Emergency Contacts

| Issue       | Contact         | Escalation (15 min) |
| ----------- | --------------- | ------------------- |
| Application | [On-call Dev]   | [Dev Lead]          |
| Database    | [DBA]           | [Infra Lead]        |
| Security    | [Security Team] | [CISO]              |

---

## 7. Post-Incident

After recovery:

1. Document incident timeline
2. Identify root cause
3. Update runbook if needed
4. Schedule post-mortem meeting
5. Create preventive measures

---

_Last Updated: 2026-01-06_
