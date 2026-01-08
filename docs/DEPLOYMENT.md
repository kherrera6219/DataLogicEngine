# Deployment Guide

## Overview

Deploying the Universal Knowledge Graph (UKG) involves hosting two distinct services:

1.  **Frontend**: Next.js Node.js application.
2.  **Backend**: Flask Python application.

## 1. Backend Deployment

The backend requires a Python 3.11 environment and a PostgreSQL database.

### Docker Method (Recommended)

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Infrastructure Requirements

- **PostgreSQL 15+**: Azure Database for PostgreSQL, RDS, or self-hosted.
- **Redis 6+**: Azure Redis Cache or ElastiCache.
- **Environment Variables**: See `.env.template`.

### Azure App Service (Linux)

1.  Create an App Service Plan (Linux).
2.  Create a Web App targeting **Python 3.11**.
3.  Set Startup Command: `gunicorn -w 4 -b 0.0.0.0:8000 app:app`
4.  Configure App Settings (Environment Variables).

---

## 2. Frontend Deployment

The frontend is a standard Next.js application.

### Vercel (Recommended)

1.  Import repository to Vercel.
2.  Set `Root Directory` to `frontend`.
3.  Configure Environment Variables:
    - `NEXT_PUBLIC_API_URL`: The URL of your deployed Backend (e.g., `https://api.ukg.io`).
    - **Note**: You may need to update `next.config.ts` to use this variable for rewrites, or configure CORS on the backend to allow the Vercel domain and use direct API calls.

### Azure Static Web Apps / Container

1.  **Static Web App**: If using Static Export (`output: 'export'`), deploy to Azure SWA.
2.  **Container**: Dockerize the Next.js app.

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build
CMD ["npm", "start"]
```

---

## 3. Database Migration

Always run migrations against the production database before deployment.

```bash
# From backend directory
export DATABASE_URL="postgresql://user:pass@host/db"
flask db upgrade
python backend/seed_data.py  # Only for initial setup
```
