# DataLogicEngine Developer Guide

**Last Updated:** 2026-01-28  
**Version:** 2.5.0-GRADUATED

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+ (optional for local SQLite fallback)
- Redis 7+ (optional for local development mode)
- Node.js 20+ (for frontend)
- **OpenAI API Key** (Vision support required for VideoService)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd DataLogicEngine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
# Edit .env with your configuration (SESSION_SECRET + provider API keys minimum)

# Initialize database
flask db upgrade

# Run development server
python app.py
```

For Windows 11 local bring-up with API keys only (SQLite/in-memory fallback), see:

- `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
- `scripts/windows/start_local_stack.ps1`

For full local data services (PostgreSQL + Redis + Neo4j + MinIO), run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1 -WithDataServices
```

---

## Project Structure

```
DataLogicEngine/
├── backend/
│   ├── mcp_server/        # MCP Router & Registry
│   ├── services/          # Multimodal (Audio, Video, Doc)
│   ├── security/          # PII & Injection Shiels
│   ├── quad_persona/      # Multi-expert engine
│   ├── simulation/        # 10-layer scenario stack
│   └── truth_engine/      # Compliance & Blockchain
├── frontend/
│   ├── app/               # Next.js Routes
│   ├── components/        # React UI
│   └── electron/          # Desktop process
├── sdk/                   # UKG Python SDK
├── tests/                 # Security & Quality suites
└── docs/                  # Graduation documentation
```

---

## Key Concepts

### 17-Axis Knowledge Framework

The system uses a 17-dimensional coordinate system:
- **Axes 1-7**: Knowledge organization (Pillar, Sector, Honeycomb, Branch, Node, Octopus, Spiderweb)
- **Axes 8-11**: Personas (Knowledge, Sector, Regulatory, Compliance experts)
- **Axes 12-13**: Context (Location, Time)
- **Axes 14-17**: Meta (Risk, Performance, Ethics, Learning)

### Quad Persona Engine

Four AI personas debate each query:
1. **Knowledge Expert** - Domain accuracy
2. **Sector Expert** - Industry applicability
3. **Regulatory Expert** - Compliance requirements
4. **Compliance Expert** - Internal policy alignment

### 10-Layer Simulation Stack

Queries flow through 10 processing layers with recursive refinement until confidence threshold (≥99.5%) is met.

---

## Development Workflow

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/integration/test_api_endpoints.py -v

# Load testing (requires locust)
locust -f tests/performance/locustfile.py
```

### Code Quality

```bash
# Linting
pylint backend/ core/

# Security scan
bandit -r . -ll --exclude .venv,tests

# Type checking (if using mypy)
mypy backend/
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```

---

## API Development

### Adding a New Endpoint

1. Create route in `routes/` or add to existing blueprint
2. Add schema validation in `backend/schemas/`
3. Write integration test in `tests/integration/`
4. Update Postman collection in `docs/api/`

### Authentication

All API endpoints (except `/health`, `/api/v1/auth/*`) require authentication:
- Session-based for web UI
- API key for programmatic access (header: `X-API-Key`)

### Rate Limiting

Default limits configured in `.env`:
- Global: 200 requests/hour
- Auth endpoints: 5 requests/minute

---

## Environment Variables

See `.env.template` for full list. Key variables:

| Variable | Description |
|----------|-------------|
| `SESSION_SECRET` | Session signing key (required for local runtime) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis for caching/rate limiting |
| `OPENAI_API_KEY` | OpenAI provider key |
| `ANTHROPIC_API_KEY` | Anthropic provider key |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Google Gemini provider key |
| `AZURE_OPENAI_*` | LLM provider credentials |

---

## Troubleshooting

### Common Issues

**Database connection failed:**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432
```

**Redis connection failed:**
```bash
# Check Redis is running
redis-cli ping
```

**Import errors:**
```bash
# Ensure virtual environment is activated
which python  # Should show .venv path
```

---

## Resources

- [API Documentation](/api/docs) - Swagger UI
- [Production Readiness](PRODUCTION_READINESS.md)
- [Deployment Checklist](../deploy/DEPLOYMENT_CHECKLIST.md)
- [Architecture Whitepapers](whitepapers/)
