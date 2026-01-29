# Cloud Deployment Guide (Coming Soon)

> **DEPLOYMENT MODE**: This guide is for **Cloud Mode** (SaaS) deployment.  
> For Windows desktop installation, see [`DEPLOYMENT_DESKTOP.md`](DEPLOYMENT_DESKTOP.md).  
> These are **mutually exclusive modes** - do not attempt to run both simultaneously.

---

## Overview

DataLogicEngine Cloud Mode is designed for traditional SaaS deployments with multi-tenant support, OAuth/SSO authentication, and horizontal scaling capabilities.

### Key Features
- OAuth 2.0 / SSO authentication
- Multi-tenant data isolation
- Cloud-hosted PostgreSQL
- Horizontal auto-scaling
- API-first architecture
- WebSocket real-time updates

---

## Prerequisites

### Infrastructure Requirements
- Cloud provider account (AWS, GCP, Azure, Heroku, DigitalOcean)
- PostgreSQL 15+ (managed service recommended)
- Redis 5+ (managed service recommended)
- Domain with SSL certificate
- CDN (optional, for static assets)

### Development Tools
- Docker Desktop
- kubectl (for Kubernetes deployments)
- Node.js 18+
- Python 3.13+

---

## Quick Start (Docker)

```bash
# Clone repository
git clone https://github.com/your-org/DataLogicEngine.git
cd DataLogicEngine

# Set deployment mode
export DEPLOYMENT_MODE=cloud

# Configure environment
cp .env.example .env
# Edit .env with cloud-specific values

# Build and run
docker-compose -f docker-compose.cloud.yml up -d
```

---

## Environment Variables

### Required
```env
DEPLOYMENT_MODE=cloud
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379
SECRET_KEY=<64-char-random-string>
ALLOWED_HOSTS=yourdomain.com,*.yourdomain.com
```

### Authentication (OAuth)
```env
OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-secret>
MICROSOFT_CLIENT_ID=<your-client-id>
MICROSOFT_CLIENT_SECRET=<your-secret>
```

### Cloud Services
```env
# AWS (if using)
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_S3_BUCKET=<bucket-name>

# Storage
CLOUD_STORAGE_BACKEND=s3  # or gcs, azure-blob
```

---

## Deployment Targets

### Heroku
```bash
# Install Heroku CLI
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL and Redis
heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0

# Configure environment
heroku config:set DEPLOYMENT_MODE=cloud
heroku config:set SECRET_KEY=$(openssl rand -hex 32)

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py db upgrade
```

### AWS ECS (Fargate)
See `docs/deployment/aws-ecs.md` (coming soon)

### Google Cloud Run
See `docs/deployment/gcp-cloud-run.md` (coming soon)

### Kubernetes
See `docs/deployment/kubernetes.md` (coming soon)

---

## Authentication Setup

### OAuth 2.0 Configuration

1. **Google OAuth**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create OAuth 2.0 credentials
   - Add authorized redirect: `https://yourdomain.com/auth/google/callback`

2. **Microsoft OAuth**:
   - Register app in [Azure Portal](https://portal.azure.com)
   - Add redirect URI: `https://yourdomain.com/auth/microsoft/callback`

3. **Configure in .env**:
   ```env
   OAUTH_ENABLED=true
   GOOGLE_CLIENT_ID=xxx
   GOOGLE_CLIENT_SECRET=xxx
   MICROSOFT_CLIENT_ID=xxx
   MICROSOFT_CLIENT_SECRET=xxx
   ```

---

## Database Migration

```bash
# Run migrations (production)
python manage.py db upgrade

# Create admin user
python scripts/create_admin_user.py \
  --email admin@yourdomain.com \
  --username admin \
  --role owner
```

---

## Scaling

### Horizontal Scaling

**Web Workers** (Gunicorn):
```bash
# Scale web dynos (Heroku)
heroku ps:scale web=4

# Or in docker-compose
docker-compose up --scale web=4
```

**Background Workers** (Celery):
```bash
# Scale worker dynos
heroku ps:scale worker=2 
```

### Auto-Scaling (Kubernetes)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ukg-web
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ukg-web
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring

### Health Checks
- **Endpoint**: `GET /api/v1/health`
- **Expected**: `{"status": "healthy", "database": "ok", "redis": "ok"}`

### Logging
Cloud mode uses structured JSON logging:
```json
{
  "timestamp": "2026-01-16T12:00:00Z",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "req_abc123",
  "user_id": 123,
  "duration_ms": 45
}
```

### APM Integration
Configure DataDog/New Relic/Sentry:
```env
DD_API_KEY=<your-key>
DD_SERVICE=datalogic-engine
DD_ENV=production
```

---

## Security

### SSL/TLS
- Always use HTTPS in production
- Redirect HTTP → HTTPS
- Use HSTS headers

### CORS Configuration
```env
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
``

`

### Rate Limiting
Cloud mode includes Redis-backed rate limiting:
- 100 requests/minute per IP (unauthenticated)
- 1000 requests/minute (authenticated)

---

## Multi-Tenancy

### Tenant Isolation
Each organization gets:
- Separate database schema (or database)
- Isolated API keys
- Separate user namespace

### Creating Tenants
```python
from models import Tenant

tenant = Tenant(
    name="Acme Corp",
    subdomain="acme",
    plan="enterprise"
)
db.session.add(tenant)
db.session.commit()
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Test connection
psql $DATABASE_URL

# Check pool status
heroku pg:info
```

### Redis Connection Issues
```bash
# Test connection
redis-cli -u $REDIS_URL ping
```

---

## Backup & Recovery

### Automated Backups
Most cloud providers offer automated backups:
- **Heroku**: Automatic daily backups with PGBackups
- **AWS RDS**: Automated snapshots
- **GCP SQL**: Automated backups with point-in-time recovery

### Manual Backup
```bash
# Heroku
heroku pg:backups:capture
heroku pg:backups:download

# Docker/Self-hosted
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

---

## Cost Optimization

### Development/Staging
- Use smaller database instances
- Reduce worker count
- Disable auto-scaling

### Production
- Enable connection pooling
- Use read replicas for analytics
- Implement caching aggressively
- CDN for static assets

---

## Migration from Desktop to Cloud

> **Note**: Desktop and Cloud modes are architecturally different. Migration requires data export/import.

**Steps**:
1. Export data from Desktop Mode (`/api/v1/user/data/export`)
2. Set up Cloud instance
3. Import user data via API
4. Migrate LLM API keys manually (DPAPI → Cloud KMS)

---

## Support

For cloud deployment support:
- Documentation: `docs/deployment/`
- Issues: GitHub Issues
- Enterprise: enterprise@example.com

---

## Coming Soon

- [ ] AWS ECS deployment guide
- [ ] GCP Cloud Run deployment guide
- [ ] Kubernetes Helm charts
- [ ] Terraform modules
- [ ] CloudFormation templates
- [ ] Multi-region deployment
- [ ] Disaster recovery procedures
