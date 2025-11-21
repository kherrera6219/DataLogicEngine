# Deployment Guide

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployment Methods](#deployment-methods)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
  - [Replit Deployment](#replit-deployment)
  - [Cloud Deployment](#cloud-deployment)
- [Database Setup](#database-setup)
- [Security Configuration](#security-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Overview

DataLogicEngine supports multiple deployment methods to accommodate different use cases, from local development to enterprise cloud deployments.

### Deployment Environments

- **Development**: Local machine with hot reload
- **Staging**: Pre-production testing environment
- **Production**: Live production environment

## Prerequisites

### Required Software

- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher
- **PostgreSQL**: 16 (14+ compatible)
- **Git**: 2.x
- **npm**: 10.x or higher (comes with Node.js)

### Optional Software

- **Docker**: 24.x+ and Docker Compose 2.x+
- **Redis**: 7.x (for caching)
- **Nginx**: 1.x (reverse proxy)

### System Requirements

#### Minimum Requirements (Development)
- CPU: 2 cores
- RAM: 4 GB
- Storage: 10 GB
- Network: Broadband internet

#### Recommended Requirements (Production)
- CPU: 4+ cores
- RAM: 16+ GB
- Storage: 100+ GB SSD
- Network: High-speed internet with low latency

## Environment Configuration

### Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
cp .env.template .env
```

#### Essential Variables

```bash
# Application Mode
FLASK_ENV=production  # development, testing, or production
NODE_ENV=production   # development or production

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/datalogic
POSTGRES_USER=datalogic_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=datalogic
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
SESSION_SECRET=your-session-secret

# API Keys
OPENAI_API_KEY=sk-your-openai-key
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Azure AD (Optional)
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_TENANT_ID=your-tenant-id

# Service Ports
API_GATEWAY_PORT=5000
WEBHOOK_SERVER_PORT=5001
MODEL_CONTEXT_PORT=5002
UKG_SERVICE_PORT=5003
FRONTEND_PORT=3000

# Feature Flags
ENABLE_SWAGGER=true
ENABLE_CORS=true
ENABLE_RATE_LIMITING=true

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Generating Secret Keys

```bash
# Python method
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL method
openssl rand -hex 32
```

## Deployment Methods

### Local Development

#### 1. Clone Repository

```bash
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine
```

#### 2. Set Up Python Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-enterprise.txt
```

#### 3. Set Up Node.js Environment

```bash
npm install
```

#### 4. Configure Environment

```bash
cp .env.template .env
# Edit .env with your configuration
```

#### 5. Initialize Database

```bash
# Create PostgreSQL database
createdb datalogic

# Run migrations
python init_db.py
```

#### 6. Start Development Servers

**Option 1: Separate Terminals**

```bash
# Terminal 1 - Backend
gunicorn --bind 0.0.0.0:5000 --reload main:app

# Terminal 2 - Frontend
npm run dev
```

**Option 2: Enterprise Mode**

```bash
./start_enterprise.sh
```

#### 7. Access Application

- Frontend: http://localhost:3000
- API: http://localhost:5000
- Swagger Docs: http://localhost:5000/swagger

---

### Docker Deployment

#### 1. Create Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-enterprise.txt .
RUN pip install --no-cache-dir -r requirements-enterprise.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs/security logs/audit logs/compliance

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

Create `frontend.Dockerfile`:

```dockerfile
# Frontend Dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --production

# Copy application code
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "start"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: datalogic_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: datalogic
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U datalogic_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://datalogic_user:secure_password@postgres:5432/datalogic
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs

  frontend:
    build:
      context: .
      dockerfile: frontend.Dockerfile
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://backend:5000
    ports:
      - "3000:3000"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

#### 3. Deploy with Docker Compose

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

#### 4. Initialize Database in Docker

```bash
docker-compose exec backend python init_db.py
```

---

### Replit Deployment

The application is pre-configured for Replit deployment.

#### 1. Fork/Import Repository

1. Go to [Replit](https://replit.com)
2. Click "Create Repl"
3. Import from GitHub: `https://github.com/kherrera6219/DataLogicEngine`

#### 2. Configure Secrets

In Replit Secrets (lock icon in sidebar), add:

```
DATABASE_URL=postgresql://...
SECRET_KEY=...
JWT_SECRET_KEY=...
OPENAI_API_KEY=...
```

#### 3. Database Setup

Replit provides PostgreSQL 16:

```bash
# Database URL is automatically provided
# Initialize database
python init_db.py
```

#### 4. Run Application

The `.replit` file is pre-configured. Just click "Run".

---

### Cloud Deployment

#### AWS Deployment

##### Using Elastic Beanstalk

1. **Install EB CLI**
```bash
pip install awsebcli
```

2. **Initialize EB Application**
```bash
eb init -p python-3.11 datalogicengine
```

3. **Create Environment**
```bash
eb create datalogic-prod
```

4. **Configure Environment Variables**
```bash
eb setenv FLASK_ENV=production SECRET_KEY=xxx DATABASE_URL=xxx
```

5. **Deploy**
```bash
eb deploy
```

##### Using ECS (Fargate)

1. **Build and Push Docker Image**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t datalogicengine .
docker tag datalogicengine:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/datalogicengine:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/datalogicengine:latest
```

2. **Create ECS Task Definition** (use AWS Console or CLI)

3. **Create ECS Service**

#### Azure Deployment

##### Using Azure App Service

1. **Create App Service**
```bash
az webapp create --resource-group DataLogicEngine \
  --plan DataLogicPlan \
  --name datalogicengine \
  --runtime "PYTHON:3.11"
```

2. **Configure Environment Variables**
```bash
az webapp config appsettings set --resource-group DataLogicEngine \
  --name datalogicengine \
  --settings FLASK_ENV=production SECRET_KEY=xxx
```

3. **Deploy Code**
```bash
az webapp up --name datalogicengine --runtime "PYTHON:3.11"
```

##### Using Azure Kubernetes Service (AKS)

1. **Create Kubernetes manifests** (see `k8s/` directory)

2. **Deploy to AKS**
```bash
kubectl apply -f k8s/
```

#### Google Cloud Platform

##### Using Cloud Run

1. **Build Container**
```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/datalogicengine
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy datalogicengine \
  --image gcr.io/PROJECT-ID/datalogicengine \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Database Setup

### PostgreSQL Configuration

#### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-16 postgresql-contrib
```

**macOS:**
```bash
brew install postgresql@16
brew services start postgresql@16
```

#### 2. Create Database and User

```bash
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE USER datalogic_user WITH PASSWORD 'secure_password';
CREATE DATABASE datalogic OWNER datalogic_user;
GRANT ALL PRIVILEGES ON DATABASE datalogic TO datalogic_user;
\q
```

#### 3. Configure PostgreSQL for Remote Access (Production)

Edit `/etc/postgresql/16/main/postgresql.conf`:
```
listen_addresses = '*'
```

Edit `/etc/postgresql/16/main/pg_hba.conf`:
```
host    datalogic    datalogic_user    0.0.0.0/0    scram-sha-256
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

#### 4. Run Migrations

```bash
python init_db.py
```

### Database Backup

```bash
# Backup
pg_dump -U datalogic_user -h localhost datalogic > backup.sql

# Restore
psql -U datalogic_user -h localhost datalogic < backup.sql
```

---

## Security Configuration

### SSL/TLS Configuration

#### Using Let's Encrypt with Nginx

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d datalogicengine.com -d www.datalogicengine.com

# Auto-renewal is configured by default
```

#### Nginx Configuration

Create `/etc/nginx/sites-available/datalogicengine`:

```nginx
server {
    listen 80;
    server_name datalogicengine.com www.datalogicengine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name datalogicengine.com www.datalogicengine.com;

    ssl_certificate /etc/letsencrypt/live/datalogicengine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/datalogicengine.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/datalogicengine /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## Monitoring and Logging

### Application Logging

Logs are stored in:
- `logs/security/` - Security events
- `logs/audit/` - Audit trail
- `logs/compliance/` - Compliance events
- `logs/app.log` - General application logs

### Log Rotation

Create `/etc/logrotate.d/datalogicengine`:

```
/path/to/DataLogicEngine/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload datalogicengine
    endscript
}
```

### Monitoring Tools

#### Prometheus + Grafana

```bash
# Install Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Install Grafana
docker run -d -p 3001:3000 grafana/grafana
```

#### Application Performance Monitoring

Consider integrating:
- **New Relic**
- **Datadog**
- **Sentry** (for error tracking)

---

## Backup and Recovery

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/datalogic"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U datalogic_user datalogic | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# File backup
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" /path/to/DataLogicEngine/data

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Cron Job

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

#### Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U datalogic_user -h localhost -d datalogic
```

#### Permission Denied Errors

```bash
# Fix file permissions
chmod +x start_enterprise.sh
chmod +x start_ukg.sh

# Fix log directory permissions
chmod -R 755 logs/
```

#### Module Not Found

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements-enterprise.txt
npm install
```

### Health Checks

```bash
# Check backend health
curl http://localhost:5000/health

# Check database connectivity
python check_enterprise_health.py
```

### Performance Issues

1. **Enable PostgreSQL query logging**
2. **Monitor slow queries**
3. **Add database indexes**
4. **Enable caching (Redis)**
5. **Scale horizontally**

---

## Production Checklist

- [ ] Environment variables configured
- [ ] Secret keys generated and secure
- [ ] Database backups automated
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured
- [ ] Monitoring set up
- [ ] Log rotation configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers set
- [ ] Database indexes optimized
- [ ] Error tracking enabled
- [ ] Health checks implemented
- [ ] Documentation updated
- [ ] Disaster recovery plan in place

---

For more information, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Security Policy](../SECURITY.md)
